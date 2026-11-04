# where: ~/.claude/skills/manual-todo/tests/test_hub_hardening.py
# what : ハブの配信範囲とレポートの隔離を検証する
# why  : ハブの配下には状態ファイルや Chrome プロファイルがあり、取り込んだレポートは信用できないため
# 実行: python3 -m unittest discover -s ~/.claude/skills/manual-todo/tests

import http.client
import importlib.util
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("todo_hub_hardening", ROOT / "scripts" / "todo-hub.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


class HubServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), hub.Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.hub_dir = self.base / "todo"
        for rel in ("index.html", "reports.html", "pages/a.html", "heroes/a.png",
                    "state/registry.json", "chrome-profile/Cookies"):
            f = self.hub_dir / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("x", encoding="utf-8")
        sibling = self.base / "todo-other" / "secret.html"
        sibling.parent.mkdir()
        sibling.write_text("x", encoding="utf-8")
        self.report = self.base / "report.html"
        self.report.write_text("<p>x</p>", encoding="utf-8")
        self.key = self.base / "id_rsa"
        self.key.write_text("x", encoding="utf-8")
        for patcher in (
            mock.patch.object(hub, "HUB", self.hub_dir),
            mock.patch.object(hub, "load_reports", return_value={"reports": [
                {"path": str(self.report)}, {"path": str(self.key)}]}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1])
        conn.putrequest("GET", path, skip_host=True)
        conn.putheader("Host", "localhost:7799")
        conn.endheaders()
        res = conn.getresponse()
        res.read()
        conn.close()
        return res

    def test_public_files_are_served(self):
        for path in ("/", "/index.html", "/reports.html", "/pages/a.html", "/heroes/a.png"):
            self.assertEqual(self.get(path).status, 200, path)

    def test_private_files_are_refused(self):
        for path in ("/state/registry.json", "/chrome-profile/Cookies", "/../todo-other/secret.html"):
            self.assertEqual(self.get(path).status, 403, path)

    def test_report_runs_in_sandbox(self):
        res = self.get(f"/file?path={self.report}")
        self.assertEqual(res.status, 200)
        self.assertIn("sandbox", res.getheader("Content-Security-Policy", ""))
        self.assertNotIn("allow-same-origin", res.getheader("Content-Security-Policy", ""))

    def test_registered_non_html_is_refused(self):
        self.assertEqual(self.get(f"/file?path={self.key}").status, 403)


class ScanCandidatesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.root = self.base / "projects"
        self.reports = self.root / "app" / "daily_report"
        self.reports.mkdir(parents=True)
        self.outside = self.base / "secret.html"
        self.outside.write_text("x", encoding="utf-8")

    def scan(self):
        return [p.name for p in hub.scan_candidates(self.root, ("*/daily_report/*_visualize.html",))]

    def test_regular_report_is_found(self):
        (self.reports / "a_visualize.html").write_text("x", encoding="utf-8")
        self.assertEqual(self.scan(), ["a_visualize.html"])

    def test_symlink_to_outside_is_skipped(self):
        (self.reports / "b_visualize.html").symlink_to(self.outside)
        self.assertEqual(self.scan(), [])

    def test_symlinked_directory_to_outside_is_skipped(self):
        real = self.base / "elsewhere" / "daily_report"
        real.mkdir(parents=True)
        (real / "c_visualize.html").write_text("x", encoding="utf-8")
        (self.root / "linked").symlink_to(real.parent)
        self.assertEqual(self.scan(), [])


if __name__ == "__main__":
    unittest.main()
