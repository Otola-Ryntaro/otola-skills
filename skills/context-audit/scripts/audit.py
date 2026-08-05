#!/usr/bin/env python3
"""
where: ~/.claude/skills/context-audit/scripts/audit.py
what:  Claude Code が毎セッション固定で注入するコンテキストを計測・ランク付けする。
why:   会話開始前のオーバーヘッドの内訳を可視化し、安全な削減対象を特定するため。
注意:  読み取り専用。ファイル/設定は一切変更しない。トークンは粗い推定（真値は /context）。

計測の考え方:
- CLAUDE.md の import 連鎖 と rules/ は「全文」が注入される -> ファイル全体のバイト数で測る。
- skills / agents は一覧に「name + description」だけが注入される（本文は呼び出し時のみ load）
  -> frontmatter の name+description のバイト数で測る（全文バイトは約10倍の過大評価になるため使わない）。
"""
import json
import re
from pathlib import Path

HOME = Path.home()
CLAUDE = HOME / ".claude"


def est_tokens(nbytes: int) -> int:
    return round(nbytes / 4)  # 日英混在の粗い近似。真値は /context。


def fmt_kb(n: int) -> str:
    return f"{n / 1024:.1f}KB"


def front_desc_bytes(path: Path) -> int:
    """SKILL.md / agent.md の frontmatter から name+description のバイト数を返す（=実際の注入量の近似）。"""
    try:
        txt = path.read_text(errors="replace")
    except Exception:
        return 0
    if not txt.startswith("---"):
        return min(len(txt.encode()), 400)
    end = txt.find("\n---", 3)
    fm = txt[3:end] if end != -1 else txt[3:]
    name, desc = "", []
    lines = fm.splitlines()
    i, n = 0, len(lines)
    while i < n:
        mn = re.match(r"^name:\s*(.*)", lines[i])
        md = re.match(r"^description:\s*(.*)", lines[i])
        if mn:
            name = mn.group(1)
            i += 1
        elif md:
            desc.append(md.group(1))
            i += 1
            while i < n and not re.match(r"^[A-Za-z_][\w-]*:", lines[i]):
                desc.append(lines[i])
                i += 1
        else:
            i += 1
    return len((name + " " + " ".join(desc)).encode())


rows = []   # (category, label, bytes, note)
findings = []


# 1. CLAUDE.md の @import 連鎖（全文注入）と「# @」import トラップ
claude_md = CLAUDE / "CLAUDE.md"
active, trap = [], []
chain_bytes = 0
if claude_md.exists():
    chain_bytes += claude_md.stat().st_size
    for ln, line in enumerate(claude_md.read_text(errors="replace").splitlines(), 1):
        ma = re.match(r"^\s*@(\S+\.md)", line)
        mt = re.match(r"^\s*#\s*@(\S+\.md)", line)
        if ma:
            active.append((ln, ma.group(1)))
        elif mt:
            trap.append((ln, mt.group(1)))
    for _, fn in active + trap:
        p = CLAUDE / fn
        if p.exists():
            chain_bytes += p.stat().st_size
rows.append(("グローバル指示", "CLAUDE.md import連鎖(全文)",
             chain_bytes, f"active={len(active)} / #@トラップ={len(trap)}"))
if trap:
    findings.append(
        "「# @」import トラップ: 次の行は # 付きでも import されています（コメント化されない）。"
        "停止するには行頭の @ を外す:\n"
        + "\n".join(f"    L{ln}: # @{fn}  ->  # {fn}" for ln, fn in trap))


# 2. ~/.claude/rules/ 自動ロード（全文注入）
rules_dir = CLAUDE / "rules"
rules = sorted(rules_dir.glob("*.md")) if rules_dir.exists() else []
rb = sum(p.stat().st_size for p in rules)
rows.append(("グローバル指示", f"rules/ 自動ロード({len(rules)},全文)",
             rb, "CLAUDE.md 不参照でも自動ロード"))


# 3. ~/.claude/agents/（一覧 = name+description のみ注入）
adir = CLAUDE / "agents"
agents = sorted(adir.glob("*.md")) if adir.exists() else []
ab = sum(front_desc_bytes(p) for p in agents)
rows.append(("agents", f"~/.claude/agents/ ({len(agents)})",
             ab, "name+description が agents 一覧に常時注入"))


# 4. ~/.claude/skills/（一覧 = name+description のみ注入）
sdir = CLAUDE / "skills"
skills = [d for d in sdir.iterdir() if d.is_dir() and not d.name.startswith(".")] if sdir.exists() else []
sb = sum(front_desc_bytes(d / "SKILL.md") for d in skills if (d / "SKILL.md").exists())
rows.append(("skills", f"~/.claude/skills/ ({len(skills)})",
             sb, "name+description が skills 一覧に常時注入"))


# 5. 有効プラグイン（一覧 = 各 skill/agent の name+description のみ注入）
enabled = {}
st = CLAUDE / "settings.json"
if st.exists():
    try:
        enabled = json.loads(st.read_text()).get("enabledPlugins", {})
    except Exception:
        pass
paths = {}
inst = CLAUDE / "plugins" / "installed_plugins.json"
if inst.exists():
    try:
        for k, arr in json.loads(inst.read_text()).get("plugins", {}).items():
            if arr:
                paths[k] = arr[0].get("installPath")
    except Exception:
        pass
for k, on in enabled.items():
    if not on:
        continue
    ip = paths.get(k)
    if not ip or not Path(ip).exists():
        rows.append(("plugin", k.split("@")[0], 0, "installPath 不明"))
        continue
    base = Path(ip)
    sk = list(base.rglob("SKILL.md"))
    ag = [p for p in base.rglob("*.md") if "agents" in p.parts]
    ncmd = len([p for p in base.rglob("*.md") if "commands" in p.parts])
    inj = sum(front_desc_bytes(p) for p in sk) + sum(front_desc_bytes(p) for p in ag)
    rows.append(("plugin", k.split("@")[0], inj,
                 f"skills={len(sk)} agents={len(ag)} cmds={ncmd}"))


# 6. claude-mem 等の SessionStart 注入（disk からは正確に測れない -> 警告）
if any(on and "claude-mem" in k for k, on in enabled.items()):
    findings.append(
        "claude-mem 有効: SessionStart で recent context を注入（実測で 1万 tokens 規模になりうる）。"
        "正確な量は /context で確認。減らすには注入観測数を絞るか無効化。")


# ---- レポート ----
rows.sort(key=lambda r: r[2], reverse=True)
total = sum(r[2] for r in rows)
print("=" * 74)
print(" Claude Code コンテキスト棚卸し（読み取り専用 / 一覧は name+description 実測）")
print("=" * 74)
print(f"{'カテゴリ':<10}{'項目':<32}{'注入推定':>9}{'推定tok':>9}  備考")
print("-" * 74)
for cat, label, b, note in rows:
    print(f"{cat:<10}{label[:31]:<32}{fmt_kb(b):>9}{est_tokens(b):>9}  {note}")
print("-" * 74)
print(f"{'合計(計測分)':<42}{fmt_kb(total):>9}{est_tokens(total):>9}")
print("\n[発見・注意]")
for f in findings:
    print("- " + f)
if not findings:
    print("- 特になし")
print("\n[次の一手]")
print("- 真値確認: Claude Code で /context を実行（このスクリプトは disk 推定）。")
print("- 削減は必ずユーザー確認後に。移動/退避はすべて mv で可逆。")
print("- プラグイン: settings.json の enabledPlugins を false（or /plugin）。")
print("- agents/skills: 専用プロジェクトの .claude/ へ移動 か ~/.claude/*_archive/ へ退避。")
print("=" * 74)
