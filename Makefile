.PHONY: all doctor build test smoke scan lock shell clean

all:
	python3 scripts/e4/run.py all

doctor build test smoke scan:
	python3 scripts/e4/run.py $@

lock:
	python3 scripts/e4/run.py lock

shell:
	python3 scripts/e4/run.py shell

clean:
	python3 scripts/e4/run.py clean
