"""Final packaging must distinguish a verified peer run from a reference replay."""
import io
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/e11e12'))
import package_submission


class SubmissionStatusTests(unittest.TestCase):
    def make_package(self, status, binary=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        evidence = root/'evidence'
        evidence.mkdir()
        (evidence/'SUBMISSION_INDEX.md').write_text('# Actual file index')
        if binary:
            (evidence/'main.o').write_bytes(b'recorded original object evidence')
            (evidence/'unreferenced.o').write_bytes(b'not necessary')
            (evidence/'result.json').write_text(json.dumps({'schema_version': 'e11e12-1',
                'job_id': 'job-test', 'artifacts': [{'uri': 'artifact://job-test/main.o',
                    'sha256': hashlib.sha256((evidence/'main.o').read_bytes()).hexdigest(),
                    'bytes': (evidence/'main.o').stat().st_size}]}))
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w'):
            pass
        output = root/'submission.zip'
        with patch.object(package_submission.subprocess, 'check_output', return_value=stream.getvalue()):
            package_submission.package(evidence, output, 'a'*40, status)
        return zipfile.ZipFile(output)

    def test_verified_peer_final_materials_do_not_say_still_waiting(self):
        with self.make_package({'experiment': 'E12', 'submission_materials_complete': True,
                                'peer_confirmation': 'VERIFIED_B11_INDEPENDENT_CJSON_API_RUN'}) as archive:
            readme = archive.read('README-先读.md').decode()
            self.assertIn('B11 独立 cJSON API 访问及服务器原始记录已交叉核验', readme)
            self.assertNotIn('不能把本包标成 E12 全部通过', readme)
            self.assertIn('不代表教师已认可选题例外或 GitHub 已合并', readme)
            self.assertEqual(archive.read('交付目录与复现.md'), b'# Actual file index')

    def test_reference_package_keeps_pending_warning(self):
        with self.make_package({'peer_confirmation': 'PENDING'}) as archive:
            readme = archive.read('README-先读.md').decode()
            self.assertIn('不构成 B11 分机访问确认', readme)
            self.assertIn('不能把本包标成 E12 全部通过', readme)

    def test_keeps_manifest_referenced_binary_but_not_unreferenced_build_cache(self):
        with self.make_package({}, binary=True) as archive:
            self.assertEqual(archive.read('evidence/main.o'), b'recorded original object evidence')
            self.assertNotIn('evidence/unreferenced.o', archive.namelist())
