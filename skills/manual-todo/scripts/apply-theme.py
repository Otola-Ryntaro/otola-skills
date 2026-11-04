#!/usr/bin/env python3
# where: ~/.claude/skills/manual-todo/scripts/apply-theme.py
# what : assets/kanban-theme.css を manual-todo ページ（と template.html）の </body> 直前へ差し込む。
#        マーカーで囲むので再実行すると中身を置き換えるだけ（冪等）
# why  : 既存ページの <style> は系統がばらばらで書き換えると壊しやすい。後勝ちの上書きブロックを
#        1 か所に足すだけにすれば、テーマを直したときも全ページへ同じ手順で再配布できる。
#        後付けアドオンの <style> が body 末尾にあるため、それより後ろの </body> 直前に置く
#
# 使い方:
#   apply-theme.py FILE...           # 差し込み／置換（変更したファイル数を表示）
#   apply-theme.py --check FILE...   # 書き込まず、未適用・古いファイルを列挙（1 件でもあれば exit 1）

import argparse
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
START = "<!-- kanban-theme:start -->"
END = "<!-- kanban-theme:end -->"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600'
         '&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">')
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)


def build_block(css):
    return f"{START}\n{FONTS}\n<style>\n{css.rstrip()}\n</style>\n{END}\n"


def themed(html, block):
    """ブロックを除去してから最後の </body> 直前に入れ直した HTML を返す。</body> が無ければ None。"""
    stripped = BLOCK_RE.sub("", html)
    idx = stripped.rfind("</body>")
    if idx < 0:
        return None
    return stripped[:idx] + block + stripped[idx:]


def main(argv=None):
    ap = argparse.ArgumentParser(description="manual-todo ページへ kanban テーマを適用する")
    ap.add_argument("--check", action="store_true", help="書き込まずに差分の有無だけ報告する")
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args(argv)
    block = build_block((ASSETS / "kanban-theme.css").read_text(encoding="utf-8"))
    changed, skipped = [], []
    for f in args.files:
        html = f.read_text(encoding="utf-8")
        new = themed(html, block)
        if new is None:
            skipped.append(f)
            print(f"警告: </body> が無いためスキップ: {f}", file=sys.stderr)
            continue
        if new != html:
            changed.append(f)
            if not args.check:
                f.write_text(new, encoding="utf-8")
    verb = "未適用・古い" if args.check else "更新"
    print(f"{verb} {len(changed)} 件 / 対象 {len(args.files)} 件 / スキップ {len(skipped)} 件")
    for f in changed if args.check else []:
        print(f"  {f}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
