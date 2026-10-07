# Who deserves the conversion?

Instagram receives 12.7% of last-touch conversion credit and 17.1% under a first-order Markov model. That moves it ahead of Online Video. A 7-day lookback reverses that ordering again. The useful question is how much confidence a marketing team should place in that shift before changing spend.

[Read the interactive case](https://kelvinwangechi.github.io/data-analyst-portfolio/project-showcases/marketing-attribution/) · [Business case and analysis plan](PLAN.md) · [Data and scope](data/README.md) · [Model definitions](METHODS.md)

## Findings

- Facebook leads all six full-path models. That is a stable descriptive ranking, not evidence that its next unit of spend will earn the highest return.
- Instagram appears earlier without closing in 2,343 converting paths; its fitted network role differs from its closing share. Its third-place Markov ranking depends on the lookback window.
- 7,417 of 17,639 conversions (42.0%) have only the conversion event recorded. An impressions-only analysis can allocate credit to only 10,222 conversions. Different denominators must stay visible.
- No spend or causal comparison is available. The next decision is a measurement check and an incrementality test, with channel costs and net outcome value collected before a budget recommendation.

## Reproduce

Python 3.12 was used. From this folder:

```bash
python -m pip install -r requirements.txt
python scripts/download_data.py
python scripts/analyze.py
python -m unittest discover -s tests -v
python scripts/build_article.py
```

Serve the repository root with `python -m http.server 8765`, then open `/project-showcases/marketing-attribution/`. The article's default findings are present without JavaScript. The interactive path and model controls require JavaScript.

The download pins the documented Kaggle version and verifies its SHA256. If a future download returns different bytes, it stops rather than generating new numbers silently. An existing source file can be used if its checksum matches. Browser-only exploration does not need the raw file.

## Inspect the evidence

| Output | Purpose |
|---|---|
| [Model comparison](results/model-comparison.csv) | Six models across eight journey definitions, with count, share, rank and denominator |
| [Specifications](results/specifications.csv) | Eligible populations and unassigned conversions |
| [Quality audit](results/audit.json) | Input grain, duplicates, timestamp ambiguity and path coverage |
| [Channel roles](results/channel-roles.csv) | Opening, closing and earlier-without-closing appearances |
| [Markov intervals](results/markov-intervals.csv) | Removal effects and conditional bootstrap share intervals |
| [Transition matrix](results/transition-matrix.csv) | The fitted absorbing chain |
| [Value attribution](results/value-attribution.csv) | Separate rule-based value allocation in unspecified units |
| [SQL reconciliation](results/sql-reconciliation.csv) | Independent first-/last-touch checks |
| [Explorer data](results/explorer-data.json) | Saved aggregates and four observed examples with source CSV row references |

The code, figures and article form one reproducible project. Attribution allocates observed credit; an experiment must establish incremental effect.
