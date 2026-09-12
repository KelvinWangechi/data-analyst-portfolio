# What did “too expensive” actually mean?

[Explore the interactive case](https://kelvinwangechi.github.io/data-analyst-portfolio/project-showcases/customer-voice/)

A meal subscription should make someone's week easier. A price complaint could mean budget pressure, poor value, small portions or a box they cannot pause. This case follows open feedback into evidence-linked coding, R analysis and a decision worth testing.

## The decision

Among 152 written responses attached to “Too expensive,” 49 explicitly mention difficulty paying, 44 mention value for money and 36 mention delivery flexibility or pause control. These groups overlap. I would retain price as a hypothesis, investigate the pause experience for customers whose schedules change, and test a focused intervention only after confirming the friction.

The counts are descriptive. They do not establish a treatment effect or rule out unmentioned concerns. [Data, scope and assumptions](data/README.md) explain how to interpret them.

## What to inspect

- **Read a response:** select a theme and see the exact supporting words.
- **Change a coding decision:** exclude an issue locally and watch the count update; Reset restores the reference view.
- **Compare schedules:** inspect subgroup counts, denominators and Wilson intervals.
- **Try the language example:** a keyword baseline exposes how negation can reverse a meaning.
- **Inspect the AI contract:** model-neutral prompt, structured assignments and quote validation. The explorer uses saved coding, not a live model service.

## Reproduce

Python 3.12+, base R, and matplotlib for figure export. The executed R environment is recorded in `results/r-environment.txt`. There are no contributed R package dependencies. The browser needs no framework, analytics service or model API.

```sh
python generate_data.py
Rscript analysis.R
python -m pip install -r requirements.txt
python build.py
python -m unittest test_analysis.py
node test-browser-math.mjs
```

If desktop R is unavailable, Node 20.6+ can run the same script through webR 0.6.0:

```sh
npm ci --ignore-scripts
npm run analysis:r
```

The small Windows loader normalizes worker import paths; other platforms use the standard module resolution. No desktop installer is needed. [webR documentation](https://docs.r-wasm.org/webr/latest/downloading.html).

Serve this folder over HTTP to use browser module scripts, for example `python -m http.server 8000`, and open localhost:8000. `page.template.html` is the editable story; `build.py` embeds the validated data and default figures into `index.html`. Rebuild after changing any source data, analysis or narrative. Do not edit a generated number in the HTML to make a claim fit.

## Evidence map

| Claim or behaviour | Source |
|---|---|
| 152 price-related written responses; 49 affordability mentions | `results/r-summary.csv`, `results/sql-summary.json` |
| 36 comments mention pausing or delivery flexibility | Distinct response union in `analysis.R` and `generate_data.py` |
| Schedule comparison: 16/66 versus 2/86 for flexibility | `results/theme-summary.csv` |
| Unequal survey participation | `results/response-rates.csv` |
| Exact quoted evidence | `data/assignments.csv` joined to `data/responses.csv` |
| Browser mathematics and local exclusions | `test-browser-math.mjs` |
| R/SQL agreement and invalid-output rejection | `test_analysis.py`, `results/verification.json` |

The CSVs and schema preserve customer, response and weekly-order grain. `queries.sql` shows how to avoid multiplying survey rows through an order join. The full-width figure is available as [SVG](results/theme-prevalence.svg).

## Analytical boundaries

This release does not claim model accuracy, independent human adjudication, measured time savings or improved customer retention. Those require separate evidence. The implemented pipeline is useful because the original words, definitions, denominators and model-output checks are inspectable.
