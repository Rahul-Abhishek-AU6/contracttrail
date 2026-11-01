import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "contracttrail.py"

PATCH = """diff --git a/src/api.py b/src/api.py
index 111..222 100644
--- a/src/api.py
+++ b/src/api.py
@@ -1 +1 @@
-def fetch_user(user_id):
+def fetch_user(user_id, include_roles=False):
diff --git a/src/widget.ts b/src/widget.ts
index 111..222 100644
--- a/src/widget.ts
+++ b/src/widget.ts
@@ -1 +1 @@
-export function renderCard() {}
+export function renderCard(theme: string) {}
"""


class ContractTrailTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "src" / "use.py").write_text("from api import fetch_user\nfetch_user(3)\n")
        (root / "tests" / "test_api.py").write_text("from api import fetch_user\ndef test_user(): fetch_user(3)\n")
        (root / "src" / "widget-consumer.ts").write_text("renderCard()\n")
        (root / "danger.py").write_text("# do not execute: touch SHOULD_NOT_EXIST\n")
        patch = root / "change.patch"
        patch.write_text(PATCH)
        return temp, root, patch

    def test_receipt_groups_consumers_and_tests(self):
        temp, root, patch = self.fixture()
        self.addCleanup(temp.cleanup)
        result = subprocess.run(["python3", str(CLI), "scan", str(root), "--patch", str(patch)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("added `fetch_user`", result.stdout)
        self.assertIn("test-path references: 2", result.stdout)
        self.assertIn("src/use.py", result.stdout)
        self.assertFalse((root / "SHOULD_NOT_EXIST").exists())

    def test_json_and_strict_mode(self):
        temp, root, patch = self.fixture()
        self.addCleanup(temp.cleanup)
        out = root / "receipt.json"
        result = subprocess.run(["python3", str(CLI), "scan", str(root), "--patch", str(patch), "--json", str(out), "--strict"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        receipt = json.loads(out.read_text())
        self.assertEqual(len(receipt["declaration_changes"]), 4)
        self.assertEqual(receipt["declaration_changes"][0]["change"]["symbol"], "fetch_user")


if __name__ == "__main__":
    unittest.main()
