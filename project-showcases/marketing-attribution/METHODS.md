# Attribution definitions and verification

## Unit of analysis

The source is an event table. Events are sorted within cookie by timestamp and original CSV row number (header is row 1). The input audit verifies one terminal conversion per converting cookie. Each cookie contributes one path, with a conversion or a no-observed-conversion terminal. Model comparison uses conversion counts; value-weighted rule allocations are saved separately.

Main paths include the channel associated with the conversion event. Impressions-only paths remove that event and omit converting cookies with no remaining exposure. Missing exposure is explicitly reported rather than silently distributing its credit to other cookies.

## Rule-based allocations

For a converting path with n eligible events:

| Model | Event credit |
|---|---|
| First touch | 1 to the first recorded event |
| Last touch | 1 to the final recorded event |
| Linear | 1/n to each event |
| Position based | 0.4 each to the first and last, 0.2 divided among middle events; one event gets 1 and two get 0.5 each |
| Time decay | Weight proportional to 2^(-age in days / 7), normalized within path |

Sum event weights for each channel. Multiply by conversion value for the separate value allocation. Repeated channel appearances each receive event credit; `unique-channel-credit.csv` instead gives one equal vote to each distinct channel. These are analyst-defined rules, not a reproduction of a vendor's proprietary model.

## First-order Markov attribution

States: START, five channels, CONVERSION and NULL. Collapse consecutive appearances of the same channel but retain revisits after another channel. Add START and the observed terminal to each path. Count transitions on **all** converted and non-converted paths; normalize each row to form transition matrix P. CONVERSION and NULL are absorbing.

Let Q contain transitions among START and channels, and r contain transitions from those states into CONVERSION. Solve:

```text
b = (I - Q)^(-1) r
base conversion probability = b[START]
```

Implementation uses a linear solve, not an explicit matrix inverse. The main base probability reconciles to 17,639 / 240,108 = 7.3463%.

For channel c, redirect all incoming transition probability to NULL, set c's row to NULL, and solve again. Other retained probabilities are not renormalized. Define:

```text
removal_effect[c] = 1 - probability_without_c / base_probability
share[c] = removal_effect[c] / sum(removal_effect)
conversion_credit[c] = share[c] * observed_conversions
```

Removal effects overlap and need not sum to 1; only the normalized shares do. Facebook's 41.39% removal effect is a change inside this fitted transition model, not a prediction that removing its ads would lose 41.39% of actual conversions. The convention treats transitions into a removed channel as failed paths. A real customer may substitute another route. It also assumes the next transition depends only on the current state, losing richer history and timing.

No per-customer Markov credit is displayed in the path explorer. This implementation creates aggregate removal-based credit; assigning it to an individual path would require an additional definition. No revenue Markov result is inferred from count shares.

## Sensitivity and uncertainty

`model-comparison.csv` contains all six models for eight specifications: full path, 7-, 14- and 30-day lookbacks, duplicates retained, ambiguous timestamps excluded, impressions only, and first seen July 8 onward. `specifications.csv` contains each population and unassigned conversion count. Thirty days covers this entire source extract, so it is a useful identity check, not evidence of longer-window robustness.

The primary Markov intervals use 300 bootstrap resamples of complete cookies, seed 20261007. Identical collapsed path/outcome pairs are grouped and their frequencies resampled multinomially; this is equivalent to sampling cookie paths with replacement. The chain and removal effects are refitted each time. The 2.5th and 97.5th percentiles are pointwise intervals. They do not test the Instagram/Video difference or establish a causal ranking. Small sampling intervals can coexist with large specification changes.

## Reconciliation and tests

- Every rule conserves observed conversion count and value within its eligible population.
- Every Markov result conserves conversion credit after normalization; its base probability reconciles to the observed path conversion rate.
- The independent SQLite query in `queries.sql` uses window functions to derive first and last event credit, then compares it with Python. `sql-reconciliation.csv` records the differences.
- Unit fixtures cover short paths, repeated events, half-life decay, self-loops, non-converting paths, unobserved channels, no-conversion populations and reproducible bootstrap sampling.
- The browser explorer reads the same saved aggregates and precomputed path weights. It changes the displayed specification without fitting a new model in the browser.

## Method context

[Google's attribution overview](https://support.google.com/analytics/answer/10596866?hl=en) defines attribution as credit allocation across touchpoints. The event definitions and models here differ from GA4, which also has information and modelling not present in this file. [Tao et al., A Graphical Point Process Framework for Understanding Removal Effects in Multi-Touch Attribution](https://arxiv.org/abs/2302.06075) provides research context for removal-based scores; this project implements a simpler first-order chain, not that paper's point-process method.
