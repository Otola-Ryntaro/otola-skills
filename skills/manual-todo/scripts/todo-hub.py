#!/usr/bin/env python3
# where: ~/.claude/skills/manual-todo/scripts/todo-hub.py（正本。~/dev/todo/bin/todo-hub から exec される）
# what : manual-todo の集約ハブ CLI。ローカル HTTP サーバでチェック状態を JSON 保存し、
#        index.html の静的生成・Chrome アプリモード起動・launchd 常駐化を提供する
# why  : 各プロジェクトに分散していた手作業 TODO を ~/dev/todo に集約し、
#        ブラウザのチェック操作を Claude が読める JSON に書き戻すため
#
# 依存: python3 標準ライブラリのみ（macOS 標準の python3 で動作）
# 使い方:
#   todo-hub serve                     # サーバをフォアグラウンド起動（ポート 7799）
#   todo-hub open [slug]               # サーバ自動起動 + Chrome アプリモードで開く
#   todo-hub register --slug S --project P --project-path DIR --title T [--legacy HTML]
#   todo-hub reindex                   # registry + state から index.html を再生成
#   todo-hub install-launchd           # 常駐化（オプション）

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 7799
HUB = Path.home() / "dev" / "todo"
PAGES = HUB / "pages"
STATE = HUB / "state"
HEROES = HUB / "heroes"
BIN = HUB / "bin"
PROFILE = HUB / "chrome-profile"
REGISTRY = STATE / "registry.json"
REPORTS = STATE / "reports.json"
ASSETS = Path(__file__).resolve().parent.parent / "assets"
JST = timezone(timedelta(hours=9))
# 配信するのはハブの画面だけ。state や chrome-profile など配下の他のファイルは出さない
STATIC_FILES = ("index.html", "reports.html")
STATIC_DIRS = ("pages", "heroes")
# 取り込んだレポートは信用できないので、ハブとは別オリジン扱いにして API を呼ばせない
REPORT_CSP = "sandbox allow-scripts allow-popups"


def ensure_dirs():
    for d in (PAGES, STATE, HEROES, BIN, PROFILE):
        d.mkdir(parents=True, exist_ok=True)
    wrapper = BIN / "todo-hub"
    script = Path(__file__).resolve()
    content = f'#!/bin/sh\nexec python3 "{script}" "$@"\n'
    if not wrapper.exists() or wrapper.read_text() != content:
        wrapper.write_text(content)
        wrapper.chmod(0o755)


def now_iso():
    return datetime.now(JST).isoformat(timespec="seconds")


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_registry():
    return load_json(REGISTRY, {"pages": []})


def safe_slug(slug):
    # パストラバーサル防止: slug はファイル名になるため英数・ハイフン・アンダースコアのみ許可
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+", slug)) and ".." not in slug


def page_summary(entry):
    st = load_json(STATE / f"{entry['slug']}.json", {})
    tasks = st.get("tasks", {})
    done = sum(1 for t in tasks.values() if t.get("done"))
    return {"done": done, "total": len(tasks)}


# ---------------------------------------------------------------- server

def vscode_target(target):
    """登録済みプロジェクト配下のパスだけを通す。(path, project_root, error) を返す"""
    if not target:
        return None, None, (400, "path required")
    tp = Path(target).resolve()
    roots = {str(Path(e["projectPath"]).resolve())
             for e in load_registry()["pages"] if e.get("projectPath")}
    roots.add(str(HUB.resolve()))
    proot = next((r for r in roots
                  if str(tp) == r or str(tp).startswith(r + "/")), None)
    if not proot:
        return None, None, (403, "path not under a registered project")
    if not tp.exists():
        return None, None, (404, "not found")
    return tp, proot, None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 静かに

    def _send(self, code, body, ctype="application/json; charset=utf-8", csp=""):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # CORS: 自分自身（localhost:7799）のみ許可。null origin（file:// フォールバック）は
        # サンドボックス iframe に偽装されうるため 2026-08-11 に閉鎖。
        # file:// で開いた場合のチェック保存は localStorage のみとなる（サーバ経由が正）
        origin = self.headers.get("Origin", "")
        if origin in ("http://localhost:7799", "http://127.0.0.1:7799"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if csp:
            self.send_header("Content-Security-Policy", csp)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, b"")

    def _host_ok(self):
        # DNS rebinding 対策: Host ヘッダが localhost 系でなければ拒否
        return self.headers.get("Host", "") in ("localhost:7799", "127.0.0.1:7799")

    def _origin_ok(self):
        # CSRF 対策: 書き込みは自分自身のページ（localhost:7799）からのみ受け付ける。
        # Origin なし・null・他サイトは拒否。JSON 必須にして他サイトからは CORS プリフライトを強制する
        origin = self.headers.get("Origin", "")
        ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        return origin in ("http://localhost:7799", "http://127.0.0.1:7799") and ctype == "application/json"

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "bad host"})
        path = self.path.split("?")[0]
        if path == "/api/health":
            return self._send(200, {"ok": True, "hub": str(HUB)})
        if path == "/api/summary":
            reg = load_registry()
            pages = []
            for e in reg["pages"]:
                s = page_summary(e)
                pages.append({**e, **s})
            return self._send(200, {"pages": pages})
        m = re.fullmatch(r"/api/state/([^/]+)", path)
        if m:
            slug = m.group(1)
            if not safe_slug(slug):
                return self._send(400, {"error": "bad slug"})
            return self._send(200, load_json(STATE / f"{slug}.json", {}))
        # 登録済みレポート HTML の配信（http ページから file:// へ遷移できない問題の回避。
        # reports.json に登録されたパスのみ許可するホワイトリスト方式）
        if path == "/file":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            target = qs.get("path", [""])[0]
            tp = Path(target).resolve()
            allowed = {str(Path(e["path"]).resolve()) for e in load_reports()["reports"]}
            if str(tp) not in allowed or tp.suffix != ".html":
                return self._send(403, {"error": "not registered"})
            if not tp.is_file():
                return self._send(404, {"error": "not found"})
            return self._send(200, tp.read_bytes(), "text/html; charset=utf-8", csp=REPORT_CSP)
        # VS Code でファイルを開く（manual-todo ページの「VS Code で開く」ボタン用）。
        # 任意コマンド実行を防ぐため、登録済み projectPath 配下＋ハブ配下のみ許可
        if path == "/api/vscode":
            # check=1: 存在確認のみ。VS Code の起動は POST に限る（他サイトから GET で叩かれるため）
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if not qs.get("check", [""])[0]:
                return self._send(405, {"error": "use POST"})
            tp, _proot, err = vscode_target(qs.get("path", [""])[0])
            if err:
                return self._send(err[0], {"error": err[1]})
            return self._send(200, {"ok": True, "path": str(tp)})
        # 静的配信: index / pages / heroes
        return self._serve_static(path)

    def _serve_static(self, path):
        hub = HUB.resolve()
        target = (hub / ("index.html" if path == "/" else path.lstrip("/"))).resolve()
        if not (target in [hub / f for f in STATIC_FILES]
                or any(target.is_relative_to(hub / d) for d in STATIC_DIRS)):
            return self._send(403, {"error": "forbidden"})
        if not target.is_file():
            return self._send(404, {"error": "not found"})
        ctypes = {".html": "text/html; charset=utf-8", ".png": "image/png",
                  ".jpg": "image/jpeg", ".json": "application/json; charset=utf-8",
                  ".svg": "image/svg+xml"}
        self._send(200, target.read_bytes(), ctypes.get(target.suffix, "application/octet-stream"))

    def _open_vscode(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except ValueError:
            return self._send(400, {"error": "bad json"})
        line = str(body.get("line", ""))
        tp, proot, err = vscode_target(body.get("path", ""))
        if err:
            return self._send(err[0], {"error": err[1]})
        code = shutil.which("code") or "/opt/homebrew/bin/code"
        if tp.is_dir():
            subprocess.run([code, str(tp)], check=False)
            return self._send(200, {"ok": True, "opened": str(tp)})
        goto = f"{tp}:{line}" if line.isdigit() else str(tp)
        # プロジェクトフォルダをワークスペースとして開き、該当ファイルへジャンプ
        subprocess.run([code, proot, "--goto", goto], check=False)
        return self._send(200, {"ok": True, "opened": goto, "workspace": proot})

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {"error": "bad host"})
        if not self._origin_ok():
            return self._send(403, {"error": "bad origin"})
        if self.path.split("?")[0] == "/api/vscode":
            return self._open_vscode()
        m = re.fullmatch(r"/api/state/([^/]+)", self.path.split("?")[0])
        if not m:
            return self._send(404, {"error": "not found"})
        slug = m.group(1)
        if not safe_slug(slug):
            return self._send(400, {"error": "bad slug"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, OSError):
            return self._send(400, {"error": "bad json"})
        path = STATE / f"{slug}.json"
        st = load_json(path, {"slug": slug, "tasks": {}})
        # ページ側メタ（title 等）は既存値を優先しつつ未設定なら受け取る
        for key in ("title", "project", "projectPath"):
            if key in payload and not st.get(key):
                st[key] = payload[key]
        tasks = st.setdefault("tasks", {})
        for tid, t in payload.get("tasks", {}).items():
            if not isinstance(t, dict):
                continue
            cur = tasks.get(tid, {})
            # ts が新しい方を採用（オフライン変更のマージ用）
            if not cur or str(t.get("checkedAt", "")) >= str(cur.get("checkedAt", "")):
                tasks[tid] = {"title": t.get("title", cur.get("title", "")),
                              "done": bool(t.get("done")),
                              "checkedAt": t.get("checkedAt", now_iso())}
        st["updated"] = now_iso()
        save_json(path, st)
        self._send(200, {"ok": True, "saved": str(path)})


def cmd_serve(_args):
    ensure_dirs()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as e:
        print(f"エラー: ポート {PORT} を確保できません（{e}）。\n"
              f"既に todo-hub serve が動いているか、他プロセスが使用中です。\n"
              f"確認: lsof -i :{PORT}", file=sys.stderr)
        sys.exit(1)
    print(f"todo-hub serve: http://localhost:{PORT}/  (hub: {HUB})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------- open

def server_alive():
    try:
        with urllib.request.urlopen(f"http://localhost:{PORT}/api/health", timeout=1) as r:
            return r.status == 200
    except OSError:
        return False


def cmd_open(args):
    ensure_dirs()
    if not server_alive():
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "serve"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        import time
        for _ in range(20):
            if server_alive():
                break
            time.sleep(0.15)
    if server_alive():
        url = f"http://localhost:{PORT}/"
        if args.slug:
            url = f"http://localhost:{PORT}/pages/{args.slug}.html"
    else:
        # サーバが立てられない場合の file:// フォールバック（チェックは localStorage 保存）
        target = PAGES / f"{args.slug}.html" if args.slug else HUB / "index.html"
        url = target.as_uri()
        print("注意: サーバ起動に失敗したため file:// で開きます（チェックは localStorage 保存）",
              file=sys.stderr)
    subprocess.run(["open", "-na", "Google Chrome", "--args",
                    f"--app={url}", f"--user-data-dir={PROFILE}",
                    "--no-first-run", "--no-default-browser-check"], check=False)
    print(f"開きました: {url}")


# ---------------------------------------------------------------- register / reindex

def cmd_register(args):
    ensure_dirs()
    if not safe_slug(args.slug):
        print("エラー: slug は英数・ハイフン・ドットのみ使用可", file=sys.stderr)
        sys.exit(1)
    reg = load_registry()
    entry = {
        "slug": args.slug,
        "project": args.project,
        "projectPath": args.project_path or "",
        "title": args.title,
        "created": args.created or now_iso(),
        "page": args.legacy if args.legacy else f"pages/{args.slug}.html",
        "legacy": bool(args.legacy),
    }
    reg["pages"] = [e for e in reg["pages"] if e["slug"] != args.slug] + [entry]
    reg["pages"].sort(key=lambda e: e.get("created", ""), reverse=True)
    save_json(REGISTRY, reg)
    # state ファイルが無ければ骨組みを作る（tasks はページ側 POST か Claude の初期生成で埋まる）
    spath = STATE / f"{args.slug}.json"
    if not spath.exists():
        save_json(spath, {"slug": args.slug, "project": args.project,
                          "projectPath": entry["projectPath"], "title": args.title,
                          "created": entry["created"], "tasks": {}})
    print(f"登録しました: {args.slug}")
    cmd_reindex(args)


def find_hero(entry):
    """プロジェクトの assets/hero.png を heroes/ にコピーして相対パスを返す。無ければ None。"""
    ppath = entry.get("projectPath")
    if not ppath:
        return None
    src = Path(ppath) / "assets" / "hero.png"
    if not src.is_file():
        return None
    dst = HEROES / f"{entry['project']}.png"
    try:
        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(src, dst)
        return f"heroes/{entry['project']}.png"
    except OSError:
        return None


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


COLUMNS = ("todo", "doing", "done")  # 一覧ボードの列（index-template.html の data-col と対応）


def card_status(done, total):
    """カンバン列の判定。テンプレート側 JS の statusOf() と同じ規則（total==0 は未着手）。"""
    if total > 0 and done == total:
        return "done"
    return "doing" if done > 0 else "todo"


def render_card(e, s, hero):
    status = card_status(s["done"], s["total"])
    pct = round(s["done"] / s["total"] * 100) if s["total"] else 0
    page = e["page"]
    href = esc(page if not e.get("legacy") else Path(page).as_uri())
    created = esc(e.get("created", "")[:10])
    legacy = ' <span class="legacy-tag mono">legacy</span>' if e.get("legacy") else ""
    # hero 画像は未着手・進行中ではカバー、完了ではアバターとして出す（出し分けは CSS）。
    # 無ければプロジェクト名の先頭 2 文字
    avatar = (f'<img src="{esc(hero)}" alt="">' if hero else esc(e["project"][:2]))
    return f'''<a class="card" href="{href}" data-slug="{esc(e["slug"])}" data-status="{status}">
  <div class="card-cover">{avatar}</div>
  <div class="card-main">
    <div class="card-head"><svg class="card-icon" aria-hidden="true"><use href="#i-{status}"></use></svg><h3 class="card-title">{esc(e["title"])}</h3></div>
    <p class="card-meta"><span class="mono">{created}</span><span class="dot-sep"></span><span>{esc(e["project"])}</span>{legacy}</p>
  </div>
  <div class="card-foot">
    <span class="card-progress"><span class="card-bar"><span class="card-bar-fill" style="width:{pct}%"></span></span><span class="card-count mono">{s["done"]}/{s["total"]}</span></span>
    <span class="card-done-label mono">完了</span>
    <span class="avatar" title="{esc(e["project"])}">{avatar}</span>
  </div>
</a>'''


def render_nav(active, todo_count, report_count):
    """index.html と reports.html で共通のタブ。TODO の件数は未着手＋進行中、日報は登録件数。
    日報が 0 件のときは reports.html が空なのでタブ自体を出さない。"""
    tabs = [("todo", "index.html", "手作業 TODO", todo_count)]
    if report_count:
        tabs.append(("reports", "reports.html", "日報", report_count))
    current = ' aria-current="page"'
    links = "".join(
        f'<a class="tab" href="{href}"{current if key == active else ""}>'
        f'{label}<span class="tab-count mono">{n}</span></a>'
        for key, href, label, n in tabs)
    return f'<nav class="hub-tabs" aria-label="ハブ内の移動">{links}</nav>'


def build_index_html(template, items, report_count, generated):
    """items: (registry エントリ, page_summary, hero パス or None) の列。index.html の文字列を返す。"""
    cols = {k: [] for k in COLUMNS}
    for e, s, hero in items:
        cols[card_status(s["done"], s["total"])].append(render_card(e, s, hero))
    html = template.replace("__GENERATED__", generated)
    for k in COLUMNS:
        key = k.upper()
        html = (html.replace(f"__COL_{key}__", "\n".join(cols[k]))
                    .replace(f"__COUNT_{key}__", str(len(cols[k])))
                    .replace(f"__EMPTY_{key}__", "hidden" if cols[k] else ""))
    nav = render_nav("todo", len(cols["todo"]) + len(cols["doing"]), report_count)
    return html.replace("__NAV__", nav), {k: len(v) for k, v in cols.items()}


def active_todo_count():
    """未着手＋進行中のリスト数（reports.html のタブ表示用）。"""
    summaries = (page_summary(e) for e in load_registry()["pages"])
    return sum(1 for s in summaries if card_status(s["done"], s["total"]) != "done")


def cmd_reindex(_args):
    ensure_dirs()
    reg = load_registry()
    template = (ASSETS / "index-template.html").read_text(encoding="utf-8")
    items = [(e, page_summary(e), find_hero(e)) for e in reg["pages"]]
    html, counts = build_index_html(template, items, len(load_reports()["reports"]), now_iso())
    (HUB / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html を再生成しました（未着手 {counts['todo']} / 進行中 {counts['doing']} / "
          f"完了 {counts['done']}）: {HUB / 'index.html'}")


# ---------------------------------------------------------------- reports（shime visualize 作業ログ）

def load_reports():
    return load_json(REPORTS, {"reports": []})


def report_entry_from_path(path, title=""):
    """visualize HTML の絶対パスから登録エントリを組み立てる。
    project は daily_report の親ディレクトリ名、date はファイル名の YYYY-MM-DD から推定。"""
    p = Path(path).resolve()
    # user-guide の visualize ダッシュボード（<project>/USER_GUIDE/visualize/YYYY-MM-DD_user_guide.html）
    if p.parent.name == "visualize" and p.parent.parent.name == "USER_GUIDE":
        proj_dir = p.parents[2]
        m = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
        return {"project": proj_dir.name, "projectPath": str(proj_dir),
                "title": title or "User Guide ダッシュボード",
                "date": m.group(1) if m else "", "path": str(p)}
    # source-explainer の調査レポート（work/source-explainer/<slug>/06-private-visualization.html）
    if p.name == "06-private-visualization.html" and p.parent.parent.name == "source-explainer":
        slug = p.parent.name
        m = re.search(r"(\d{4}-\d{2}-\d{2})", slug)
        if m:
            date = m.group(1)
        else:
            m8 = re.search(r"(\d{4})(\d{2})(\d{2})", slug)
            date = "-".join(m8.groups()) if m8 else ""
        if not title:
            title = re.sub(r"_?(\d{4}-\d{2}-\d{2}|\d{8})_?", "", slug).replace("_", " ").strip() or slug
        return {"project": "source-explainer調査", "projectPath": str(p.parents[3]),
                "title": title, "date": date, "path": str(p)}
    project = p.parent.parent.name if p.parent.name == "daily_report" else p.parent.name
    m = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
    date = m.group(1) if m else ""
    if not title:
        title = re.sub(r"^\d{4}-\d{2}-\d{2}_?", "", p.stem)
        title = re.sub(r"_?visualize$", "", title).replace("_", " ").strip() or p.stem
    return {"project": project, "projectPath": str(p.parent.parent),
            "title": title, "date": date, "path": str(p)}


def save_reports_and_regen(reports):
    reports["reports"].sort(key=lambda e: (e.get("date", ""), e.get("path", "")), reverse=True)
    save_json(REPORTS, reports)
    gen_reports_html(reports)


def cmd_report_add(args):
    ensure_dirs()
    p = Path(args.path).resolve()
    if not p.is_file():
        print(f"エラー: ファイルが見つかりません: {p}", file=sys.stderr)
        sys.exit(1)
    entry = report_entry_from_path(p, args.title)
    reports = load_reports()
    reports["reports"] = [e for e in reports["reports"] if e["path"] != entry["path"]] + [entry]
    save_reports_and_regen(reports)
    print(f"作業ログを登録しました: {entry['project']} / {entry['title']}")
    cmd_reindex(args)


def scan_candidates(root, patterns):
    """root の外を指すシンボリックリンクを除いて、レポート候補を返す"""
    base = root.resolve()
    for pattern in patterns:
        for f in sorted(root.glob(pattern)):
            if f.resolve().is_relative_to(base):
                yield f


def cmd_report_scan(args):
    ensure_dirs()
    # --root 指定時はそこだけ、省略時は ~/claude code と ~/dev の両方を走査
    if args.root:
        roots = [Path(args.root).expanduser()]
    else:
        roots = [Path.home() / "claude code", Path.home() / "dev"]
    reports = load_reports()
    known = {e["path"] for e in reports["reports"]}
    # 消えたファイルの登録を prune
    before = len(reports["reports"])
    reports["reports"] = [e for e in reports["reports"] if Path(e["path"]).is_file()]
    pruned = before - len(reports["reports"])
    added = 0
    scan_globs = ("*/daily_report/*_visualize.html",
                  "*/work/source-explainer/*/06-private-visualization.html",
                  "*/USER_GUIDE/visualize/*_user_guide.html")
    for root in roots:
        for f in scan_candidates(root, scan_globs):
            if str(f.resolve()) not in known:
                reports["reports"].append(report_entry_from_path(f))
                added += 1
    save_reports_and_regen(reports)
    print(f"report-scan 完了: 追加 {added} / 削除 {pruned} / 合計 {len(reports['reports'])}")
    cmd_reindex(args)


# kanban（kargulstudio/kanban）風の配色・影。index-template.html / assets/kanban-theme.css と同じトークン
FONT_LINKS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
              '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
              '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600'
              '&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">')

REPORTS_CSS = """
  :root { --bg:#ffffff; --panel:#ffffff; --panel-2:#fafafa; --border:#ededed; --card-border:#e7e7e9;
    --text:#121212; --text-dim:#757575; --text-mute:#a1a1a1; --accent:#0d5fea;
    --shadow:0 2px 4px 0 rgb(35 35 35 / .03), 0 1px 2px 0 rgb(35 35 35 / .04), 0 0 0 3px rgb(205 205 205 / .12);
    --shadow-control:0 1px 2px 0 rgb(0 0 0 / .08), 0 0 0 1px #ededed;
    --font-sans:"Geist",-apple-system,BlinkMacSystemFont,"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
    --font-mono:"Geist Mono",ui-monospace,"SF Mono",Menlo,monospace; }
  * { box-sizing:border-box; }
  html,body { margin:0; padding:0; background:var(--bg); color:var(--text);
    font-family:var(--font-sans); font-size:14px; line-height:1.5; letter-spacing:-0.01em;
    -webkit-font-smoothing:antialiased; }
  /* ヘッダーは index.html と同じ構成（タイトル + TODO・日報のタブ） */
  header { padding:16px 24px 0; border-bottom:1px solid var(--border); }
  header h1 { margin:0; font-size:16px; font-weight:600; letter-spacing:-0.02em; }
  header .subtitle { margin:2px 0 0; color:var(--text-dim); font-size:12px; }
  .mono { font-family:var(--font-mono); font-variant-numeric:tabular-nums; }
  .hub-tabs { display:flex; gap:20px; margin-top:12px; }
  .tab { display:inline-flex; align-items:center; gap:6px; padding:8px 0 10px; margin-bottom:-1px;
    color:var(--text-dim); font-weight:500; text-decoration:none; border-bottom:2px solid transparent; }
  .tab:hover { color:var(--text); }
  .tab[aria-current="page"] { color:var(--text); border-bottom-color:var(--text); }
  .tab-count { color:var(--text-mute); font-size:12px; }
  .wrap { max-width:960px; margin:0 auto; padding:24px; }
  .proj { background:var(--panel); border-radius:16px; box-shadow:var(--shadow);
    margin-bottom:20px; overflow:hidden; }
  .proj-head { display:flex; align-items:center; gap:8px; padding:14px 18px;
    border-bottom:1px solid var(--card-border); }
  .proj-hero { width:20px; height:20px; object-fit:cover; border-radius:50%;
    box-shadow:var(--shadow-control); flex-shrink:0; }
  .proj-name { margin:0; font-size:14px; font-weight:600; letter-spacing:-0.02em; }
  .proj-count { color:var(--text-mute); font-size:12px; font-family:var(--font-mono); }
  .rep-row { display:flex; align-items:baseline; gap:14px; padding:10px 18px;
    border-top:1px solid var(--card-border); text-decoration:none; color:inherit; }
  .proj-head + .rep-row { border-top:none; }
  .rep-row:hover { background:var(--panel-2); }
  .rep-date { color:var(--text-mute); font-size:12px; flex-shrink:0; width:84px;
    font-family:var(--font-mono); font-variant-numeric:tabular-nums; }
  .rep-title { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  details.older summary { padding:10px 18px; font-size:12px; color:var(--text-dim);
    cursor:pointer; border-top:1px solid var(--card-border); }
  details.older summary:hover { background:var(--panel-2); }
  .empty { text-align:center; color:var(--text-mute); padding:48px 0; }
  footer { max-width:960px; margin:0 auto; padding:8px 24px 40px;
    color:var(--text-mute); font-size:12px; text-align:center; }
  footer code { font-family:var(--font-mono); }
  @media (max-width:600px) { header { padding:14px 16px 0; } .wrap { padding:16px; }
    .rep-row { padding:10px 14px; } .proj-head { padding:12px 14px; } }
"""

RECENT_SHOWN = 5  # プロジェクトごとに折りたたまず表示する最新件数


def gen_reports_html(reports):
    # プロジェクト別にまとめ、最終更新が新しいプロジェクトを上に
    by_proj = {}
    for e in reports["reports"]:
        by_proj.setdefault(e["project"], []).append(e)
    projects = sorted(by_proj.items(),
                      key=lambda kv: max(e.get("date", "") for e in kv[1]), reverse=True)

    def row(e):
        # サーバ経由で配信（http で開いたハブから file:// リンクはブロックされるため）
        href = esc(f"http://localhost:{PORT}/file?path={urllib.parse.quote(e['path'])}")
        return (f'<a class="rep-row" href="{href}">'
                f'<span class="rep-date">{esc(e.get("date", ""))}</span>'
                f'<span class="rep-title">{esc(e["title"])}</span></a>')

    sections = []
    for name, entries in projects:
        entries = sorted(entries, key=lambda e: (e.get("date", ""), e["path"]), reverse=True)
        recent = "\n".join(row(e) for e in entries[:RECENT_SHOWN])
        older = entries[RECENT_SHOWN:]
        older_html = ""
        if older:
            older_html = (f'<details class="older"><summary>過去 {len(older)} 件</summary>'
                          + "\n".join(row(e) for e in older) + "</details>")
        # manual-todo カードと同じ hero 取得ロジックを流用（heroes/<project>.png）
        hero = find_hero(entries[0])
        hero_html = f'<img class="proj-hero" src="{esc(hero)}" alt="">' if hero else ""
        sections.append(f'''<section class="proj">
  <div class="proj-head">{hero_html}<h2 class="proj-name">{esc(name)}</h2>
    <span class="proj-count">{len(entries)} 件</span></div>
  {recent}
  {older_html}
</section>''')
    body = "\n".join(sections) if sections else '<p class="empty">作業ログはまだありません。</p>'
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>日報 — 手作業 TODO ハブ</title>
{FONT_LINKS}
<style>{REPORTS_CSS}</style>
</head>
<body>
<header>
  <h1>手作業 TODO ハブ</h1>
  <p class="subtitle">日報（shime visualize）と source-explainer 調査レポート。リンクは todo-hub サーバ経由で配信（サーバ停止中は開けません）。</p>
  {render_nav("reports", active_todo_count(), len(reports["reports"]))}
</header>
<div class="wrap">
{body}
</div>
<footer>生成: {now_iso()} ／ 更新は <code>todo-hub report-add / report-scan</code></footer>
</body>
</html>
'''
    (HUB / "reports.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- launchd

PLIST = Path.home() / "Library" / "LaunchAgents" / "com.local.todo-hub.plist"


def cmd_install_launchd(_args):
    ensure_dirs()
    python3 = shutil.which("python3") or "/usr/bin/python3"
    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.local.todo-hub</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python3}</string>
    <string>{Path(__file__).resolve()}</string>
    <string>serve</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>{HUB}/todo-hub.log</string>
</dict>
</plist>
'''
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    PLIST.write_text(plist)
    subprocess.run(["launchctl", "unload", str(PLIST)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    subprocess.run(["launchctl", "load", str(PLIST)], check=False)
    print(f"launchd に登録しました: {PLIST}\n解除: launchctl unload {PLIST} && rm {PLIST}")


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(prog="todo-hub", description="manual-todo 集約ハブ CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve", help="サーバをフォアグラウンド起動")
    po = sub.add_parser("open", help="サーバ自動起動 + Chrome アプリモードで開く")
    po.add_argument("slug", nargs="?", default=None)
    pr = sub.add_parser("register", help="TODO ページを registry に登録")
    pr.add_argument("--slug", required=True)
    pr.add_argument("--project", required=True)
    pr.add_argument("--project-path", default="")
    pr.add_argument("--title", required=True)
    pr.add_argument("--created", default="")
    pr.add_argument("--legacy", default="", help="既存 HTML の絶対パス（残置分の登録用）")
    sub.add_parser("reindex", help="index.html を再生成")
    pa = sub.add_parser("report-add", help="shime visualize HTML を作業ログに登録")
    pa.add_argument("--path", required=True, help="visualize HTML の絶対パス")
    pa.add_argument("--title", default="", help="表示タイトル（省略時はファイル名から推定）")
    ps = sub.add_parser("report-scan", help="daily_report/*_visualize.html を一括登録 + prune")
    ps.add_argument("--root", default="",
                    help="走査ルート（既定: ~/claude code と ~/dev の両方）")
    sub.add_parser("install-launchd", help="サーバを launchd 常駐化（オプション）")
    args = p.parse_args()
    {"serve": cmd_serve, "open": cmd_open, "register": cmd_register,
     "reindex": cmd_reindex, "report-add": cmd_report_add, "report-scan": cmd_report_scan,
     "install-launchd": cmd_install_launchd}[args.cmd](args)


if __name__ == "__main__":
    main()
