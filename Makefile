.PHONY: test single simulate verbose

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

single:
	PYTHONPATH=src python3 -m mascarade_sim single --players 6 --seed 1

verbose:
	PYTHONPATH=src python3 -m mascarade_sim single --players 6 --seed 1 --verbose

simulate:
	PYTHONPATH=src python3 -m mascarade_sim run --players 6 --games 100 --seed 42
