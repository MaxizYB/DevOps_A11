.PHONY: all doctor build test smoke scan lock shell

all:
	python3 scripts/e4/run.py all

doctor build test smoke scan:
	python3 scripts/e4/run.py $@

lock:
	uv pip compile requirements-dev.in --generate-hashes --python-version 3.13 -o requirements-dev.lock

shell:
	python3 scripts/e4/run.py shell
