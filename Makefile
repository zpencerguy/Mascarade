.PHONY: test single simulate verbose experiment visualize

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

single:
	PYTHONPATH=src python3 -m mascarade_sim single --players 6 --seed 1

verbose:
	PYTHONPATH=src python3 -m mascarade_sim single --players 6 --seed 1 --verbose

simulate:
	PYTHONPATH=src python3 -m mascarade_sim run --players 6 --games 100 --seed 42

experiment:
	PYTHONPATH=src python3 -m mascarade_sim experiment --seats early_bluffer random random random --games 1000 --seed 42 --rotate-seats

visualize:
	PYTHONPATH=src python3 -m mascarade_sim visualize --players 4 --seed 42 --out visualizations/game_4p_seed42.html
