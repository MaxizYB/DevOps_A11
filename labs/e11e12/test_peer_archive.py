"""Treat received evidence as untrusted data, never as executable code."""
import io
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/e11e12'))
from audit_peer_return import extract, safe_members


class PeerArchiveTests(unittest.TestCase):
    def archive(self, names):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for name in names:
                archive.writestr(name, b'evidence')
        return zipfile.ZipFile(io.BytesIO(stream.getvalue()))

    def test_traversal_windows_paths_git_and_absolute_are_rejected(self):
        for name in ('../escape', '/absolute', 'run/../escape', 'C:/escape',
                     'run\\escape', 'run/.git/config', 'run//empty'):
            with self.subTest(name=name), self.archive([name]) as archive:
                with self.assertRaisesRegex(ValueError, 'Unsafe'):
                    safe_members(archive)

    def test_symlink_is_rejected(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            item = zipfile.ZipInfo('run/link')
            item.create_system = 3
            item.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(item, '../outside')
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                safe_members(archive)

    def test_archive_is_validated_before_extracting_any_file(self):
        with tempfile.TemporaryDirectory() as folder, self.archive(['run/ok', '../bad']) as archive:
            with self.assertRaises(ValueError):
                extract(archive, Path(folder))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_preserves_exact_bytes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder, self.archive(['run/report.json']) as archive:
            extract(archive, Path(folder))
            self.assertEqual((Path(folder)/'run/report.json').read_bytes(), b'evidence')
            with self.assertRaises(FileExistsError):
                extract(archive, Path(folder))
