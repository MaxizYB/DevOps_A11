import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_package import verify

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'input').write_bytes(b'original')
        (self.root/'SHA256SUMS.json').write_text(json.dumps({'input':hashlib.sha256(b'original').hexdigest()}))

    def test_verified_bytes(self):
        self.assertEqual(verify(self.root),dict(status='PASS',files=1))

    def test_changed_bytes_rejected(self):
        (self.root/'input').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):verify(self.root)

    def test_extra_file_rejected(self):
        (self.root/'extra').write_text('extra')
        with self.assertRaisesRegex(ValueError,'unexpected files'):verify(self.root)

    def test_symlink_rejected(self):
        (self.root/'input').unlink()
        (self.root/'input').symlink_to(self.root/'SHA256SUMS.json')
        with self.assertRaises(ValueError):verify(self.root)

if __name__=='__main__':unittest.main()
