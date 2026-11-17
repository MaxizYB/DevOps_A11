# A11 configuration probe

Derived from the course C/Make fixture. Maintained by A11 (241880439), with AI assistance.
C0 tests default configuration; C1 adds group-policy validation and boundary tests.
The target intentionally omits policy.h from helper.o prerequisites; unused.h is redundant.
These controlled defects are test inputs, not claims of a general production application.
Run: python3 test_project.py; make clean && make app && ./app. Expected output: 1.
