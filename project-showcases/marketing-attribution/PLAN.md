# Business case: when is attribution strong enough to change a decision?

A marketing lead needs to choose which channel to investigate in the next incrementality test. Last-touch reports offer a ranking, but a different rule or observation window could change that recommendation. The decision is a test priority, not an immediate budget allocation.

## Questions to answer

1. Which channels receive closing credit, and which appear earlier in converting journeys?
2. Do first-touch, last-touch, linear, position-based, time-decay and Markov models support the same channel ranking?
3. How much does the answer depend on duplicate records, timestamp ordering, repeated impressions, lookback length and including the conversion event's channel label?
4. What evidence is still missing before estimating incremental return or reallocating spend?

## Analysis protocol

- Validate the event grain and conversion/value fields. Audit missing fields, exact duplicates, time ties, observation boundaries and conversion placement.
- Remove exact duplicates in the main analysis, with a retained-duplicate sensitivity check. A duplicate could represent a real repeated exposure; the data has no event identifier to settle that question.
- Sort within cookie by UTC timestamp and original row order. Retain the conversion event's channel in the main specification. Examine impressions-only attribution separately, reporting conversions with no eligible impression.
- Use the recorded cookie path up to its first conversion; otherwise end at its final recorded event. This file has one terminal conversion per converting cookie. Non-converting paths mean no conversion observed in this extract, not proven eventual failure.
- Attribute one unit per observed conversion for count comparisons. Keep monetary-value attribution separate and use unspecified value units, because currency is undocumented.
- Fit a first-order absorbing Markov chain using converted and non-converted paths. Remove a channel by redirecting its incoming probability to the non-conversion terminal. Normalize removal effects to the observed conversion total. Do not interpret removal as a causal intervention.
- Compare full observed paths with 7-, 14- and 30-day lookbacks anchored to conversion or final observation. Examine timestamp ambiguity, collapsed repeats, omitted conversion labels and later-starting cookies.
- Bootstrap complete cookie paths for Markov share intervals. These describe sampling variability conditional on the model; they do not capture omitted touchpoints, censoring, identity fragmentation or confounding.
- Reconcile rule-based allocations to conversion totals and value totals. Independently verify event and first-/last-touch results in SQLite. Test model edge cases using small fixtures.

## Deliverables

- Reproducible Python analysis and source download instructions with a checksum.
- SQL reconciliation, quality audit, model comparison, sensitivity outputs and figures.
- An interactive article: trace an observed path, change the credit rule, inspect aggregate model disagreement and compare journey definitions.
- A proposed incrementality test with outcomes, guardrails and missing-data requirements.

## Decision criteria

Consistent descriptive rankings justify a candidate for investigation, not a spend increase. Reversed rankings require resolving the measurement definition first. No cost data means no channel ROI, ROAS, response curve or budget optimum. A recommendation must state what the file supports and what an experiment must establish.
