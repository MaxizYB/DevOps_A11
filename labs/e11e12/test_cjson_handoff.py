"""The peer handoff contains only agreed inputs and never private credentials."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts/e11e12'))
from package_cjson_handoff import package


class CjsonHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request = self.root/'request.json'
        self.dataset = self.root/'dataset.json'
        self.deployment = self.root/'deployment.json'
        self.out = self.root/'handoff.zip'
        self.request.write_text(json.dumps({'mode': 'e12', 'project_profile': 'cjson',
            'base': 'a'*40, 'target': 'b'*40, 'candidate': '/course/data/candidate',
            'broken_dockerfile': '/course/data/broken'}))
        (self.root/'candidate').write_bytes(b'FROM test-candidate\n')
        (self.root/'broken').write_bytes(b'FROM test-broken\n')
        self.dataset.write_text(json.dumps({'maintenance_claim': False,
            'commits': {'base': {'sha': 'a'*40}, 'target': {'sha': 'b'*40}},
            'harness': {name: hashlib.sha256((self.root/name).read_bytes()).hexdigest()
                        for name in ('candidate', 'broken')}}))
        self.deployment.write_text(json.dumps({'source_commit': 'c'*40,
            'implementation_sha256': 'd'*64, 'implementation_differs_from_commit': False}))

    def test_allowlisted_archive_is_complete_and_hashed(self):
        (self.root/'private-password.txt').write_text('not for handoff')
        result = package(self.request, self.dataset, self.deployment, self.out)
        self.assertEqual(result['files'], 11)
        with zipfile.ZipFile(self.out) as archive:
            self.assertNotIn('private-password.txt', archive.namelist())
            manifest = json.loads(archive.read('SHA256SUMS.json'))
            self.assertEqual(set(manifest), set(archive.namelist())-{'SHA256SUMS.json'})
            for name, digest in manifest.items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
            compile(archive.read('run_peer_client.py'), 'run_peer_client.py', 'exec')

    def test_changed_candidate_is_rejected_before_archive_creation(self):
        (self.root/'candidate').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'differs from agreed dataset'):
            package(self.request, self.dataset, self.deployment, self.out)
        self.assertFalse(self.out.exists())

    def test_dirty_deployment_is_not_advertised_as_agreed_source(self):
        deployed = json.loads(self.deployment.read_text())
        deployed['implementation_differs_from_commit'] = True
        self.deployment.write_text(json.dumps(deployed))
        with self.assertRaisesRegex(ValueError, 'clean, versioned'):
            package(self.request, self.dataset, self.deployment, self.out)

    def test_previous_handoff_is_not_overwritten(self):
        self.out.write_bytes(b'keep previous archive')
        with self.assertRaises(FileExistsError):
            package(self.request, self.dataset, self.deployment, self.out)
        self.assertEqual(self.out.read_bytes(), b'keep previous archive')
