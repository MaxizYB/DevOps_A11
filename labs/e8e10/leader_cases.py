"""Student 241880439 inputs and independent expected sets for E8--E10.

Expected answers come from the explicit fixture text, never from scan().
The personal evidence runner retains these same inputs for inspection.
"""
from lab import fixture


def oracle(main, helper, *, added=(), resolved=()):
    return {'actual': {'main.o': sorted(main), 'helper.o': sorted(helper)},
            'declared': {'main.o': ['main.c', 'unused.h'], 'helper.o': ['helper.c']},
            'reused': [], 'refreshed': ['main.o', 'helper.o'],
            'added': [list(item) for item in added],
            'resolved': [list(item) for item in resolved]}


def prepare(project, stage):
    fixture(project)
    if stage == 'e8':
        (project / 'config.h').write_text('#include "branch.h"\n#define VALUE 1\n')
        (project / 'branch.h').write_text('/* initially no transitive leaf */\n')
        (project / 'leaf.h').write_text('#define LEAF 0\n')
    elif stage == 'e9':
        source = project / 'main.c'
        source.write_text('#include "extra.h"\n' + source.read_text())
    elif stage == 'e10':
        (project / 'config.h').write_text(
            '#ifdef MODE\n#include "extra.h"\n#else\n#include "cold.h"\n#endif\n#define VALUE 1\n')
        (project / 'cold.h').write_text('#define COLD 0\n')
    else:
        raise ValueError('unknown personal stage: ' + stage)


def change(project, stage, *, restore=False):
    if stage == 'e8':
        (project / 'branch.h').write_text('#include "leaf.h"\n')
    elif stage == 'e9':
        source = project / 'main.c'
        source.write_text(source.read_text().replace('#include "extra.h"\n', ''))
        helper = project / 'helper.c'
        helper.write_text('#include "extra.h"\n' + helper.read_text())
    elif stage == 'e10':
        makefile = project / 'Makefile'
        old, new = ('-O0 -DMODE=1', '-O0') if restore else ('-O0', '-O0 -DMODE=1')
        makefile.write_text(makefile.read_text().replace('CFLAGS = ' + old + '\n', 'CFLAGS = ' + new + '\n'))
    else:
        raise ValueError('unknown personal stage: ' + stage)


def expected(stage, *, restore=False):
    rd = {'type': 'REDUNDANT', 'target': 'main.o', 'dependency': 'unused.h'}
    md_config = {'type': 'MISSING', 'target': 'main.o', 'dependency': 'config.h'}
    if stage == 'e8':
        result = oracle(['branch.h', 'config.h', 'leaf.h', 'main.c'], ['helper.c'],
                        added=[('MISSING', 'main.o', 'leaf.h')])
        result['findings'] = [md_config, rd,
            {'type': 'MISSING', 'target': 'main.o', 'dependency': 'branch.h'},
            {'type': 'MISSING', 'target': 'main.o', 'dependency': 'leaf.h'}]
    elif stage == 'e9':
        result = oracle(['config.h', 'main.c'], ['extra.h', 'helper.c'],
                        added=[('MISSING', 'helper.o', 'extra.h')],
                        resolved=[('MISSING', 'main.o', 'extra.h')])
        result['findings'] = [md_config, rd,
            {'type': 'MISSING', 'target': 'helper.o', 'dependency': 'extra.h'}]
    elif stage == 'e10':
        current, previous = ('cold.h', 'extra.h') if restore else ('extra.h', 'cold.h')
        result = oracle(['config.h', current, 'main.c'], ['helper.c'],
                        added=[('MISSING', 'main.o', current)],
                        resolved=[('MISSING', 'main.o', previous)])
        result['findings'] = [md_config, rd,
            {'type': 'MISSING', 'target': 'main.o', 'dependency': current}]
    else:
        raise ValueError('unknown personal stage: ' + stage)
    return result
