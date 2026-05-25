# Notebook Guide

The `notebooks/` directory now contains the main investigation workflows for the simulator:

- `strategy_comparison.ipynb`
  - Compares hard-cut and probabilistic order sorting across source classes and MKID energy resolution.
- `config_optimization.ipynb`
  - Sweeps `delta_x_m` and `n_steps` to build SNR optimization maps for three science cases.
- `worked_example.ipynb`
  - Walks through the end-to-end simulation chain for a representative source.
- `sitelle_sn3_benchmark.ipynb`
  - Sets up a SITELLE-like SN3 benchmark configuration for external ETC comparison.

Recommended workflow:

1. Start with `worked_example.ipynb` to understand the signal chain.
2. Use `strategy_comparison.ipynb` for the primary science trade study.
3. Use `config_optimization.ipynb` when choosing scan geometry for a target science case.
4. Use `sitelle_sn3_benchmark.ipynb` when comparing the simulator against a conventional filtered imaging FTS baseline.
