import json, tempfile, unittest
from pathlib import Path
from lab import fixture,scan,patch,commit

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'sample';fixture(self.p)

    def test_independent_known_edges(self):
        r=scan(self.p)
        self.assertEqual(r['actual']['main.o'],['config.h','main.c'])
        self.assertEqual({(f['type'],f['dependency']) for f in r['findings']},{('MISSING','config.h'),('REDUNDANT','unused.h')})

    def test_unchanged_reuses_both_targets(self):
        r=scan(self.p,scan(self.p));self.assertEqual(r['reused'],['main.o','helper.o']);self.assertEqual(r['refreshed'],[])

    def test_include_added_invalidates_cache(self):
        old=scan(self.p)
        (self.p/'main.c').write_text('#include "extra.h"\n'+(self.p/'main.c').read_text());commit(self.p,'new include')
        r=scan(self.p,old)
        self.assertIn(['MISSING','main.o','extra.h'],r['added']);self.assertEqual(len(r['refreshed']),2)

    def test_patch_preserves_redundant_dependency(self):
        r=scan(self.p);diff,plan=patch(self.p,r)
        self.assertIn('+main.o: main.c unused.h config.h',diff)
        self.assertNotIn('-\tgcc',diff)
        self.assertNotIn('config.h',(self.p/'Makefile').read_text())

    def test_old_report_rejected(self):
        r=scan(self.p);r['commit']='0'*40
        with self.assertRaisesRegex(ValueError,'STALE_REPORT'):patch(self.p,r)

    def test_unsafe_dependency_rejected(self):
        r=scan(self.p);r['findings']=[{'type':'MISSING','target':'main.o','dependency':'../outside.h'}]
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):patch(self.p,r)

    def test_unsupported_configuration_rejected(self):
        (self.p/'Makefile').write_text((self.p/'Makefile').read_text().replace('-O0','-include unknown.h'))
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_FLAGS'):scan(self.p)


class Student231880027E8Tests(unittest.TestCase):
    def test_indirect_header_include_invalidates_history(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            old=scan(p)
            (p/'config.h').write_text('#include "extra.h"\n#define VALUE 1\n')
            commit(p,'student 231880027: indirect header include')
            incremental=scan(p,old)
            full=scan(p)
            expected_actual={'main.o':['config.h','extra.h','main.c'],'helper.o':['helper.c']}
            expected_declared={'main.o':['main.c','unused.h'],'helper.o':['helper.c']}
            expected_findings=[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'MISSING','target':'main.o','dependency':'extra.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
            for report in [incremental,full]:
                self.assertEqual(report['actual'],expected_actual)
                self.assertEqual(report['declared'],expected_declared)
                self.assertEqual(report['findings'],expected_findings)
            self.assertEqual(incremental['added'],[['MISSING','main.o','extra.h']])
            self.assertEqual(incremental['resolved'],[])
            self.assertEqual(incremental['reused'],[])
            self.assertEqual(incremental['refreshed'],['main.o','helper.o'])


class Student231880027E9Tests(unittest.TestCase):
    def test_macro_flag_toggle_invalidates_both_directions(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            f=p/'main.c'
            f.write_text('#ifdef MODE\n#include "extra.h"\n#endif\n'+f.read_text())
            commit(p,'student 231880027: conditional include baseline')
            baseline=scan(p)
            base_actual={'main.o':['config.h','main.c'],'helper.o':['helper.c']}
            declared={'main.o':['main.c','unused.h'],'helper.o':['helper.c']}
            base_findings=[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
            self.assertEqual(baseline['actual'],base_actual)
            self.assertEqual(baseline['declared'],declared)
            self.assertEqual(baseline['findings'],base_findings)
            previous=baseline
            for flags,actual,findings,added,resolved in [
                ('-O0 -DMODE=1',{'main.o':['config.h','extra.h','main.c'],'helper.o':['helper.c']},
                 [base_findings[0],{'type':'MISSING','target':'main.o','dependency':'extra.h'},base_findings[1]],
                 [['MISSING','main.o','extra.h']],[]),
                ('-O0',base_actual,base_findings,[],[['MISSING','main.o','extra.h']])]:
                with self.subTest(flags=flags):
                    makefile=p/'Makefile'
                    text=makefile.read_text()
                    makefile.write_text(text.replace('CFLAGS = '+previous['key']['flags'],'CFLAGS = '+flags))
                    commit(p,'student 231880027: flags '+flags)
                    incremental=scan(p,previous)
                    full=scan(p)
                    for report in [incremental,full]:
                        self.assertEqual(report['actual'],actual)
                        self.assertEqual(report['declared'],declared)
                        self.assertEqual(report['findings'],findings)
                    self.assertEqual(incremental['key']['flags'],flags)
                    self.assertNotEqual(incremental['key'],previous['key'])
                    for identity in ['directives','recipes','compiler']:
                        self.assertEqual(incremental['key'][identity],baseline['key'][identity])
                    self.assertEqual(incremental['refreshed'],['main.o','helper.o'])
                    self.assertEqual(incremental['reused'],[])
                    self.assertEqual(incremental['added'],added)
                    self.assertEqual(incremental['resolved'],resolved)
                    previous=incremental


class Student231880027E10Tests(unittest.TestCase):
    def test_removing_transitive_include_resolves_only_leaf_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            (p/'config.h').write_text('#include "extra.h"\n#define VALUE 1\n')
            (p/'extra.h').write_text('#include "leaf.h"\n#define EXTRA 0\n')
            (p/'leaf.h').write_text('#define LEAF 7\n')
            commit(p,'student 231880027: transitive include baseline')
            old=scan(p)
            declared={'main.o':['main.c','unused.h'],'helper.o':['helper.c']}
            findings=[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'MISSING','target':'main.o','dependency':'extra.h'},
                {'type':'MISSING','target':'main.o','dependency':'leaf.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
            self.assertEqual(old['actual'],{'main.o':['config.h','extra.h','leaf.h','main.c'],'helper.o':['helper.c']})
            self.assertEqual(old['declared'],declared)
            self.assertEqual(old['findings'],findings)
            (p/'extra.h').write_text('#define EXTRA 0\n')
            commit(p,'student 231880027: remove transitive leaf include')
            incremental=scan(p,old)
            full=scan(p)
            for report in [incremental,full]:
                self.assertEqual(report['actual'],{'main.o':['config.h','extra.h','main.c'],'helper.o':['helper.c']})
                self.assertEqual(report['declared'],declared)
                self.assertEqual(report['findings'],[findings[0],findings[1],findings[3]])
            self.assertTrue((p/'leaf.h').is_file())
            self.assertEqual(incremental['added'],[])
            self.assertEqual(incremental['resolved'],[['MISSING','main.o','leaf.h']])
            self.assertEqual(incremental['refreshed'],['main.o','helper.o'])
            self.assertEqual(incremental['reused'],[])

if __name__=='__main__':unittest.main()
