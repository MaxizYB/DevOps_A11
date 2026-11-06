import copy, csv, json, tempfile, unittest
from pathlib import Path
from lab import fixture,scan,patch,commit

class Student241880439Tests(unittest.TestCase):
    """Test explicit edge identity, target ownership and configuration changes."""

    def check_stage(self, stage, roundtrip=False):
        from leader_cases import change, expected, prepare
        from validation import compare_reports
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / 'sample'
            prepare(project, stage)
            commit(project, '241880439 independent ' + stage + ' baseline')
            old = scan(project)
            for restore in ([False, True] if roundtrip else [False]):
                change(project, stage, restore=restore)
                commit(project, '241880439 ' + stage + ' change restore=' + str(restore))
                inc, full = scan(project, old), scan(project)
                result = compare_reports(inc, full, expected(stage, restore=restore))
                self.assertTrue(result['passed'], result)
                old = inc

    def test_e8_nested_header_leaf_addition_refreshes_history(self):
        self.check_stage('e8')

    def test_e9_include_migration_changes_missing_target_identity(self):
        self.check_stage('e9')

    def test_e10_conditional_header_switch_and_restore_refresh_both_directions(self):
        self.check_stage('e10', roundtrip=True)


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

class Student241880411E8Tests(unittest.TestCase):
    def test_shared_transitive_header_changes_both_object_graphs(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            old=scan(p)
            baseline_actual={'main.o':['config.h','main.c'],'helper.o':['helper.c']}
            declared={'main.o':['main.c','unused.h'],'helper.o':['helper.c']}
            baseline_findings=[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
            self.assertEqual(old['actual'],baseline_actual)
            self.assertEqual(old['declared'],declared)
            self.assertEqual(old['findings'],baseline_findings)
            self.assertEqual(old['reused'],[])
            self.assertEqual(old['refreshed'],['main.o','helper.o'])
            self.assertEqual(old['added'],[
                ['MISSING','main.o','config.h'],
                ['REDUNDANT','main.o','unused.h']])
            self.assertEqual(old['resolved'],[])
            old_snapshot=copy.deepcopy(old)

            (p/'shared.h').write_text('#define SHARED 0\n')
            (p/'config.h').write_text('#include "shared.h"\n#define VALUE 1\n')
            (p/'helper.c').write_text('#include "config.h"\nint helper(void){return 0;}\n')
            commit(p,'student 241880411: shared transitive header')
            incremental=scan(p,old)
            full=scan(p)
            expected_actual={
                'main.o':['config.h','main.c','shared.h'],
                'helper.o':['config.h','helper.c','shared.h']}
            expected_findings=[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'MISSING','target':'main.o','dependency':'shared.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'},
                {'type':'MISSING','target':'helper.o','dependency':'config.h'},
                {'type':'MISSING','target':'helper.o','dependency':'shared.h'}]
            for report in [incremental,full]:
                self.assertEqual(report['actual'],expected_actual)
                self.assertEqual(report['declared'],declared)
                self.assertEqual(report['findings'],expected_findings)
            self.assertEqual(incremental['added'],[
                ['MISSING','helper.o','config.h'],
                ['MISSING','helper.o','shared.h'],
                ['MISSING','main.o','shared.h']])
            self.assertEqual(incremental['resolved'],[])
            self.assertEqual(incremental['reused'],[])
            self.assertEqual(incremental['refreshed'],['main.o','helper.o'])
            self.assertNotEqual(incremental['key'],old['key'])
            self.assertEqual(old,old_snapshot)


class Student241880411E9Tests(unittest.TestCase):
    def test_replacing_transitive_header_changes_edges_at_equal_finding_count(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            (p/'old.h').write_text('#define OLD 0\n')
            (p/'new.h').write_text('#define NEW 0\n')
            (p/'config.h').write_text('#include "old.h"\n#define VALUE 1\n')
            commit(p,'student 241880411: old transitive header baseline')
            old=scan(p)
            declared={'main.o':['main.c','unused.h'],'helper.o':['helper.c']}
            baseline_findings=[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'MISSING','target':'main.o','dependency':'old.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
            self.assertEqual(old['actual'],{
                'main.o':['config.h','main.c','old.h'],'helper.o':['helper.c']})
            self.assertEqual(old['declared'],declared)
            self.assertEqual(old['findings'],baseline_findings)
            self.assertEqual(old['reused'],[])
            self.assertEqual(old['refreshed'],['main.o','helper.o'])
            self.assertEqual(old['added'],[
                ['MISSING','main.o','config.h'],
                ['MISSING','main.o','old.h'],
                ['REDUNDANT','main.o','unused.h']])
            self.assertEqual(old['resolved'],[])

            (p/'config.h').write_text('#include "new.h"\n#define VALUE 1\n')
            commit(p,'student 241880411: replace indirect old header with new')
            incremental=scan(p,old)
            full=scan(p)
            expected_actual={
                'main.o':['config.h','main.c','new.h'],'helper.o':['helper.c']}
            expected_findings=[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'MISSING','target':'main.o','dependency':'new.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
            for report in [incremental,full]:
                self.assertEqual(report['actual'],expected_actual)
                self.assertEqual(report['declared'],declared)
                self.assertEqual(report['findings'],expected_findings)
            self.assertEqual(len(incremental['findings']),len(old['findings']))
            self.assertNotEqual(incremental['findings'],old['findings'])
            self.assertEqual(incremental['added'],[['MISSING','main.o','new.h']])
            self.assertEqual(incremental['resolved'],[['MISSING','main.o','old.h']])
            self.assertEqual(incremental['reused'],[])
            self.assertEqual(incremental['refreshed'],['main.o','helper.o'])
            self.assertEqual(set(incremental['key']['directives']),set(old['key']['directives']))
            for identity in ['recipes','flags','compiler']:
                self.assertEqual(incremental['key'][identity],old['key'][identity])
            self.assertTrue((p/'old.h').is_file())
            self.assertTrue((p/'new.h').is_file())


class Student241880411E10Tests(unittest.TestCase):
    def setUp(self):
        self.expected={
            'actual':{'main.o':['config.h','main.c'],'helper.o':['helper.c']},
            'declared':{'main.o':['main.c','unused.h'],'helper.o':['helper.c']},
            'findings':[
                {'type':'MISSING','target':'main.o','dependency':'config.h'},
                {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]}

    def compare(self,incremental,full,expected=None):
        from validation import compare_reports
        result=compare_reports(incremental,full,expected=expected)
        self.assertIsInstance(result,dict)
        for field in ['passed','checks','details']:
            self.assertIn(field,result)
        return result

    def corrupt(self,report,field):
        if field=='findings':
            report[field][0]['dependency']='wrong.h'
        else:
            report[field]['main.o'][0]='wrong.h'

    def test_equal_counts_with_wrong_graph_or_finding_are_rejected(self):
        for field in ['actual','declared','findings']:
            with self.subTest(field=field):
                incremental=copy.deepcopy(self.expected)
                full=copy.deepcopy(self.expected)
                self.corrupt(incremental,field)
                self.assertEqual(len(incremental[field]),len(full[field]))
                self.assertFalse(self.compare(incremental,full)['passed'])

    def test_agreeing_reports_must_still_match_independent_expected_sets(self):
        for field in ['actual','declared','findings']:
            with self.subTest(field=field):
                wrong=copy.deepcopy(self.expected)
                self.corrupt(wrong,field)
                self.assertFalse(self.compare(wrong,copy.deepcopy(wrong),self.expected)['passed'])

    def test_duplicate_findings_and_dependency_edges_are_rejected(self):
        for field in ['actual','declared','findings']:
            with self.subTest(field=field):
                repeated=copy.deepcopy(self.expected)
                if field=='findings':
                    repeated[field].append(copy.deepcopy(repeated[field][0]))
                else:
                    repeated[field]['main.o'].append(repeated[field]['main.o'][0])
                self.assertFalse(self.compare(repeated,copy.deepcopy(repeated))['passed'])

    def test_graph_and_finding_order_do_not_change_set_equality(self):
        reordered=copy.deepcopy(self.expected)
        for field in ['actual','declared']:
            reordered[field]={
                target:list(reversed(dependencies))
                for target,dependencies in reversed(list(reordered[field].items()))}
        reordered['findings'].reverse()
        self.assertTrue(self.compare(reordered,copy.deepcopy(self.expected),self.expected)['passed'])


class Student241880411EvidenceGateTests(unittest.TestCase):
    """Evidence identity checks use synthetic reports, never compiler runs."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name)
        self.rows=[]
        self.cases=['unchanged','body','include','declaration','flags','header']
        baseline_actual={'main.o':['config.h','main.c'],'helper.o':['helper.c']}
        baseline_declared={'main.o':['main.c','unused.h'],'helper.o':['helper.c']}
        baseline_findings=[
            {'type':'MISSING','target':'main.o','dependency':'config.h'},
            {'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
        base_key={
            'directives':{'main.c':['#include <stdio.h>','#include "config.h"'],
                          'helper.c':[],'config.h':['#define VALUE 1'],
                          'extra.h':['#define EXTRA 0'],'unused.h':[]},
            'recipes':['\tgcc $(CFLAGS) -c main.c -o main.o',
                       '\tgcc $(CFLAGS) -c helper.c -o helper.o'],
            'flags':'-O0','compiler':'synthetic GCC identity'}
        previous={
            'schema_version':'e8e10-1','profile':'GCC_LOCAL_HEADERS_EXPLICIT_MAKE',
            'actual':baseline_actual,'declared':baseline_declared,
            'findings':baseline_findings,'key':base_key,'commit':'1'*40,
            'reused':[],'refreshed':['main.o','helper.o'],
            'added':[['MISSING','main.o','config.h'],['REDUNDANT','main.o','unused.h']],
            'resolved':[],'elapsed_s':0.01}
        self.save('baseline.json',previous)
        for index,case in enumerate(self.cases):
            expanded=case in ['include','declaration','flags','header']
            repaired=case in ['declaration','flags','header']
            reused=case in ['unchanged','body','declaration']
            actual=copy.deepcopy(baseline_actual)
            declared=copy.deepcopy(baseline_declared)
            findings=copy.deepcopy(baseline_findings)
            if expanded:
                actual['main.o']=['config.h','extra.h','main.c']
                findings.insert(1,{'type':'MISSING','target':'main.o','dependency':'extra.h'})
            if repaired:
                declared['main.o']=['config.h','extra.h','main.c','unused.h']
                findings=[{'type':'REDUNDANT','target':'main.o','dependency':'unused.h'}]
            oracle={
                'actual':actual,'declared':declared,'findings':findings,
                'reused':['main.o','helper.o'] if reused else [],
                'refreshed':[] if reused else ['main.o','helper.o'],
                'added':[['MISSING','main.o','extra.h']] if case=='include' else [],
                'resolved':[['MISSING','main.o','config.h'],['MISSING','main.o','extra.h']]
                           if case=='declaration' else []}
            self.save(case+'-expected.json',oracle)
            self.save(case+'-baseline.json',previous)
            key=copy.deepcopy(base_key)
            if expanded:
                key['directives']['main.c'].insert(0,'#include "extra.h"')
            if case in ['flags','header']:
                key['flags']='-O1'
            if case=='header':
                key['directives']['config.h'].insert(0,'#include "extra.h"')
            current=str(index+1)*40
            for repeat in range(1,6):
                incremental=dict(copy.deepcopy(oracle),
                    schema_version='e8e10-1',profile='GCC_LOCAL_HEADERS_EXPLICIT_MAKE',
                    commit=current,key=copy.deepcopy(key),elapsed_s=repeat/100.0)
                full=copy.deepcopy(incremental)
                full.update(reused=[],refreshed=['main.o','helper.o'],
                    added=sorted([[finding['type'],finding['target'],finding['dependency']]
                                  for finding in findings]),
                    resolved=[],elapsed_s=repeat/50.0)
                inc_path=case+'-r'+str(repeat)+'-incremental.json'
                full_path=case+'-r'+str(repeat)+'-full.json'
                self.save(inc_path,incremental)
                self.save(full_path,full)
                self.rows.append({
                    'case':case,'repeat':repeat,'equal':True,'expected_match':True,'passed':True,
                    'incremental_s':incremental['elapsed_s'],'full_s':full['elapsed_s'],
                    'reused':len(incremental['reused']),'refreshed':len(incremental['refreshed']),
                    'baseline_commit':previous['commit'],'current_commit':current,
                    'incremental_json':inc_path,'full_json':full_path})
            self.save(case+'.json',incremental)
            previous=incremental

    def save(self,name,value):
        (self.out/name).write_text(json.dumps(value,indent=2)+'\n')

    def load(self,name):
        return json.loads((self.out/name).read_text())

    def gate(self,rows=None):
        from validation import matrix_gate
        rows=self.rows if rows is None else rows
        with (self.out/'results.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return matrix_gate(rows,self.out,{'passed':True})

    def test_complete_thirty_pair_fixture_passes_with_sixty_distinct_raw_reports(self):
        result=self.gate()
        self.assertTrue(result['passed'],result)
        self.assertEqual(result['rows'],30)
        self.assertEqual(result['raw_json_count'],60)

    def test_csv_commit_and_cache_counts_must_match_raw_reports(self):
        for field,wrong in [('current_commit','f'*40),('reused',999),('refreshed',999)]:
            with self.subTest(field=field):
                rows=copy.deepcopy(self.rows)
                rows[0][field]=wrong
                self.assertFalse(self.gate(rows)['passed'])

    def test_reusing_first_raw_pair_as_second_repeat_is_rejected(self):
        rows=copy.deepcopy(self.rows)
        for field in ['incremental_json','full_json','incremental_s','full_s']:
            rows[1][field]=rows[0][field]
        self.assertFalse(self.gate(rows)['passed'])

    def test_unrelated_baseline_commit_breaks_the_cumulative_history_chain(self):
        baseline=self.load('body-baseline.json')
        baseline['commit']='f'*40
        self.save('body-baseline.json',baseline)
        for row in self.rows:
            if row['case']=='body':
                row['baseline_commit']='f'*40
        self.assertFalse(self.gate()['passed'])

    def test_wrong_raw_reports_and_saved_oracle_cannot_override_fixed_case_oracle(self):
        paths=['include-expected.json','include.json','declaration-baseline.json']
        paths.extend('include-r'+str(repeat)+'-'+kind+'.json'
                     for repeat in range(1,6) for kind in ['incremental','full'])
        for path in paths:
            report=self.load(path)
            report['actual']['main.o']=[
                'wrong.h' if value=='extra.h' else value for value in report['actual']['main.o']]
            for finding in report['findings']:
                if finding['dependency']=='extra.h':
                    finding['dependency']='wrong.h'
            for finding in report.get('added',[]):
                if finding[2]=='extra.h':
                    finding[2]='wrong.h'
            self.save(path,report)
        self.assertFalse(self.gate()['passed'])

    def test_dynamic_projection_rejects_duplicate_edges_before_normalization(self):
        from validation import project_buildchecker
        directory=self.out/'dynamic'
        directory.mkdir()
        report={'status':'SUCCEEDED','build_exit_code':0,'clean_exit_code':0,
                'observed_targets':['main.o','helper.o'],'findings':[]}
        edges=[{'target':'main.o','dependency':'main.c','evidence':{'source':'synthetic'}},
               {'target':'helper.o','dependency':'helper.c','evidence':{'source':'synthetic'}}]
        (directory/'findings.json').write_text(json.dumps(report))
        for field in ['actual','declared']:
            with self.subTest(field=field):
                for name in ['actual','declared']:
                    graph=copy.deepcopy(edges)
                    if name==field:
                        duplicate=copy.deepcopy(edges[0])
                        duplicate['evidence']={'source':'a second observation of the same edge'}
                        graph.append(duplicate)
                    (directory/(name+'-graph.json')).write_text(json.dumps(graph))
                with self.assertRaisesRegex(ValueError,'duplicate'):
                    project_buildchecker(directory)


if __name__=='__main__':unittest.main()
