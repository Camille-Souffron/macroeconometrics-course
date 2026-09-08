# Interactive Macroeconometrics Lab

The Quarto book remains static. Only `interactive-lab.qmd` loads the small native-JavaScript interface. The first Run starts one module worker and pinned Pyodide 0.27.7. NumPy/SciPy/pandas, statsmodels, scikit-learn and autograd load by capability. Python modules and CSVs are cached in that worker; browser HTTP caching survives worker cancellation. A changed specification terminates CPU-bound work and rejects obsolete responses. No backend, API credentials, database or framework is required.

`catalog.json` registers experiments, typed controls, datasets, diagnostics, citations and implementation entry points. `data/metadata.json` documents snapshots; optional joins avoid duplicating macro data. `python/core.py` handles common transformations, sample selection, validation and JSON output. Each family exposes `estimate(frame, spec)`. The interface displays the current specification and downloads a self-contained script containing the same numerical modules. Python 3.12 and `requirements.txt` reproduce the browser package versions.

To add an experiment, implement and independently verify its numerical function, register its controls and provenance, add a chapter deep link, and update `coverage.json`. `inventory.json` preserves headings, methodological excerpts, citations and hashes from **all eleven chapters**. Any chapter edit makes the coverage gate fail until an explicit review and inventory refresh. This is a review gate, not a claim that keyword matching proves econometric correctness. `scope.json` records seven explicit qualifications and links to full desktop extensions. The same scope is visible to students.

Run from the repository root:

```sh
python -m pip install -r interactive/requirements.txt
python interactive/tools/check_coverage.py
OPENBLAS_NUM_THREADS=1 python -m pytest interactive/tests -q
quarto render
python interactive/tests/rendered.py
python -m playwright install --with-deps chromium
python -m http.server 8765 --directory _book
```

In another terminal, run `python interactive/tests/browser.py`. It uses actual Chromium/WebAssembly, checks chapter isolation, deep links, model families, cancellation, comparison, error states and narrow layouts. Optional `LAB_TEST_INTERCEPTED_TLS` and `LAB_TEST_STATSMODELS_WHEEL` support an inspecting corporate proxy; the latter accepts only the exact published wheel hash and never substitutes numerical results. Ordinary CI uses the CDN. Screenshots go to `/tmp`, not the repository.

`python interactive/tools/inventory.py` prints the updated inventory. Review differences before replacing `inventory.json`; do not automatically regenerate it in CI. Snapshot extraction in `tools/snapshots.py` is maintenance tooling, never a deployment dependency. Original retrieval dates missing from inherited course data are explicitly unknown; commit dates are not relabelled as retrieval dates.

Optional desktop routines in `python/advanced.py` use a separate environment (`requirements-advanced.txt`). Full TVP-SV has a time-varying triangular impact matrix and learned state scales, with optional outlier mixtures. Mixed-frequency DFM requires native-frequency data; climate quantiles require observed climate covariates. Pretrained Chronos inference requires an explicit model commit revision. The browser’s trained small Transformer is not a pretrained model.

The lab’s public-series macro subset excludes the inherited Moody’s spread because its source terms restrict redistribution. Original course CSVs are untouched and are not added to the published lab resources. `snapshots.py macro-policy` reproduces this exact subset without fetching or revising observations.

Two mathematical qualifications deserve attention. Conditional on **all** regression coefficients, a Jeffreys-covariance posterior has inverse-Wishart degrees of freedom equal to the usable observation count, not a residual-degrees-of-freedom correction; `bayesian.py` uses that conditional derivation. The existing Normal-diffuse discussion in the notes uses a different count, which is not silently copied into the sampler. Conjugate BVAR evidence conditions on empirical univariate scale estimates; comparisons require the same observations and prior convention. DIC/conditional WAIC and short single-chain summaries do not replace chronological predictive validation or convergence assessment.
