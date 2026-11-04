import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / 'skills/vibehoster-publish/scripts/package_static.py'
spec = importlib.util.spec_from_file_location('package_static', SCRIPT)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageStaticTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'build'
        self.root.mkdir()
        (self.root / 'index.html').write_text('<h1>Hello</h1>')
        self.output = Path(self.tmp.name) / 'site.zip'

    def tearDown(self):
        self.tmp.cleanup()

    def test_packages_static_build(self):
        (self.root / 'logo.png').write_bytes(b'\x89PNG\xff')
        count, _ = packager.package(self.root, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read('logo.png'), b'\x89PNG\xff')
            self.assertEqual(set(archive.namelist()), {'index.html', 'logo.png'})
        self.assertEqual(count, 2)

    def test_rejects_secrets_symlinks_and_unsupported_files(self):
        for name in ('.env', 'config.env', 'app.js.map'):
            path = self.root / name
            path.write_text('secret')
            with self.subTest(name=name), self.assertRaises(ValueError):
                packager.package(self.root, self.output)
            path.unlink()
        (self.root / 'link.js').symlink_to(self.root / 'index.html')
        with self.assertRaises(ValueError):
            packager.package(self.root, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_and_archive_inside_build_are_rejected(self):
        self.output.write_bytes(b'keep')
        with self.assertRaises(ValueError):
            packager.package(self.root, self.output)
        self.assertEqual(self.output.read_bytes(), b'keep')
        with self.assertRaises(ValueError):
            packager.package(self.root, self.root / 'site.zip')


if __name__ == '__main__':
    unittest.main()
