import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pipeline
import server

class Contracts(unittest.TestCase):
    def report(self):return {'schema_version':'e11e12-1','kind':'incremental-check','commit':'a'*40,'status':'SUCCEEDED'}
    def test_accept_current_report(self):pipeline.check_envelope(self.report(),'a'*40,'incremental-check')
    def test_reject_old_commit(self):
        with self.assertRaisesRegex(pipeline.Failure,'another commit'):pipeline.check_envelope(self.report(),'b'*40)
    def test_reject_schema(self):
        r=self.report();r['schema_version']='old'
        with self.assertRaises(pipeline.Failure):pipeline.check_envelope(r,'a'*40)
    def test_reject_failed_upstream(self):
        r=self.report();r['status']='FAILED'
        with self.assertRaises(pipeline.Failure):pipeline.check_envelope(r,'a'*40)
    def test_reject_wrong_artifact_kind(self):
        with self.assertRaises(pipeline.Failure):pipeline.check_envelope(self.report(),'a'*40,'fixed-md')
    def test_artifact_uses_relative_uri_and_content_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'x.json';p.write_text('{}')
            a=pipeline.artifact(p,root,'job-1');self.assertEqual(a['uri'],'artifact://job-1/x.json');self.assertEqual(len(a['sha256']),64)
    def test_existing_evidence_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'keep').write_text('keep')
            with self.assertRaises(pipeline.Failure):pipeline.execute({},root)
            self.assertEqual((root/'keep').read_text(),'keep')
    def test_changed_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json';p.write_text('{}')
            with self.assertRaises(pipeline.Failure):pipeline.load_artifact(p,'0'*64)
    def test_same_key_same_request_same_job(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);store=server.Store(root/'jobs')
            request={'mode':'e11-a','repo':str(pipeline.ROOT/'data/p'),'base':'a','target':'b'}
            with patch.object(server,'validate_request',return_value=request), patch.object(store.pool,'submit'):
                one=store.submit(request,'same');two=store.submit(request,'same')
                self.assertEqual(one['job_id'],two['job_id'])
                changed=dict(request,target='c')
                with self.assertRaisesRegex(ValueError,'IDEMPOTENCY_CONFLICT'):store.submit(changed,'same')
            store.pool.shutdown()
    def test_api_rejects_repo_outside_data(self):
        with tempfile.TemporaryDirectory() as d:
            store=server.Store(Path(d)/'jobs')
            with self.assertRaises(ValueError):store.submit({'mode':'e11-a','repo':str(Path(d)),'base':'a','target':'b'},'k')
            store.pool.shutdown()

    def test_request_requires_full_distinct_commits(self):
        with self.assertRaisesRegex(pipeline.Failure, 'full 40-character'):
            pipeline.validate_request({'mode':'e11-a','repo':str(pipeline.ROOT/'data'),'base':'a','target':'b'})

    def test_e12_requires_candidate_and_rejects_fixed_report(self):
        data_root = pipeline.ROOT/'data'
        data_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data_root) as d:
            root=Path(d); repo=root/'repo';repo.mkdir();candidate=root/'candidate.Dockerfile';candidate.write_text('FROM example@sha256:'+'0'*64)
            base='a'*40;target='b'*40
            request={'mode':'e12','repo':str(repo),'base':base,'target':target}
            with self.assertRaisesRegex(pipeline.Failure, 'candidate'):
                pipeline.validate_request(request)
            request.update(candidate=str(candidate),fixed_report=str(root/'fixed.json'))
            with self.assertRaisesRegex(pipeline.Failure, 'fixed_report'):
                pipeline.validate_request(request)

    def test_e11a_executes_without_fixed_report(self):
        data_root = pipeline.ROOT/'data'
        data_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=data_root) as d, tempfile.TemporaryDirectory() as output:
            root=Path(d);repo=root/'repo';repo.mkdir()
            base='a'*40;target='b'*40
            actual=[{'target':'main.o','dependency':'main.c'},
                    {'target':'helper.o','dependency':'helper.c'}]
            findings=[]
            def fake_full(project, folder, timeout=120):
                folder.mkdir(parents=True,exist_ok=True)
                (folder/'actual-graph.json').write_text(json.dumps(actual))
                (folder/'declared-graph.json').write_text('[]')
                report={'status':'SUCCEEDED','findings':findings}
                (folder/'findings.json').write_text(json.dumps(report))
                return report
            scanned={'actual':{'main.o':['main.c'],'helper.o':['helper.c']},'findings':findings}
            with patch.object(pipeline,'snapshot',side_effect=[base,target]), \
                 patch.object(pipeline,'full',side_effect=fake_full), \
                 patch.object(pipeline,'scan',return_value=scanned):
                result=pipeline.execute({'mode':'e11-a','repo':str(repo),'base':base,'target':target},
                                        Path(output)/'e11-a','job-test','trace-test')
            self.assertEqual(result['status'],'SUCCEEDED',result.get('error'))
            self.assertEqual([stage['name'] for stage in result['stages']],
                             ['full-check','incremental-check'])

    def test_queued_job_is_marked_failed_after_restart(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'jobs';store=server.Store(root)
            request={'mode':'e11-a','repo':str(pipeline.ROOT/'data/p'),'base':'a','target':'b'}
            with patch.object(server,'validate_request',return_value=request), patch.object(store.pool,'submit'):
                created=store.submit(request,'restart-key')
            store.pool.shutdown()
            restarted=server.Store(root)
            restored=restarted.get(created['job_id'])
            self.assertEqual(restored['status'],'FAILED')
            self.assertEqual(restored['error']['code'],'SERVER_RESTARTED')
            self.assertIsNotNone(restored['finished_at'])
            restarted.pool.shutdown()

if __name__=='__main__':unittest.main()
