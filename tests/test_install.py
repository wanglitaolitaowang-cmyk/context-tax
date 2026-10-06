"""Temporary-directory installation tests; not real host discovery or Windows E2E."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / 'install.py'

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dest = self.root / 'context-tax'
    def tearDown(self):
        self.temp.cleanup()
    def run_install(self, *args):
        return subprocess.run([sys.executable, str(INSTALL), '--dest', str(self.dest), *args], capture_output=True, text=True)
    def test_dry_run_has_no_writes(self):
        result = self.run_install('--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.dest.exists())
    def test_install_and_byte_check(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.dest / 'SKILL.md').is_file())
        self.assertTrue((self.dest / 'scripts/context_tax.py').is_file())
        self.assertEqual(self.run_install('--check').returncode, 0)
        self.assertEqual(len(list(self.root.iterdir())), 1)
    def test_existing_folder_is_not_overwritten(self):
        self.dest.mkdir(); sentinel = self.dest / 'SKILL.md'; sentinel.write_text('keep me',encoding='utf-8')
        self.assertEqual(self.run_install().returncode, 1)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep me')
        self.assertEqual(len(list(self.dest.iterdir())), 1)
    def test_changed_file_detected_read_only(self):
        self.assertEqual(self.run_install().returncode, 0)
        target = self.dest / 'SKILL.md'; target.write_text('modified',encoding='utf-8')
        self.assertEqual(self.run_install('--check').returncode, 1)
        self.assertEqual(target.read_text(encoding='utf-8'), 'modified')
    def test_missing_file_detected(self):
        self.assertEqual(self.run_install().returncode, 0)
        (self.dest / 'SKILL.md').unlink()
        self.assertEqual(self.run_install('--check').returncode, 1)
    def test_non_skill_basename_rejected(self):
        self.dest = self.root / 'unrelated'
        self.assertEqual(self.run_install().returncode, 1)
        self.assertFalse(self.dest.exists())
    @unittest.skipIf(sys.platform == 'win32', 'Windows symlink permission is host-dependent')
    def test_link_destination_rejected(self):
        actual = self.root / 'actual'; actual.mkdir()
        self.dest.symlink_to(actual, target_is_directory=True)
        self.assertEqual(self.run_install().returncode, 1)
        self.assertEqual(list(actual.iterdir()), [])

if __name__ == '__main__':
    unittest.main()
