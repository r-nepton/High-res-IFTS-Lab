# Benchmarks

## SITELLE SN3-like baseline

Use `notebooks/sitelle_sn3_benchmark.ipynb` to build a conventional filtered imaging-FTS comparison case.

The benchmark emulates:

- SN3-like spectral window: 648-685 nm
- Step size: 2943 nm
- 350 steps
- 5 s exposure per step

The notebook prints simulator-side reference SNR values at 650.0 nm, 656.3 nm, and 672.0 nm so they can be compared manually with the public SITELLE ETC.

This benchmark is intentionally lightweight: the public SITELLE ETC is browser-driven, so the simulator repo stores the benchmark setup and reference outputs rather than an automated live query.
