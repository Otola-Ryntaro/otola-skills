# where: ~/.claude/skills/manual-todo/tests/test_vscode_api.py
# what : /api/vscode が自分のページからの POST でだけ VS Code を起動することを検証する
# why  : GET で起動できると、他サイトの <img> などからローカルのハブを叩かれるため
# 実行: python3 -m unittest discover -s ~/.claude/skills/manual-todo/tests

import http.client
import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("todo_hub_api", ROOT / "scripts" / "todo-hub.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)

SELF = "http://localhost:7799"


class VscodeApiTest(unittest.TestCase):
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
        self.project = Path(tmp.name).resolve()
        self.target = self.project / "docs.md"
        self.target.write_text("x", encoding="utf-8")
        for patcher in (
            mock.patch.object(hub, "load_registry",
                              return_value={"pages": [{"projectPath": str(self.project)}]}),
            mock.patch.object(hub.shutil, "which", return_value="code"),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        run = mock.patch.object(hub.subprocess, "run")
        self.run_mock = run.start()
        self.addCleanup(run.stop)

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1])
        sent = {"Host": "localhost:7799", **(headers or {})}
        conn.request(method, path, body=body, headers=sent)
        res = conn.getresponse()
        res.read()
        conn.close()
        return res.status

    def post(self, payload, origin=SELF, ctype="application/json"):
        return self.request("POST", "/api/vscode", json.dumps(payload),
                            {"Origin": origin, "Content-Type": ctype})

    def test_get_never_launches_vscode(self):
        status = self.request("GET", f"/api/vscode?path={self.target}")
        self.assertEqual(status, 405)
        self.run_mock.assert_not_called()

    def test_get_check_only_confirms_existence(self):
        status = self.request("GET", f"/api/vscode?path={self.target}&check=1")
        self.assertEqual(status, 200)
        self.run_mock.assert_not_called()

    def test_post_from_own_page_opens_file_at_line(self):
        self.assertEqual(self.post({"path": str(self.target), "line": "24"}), 200)
        args = self.run_mock.call_args.args[0]
        self.assertEqual(args, ["code", str(self.project), "--goto", f"{self.target}:24"])

    def test_post_from_other_origin_is_rejected(self):
        self.assertEqual(self.post({"path": str(self.target)}, origin="https://evil.example"), 403)
        self.run_mock.assert_not_called()

    def test_post_requires_json(self):
        self.assertEqual(self.post({"path": str(self.target)}, ctype="text/plain"), 403)
        self.run_mock.assert_not_called()

    def test_post_outside_registered_project_is_rejected(self):
        self.assertEqual(self.post({"path": "/etc/hosts"}), 403)
        self.run_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
