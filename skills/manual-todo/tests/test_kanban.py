# where: ~/.claude/skills/manual-todo/tests/test_kanban.py
# what : kanban 風ハブの列判定・index.html 生成・ページへのテーマ差し込みを検証する
# why  : テーマ差し込みは全ページへ繰り返し実行するので冪等性と位置（アドオン style より後）を保証したい
# 実行: python3 -m unittest discover -s ~/.claude/skills/manual-todo/tests

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hub = load("todo_hub", "todo-hub.py")
theme = load("apply_theme", "apply-theme.py")


def entry(slug, project="proj", title="タイトル"):
    return {"slug": slug, "project": project, "title": title,
            "page": f"pages/{slug}.html", "created": "2026-10-08T10:00:00+09:00"}


class CardStatusTest(unittest.TestCase):
    def test_columns(self):
        self.assertEqual(hub.card_status(0, 5), "todo")
        self.assertEqual(hub.card_status(2, 5), "doing")
        self.assertEqual(hub.card_status(5, 5), "done")

    def test_empty_list_is_todo(self):
        self.assertEqual(hub.card_status(0, 0), "todo")


class BuildIndexTest(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "assets" / "index-template.html").read_text(encoding="utf-8")
        items = [
            (entry("a"), {"done": 0, "total": 3}, None),
            (entry("b", project="<x>"), {"done": 1, "total": 3}, "heroes/b.png"),
            (entry("c"), {"done": 3, "total": 3}, None),
            (entry("d"), {"done": 2, "total": 3}, None),
        ]
        self.html, self.counts = hub.build_index_html(self.template, items, 7, "GEN")

    def test_counts_per_column(self):
        self.assertEqual(self.counts, {"todo": 1, "doing": 2, "done": 1})

    def test_page_markers_appear_once(self):
        self.assertEqual(self.html.count('<main class="cards-grid" id="cards">'), 1)
        self.assertEqual(self.html.count('var API = "http://localhost:7799";'), 1)
        self.assertEqual(self.html.count("</head>"), 1)
        self.assertEqual(self.html.count("</body>"), 1)

    def test_no_placeholder_left(self):
        self.assertNotRegex(self.html, r"__[A-Z_]+__")

    def test_card_lands_in_its_column(self):
        done_col = self.html.split('data-col="done"')[1]
        self.assertIn('data-slug="c" data-status="done"', done_col)
        self.assertNotIn('data-slug="a"', done_col)

    def test_project_name_is_escaped(self):
        self.assertIn("&lt;x&gt;", self.html)
        self.assertNotIn("<x>", self.html)

    def test_empty_column_shows_placeholder(self):
        html, _ = hub.build_index_html(self.template, [], 0, "GEN")
        self.assertEqual(html.count('<p class="col-empty" >'), 3)
        self.assertNotIn('href="reports.html"', html)  # 日報 0 件ならタブを出さない

    def test_nav_tabs_count_open_lists_and_reports(self):
        self.assertIn('<a class="tab" href="index.html" aria-current="page">手作業 TODO'
                      '<span class="tab-count mono">3</span></a>', self.html)
        self.assertIn('<a class="tab" href="reports.html">日報<span class="tab-count mono">7</span></a>',
                      self.html)

    def test_cover_image_is_rendered(self):
        self.assertIn('<div class="card-cover"><img src="heroes/b.png" alt=""></div>', self.html)
        self.assertIn('<div class="card-cover">pr</div>', self.html)


class ApplyThemeTest(unittest.TestCase):
    PAGE = ("<html><head><style>.a{}</style></head><body><main></main>\n"
            "<style>.task-vscode{color:red}</style>\n</body></html>")

    def test_idempotent_and_after_addon_style(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "p.html"
            f.write_text(self.PAGE, encoding="utf-8")
            self.assertEqual(theme.main([str(f)]), 0)
            once = f.read_text(encoding="utf-8")
            theme.main([str(f)])
            twice = f.read_text(encoding="utf-8")
            self.assertEqual(once, twice)
            self.assertEqual(once.count(theme.START), 1)
            self.assertLess(once.index(".task-vscode{color:red}"), once.index(theme.START))
            self.assertLess(once.index(theme.END), once.index("</body>"))
            self.assertEqual(theme.main(["--check", str(f)]), 0)

    def test_check_reports_unthemed_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "p.html"
            f.write_text(self.PAGE, encoding="utf-8")
            self.assertEqual(theme.main(["--check", str(f)]), 1)
            self.assertEqual(f.read_text(encoding="utf-8"), self.PAGE)


if __name__ == "__main__":
    unittest.main()
