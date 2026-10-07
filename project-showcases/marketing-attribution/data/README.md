# Data and measurement scope

**Provenance.** This analysis uses Fatima Habib Khan's [Kaggle attribution_data distribution](https://www.kaggle.com/datasets/fatimahabibkhan/attribution-data), version 1, listed as CC0: Public Domain. The archive's `attribution data.csv` is saved locally as `attribution_data.csv` without changing its bytes. The distribution does not document the original advertiser, collection method, whether records are generated or observed, or currency. It is used as a methodological case, without claiming a client result.

SHA256: `b17dde7505e6fb41b9fd21bdbb587adc425e53f8d9e1df0a6ccea78092df5ee4`

The source download script pins version 1 and verifies this checksum. The raw CSV is excluded from Git to keep the repository compact. Generated summaries and four traceable path examples are included.

## Fields and grain

| Field | Interpretation in this analysis |
|---|---|
| `cookie` | Recorded browser identifier; not a verified person or account |
| `time` | UTC event timestamp |
| `interaction` | `impression` or `conversion`; no click events are present |
| `conversion` | Binary observed conversion flag |
| `conversion_value` | Value recorded on conversion events, in unspecified units |
| `channel` | Channel recorded against the event, including conversion events |

There are 586,737 source rows spanning July 1-31, 2018, five channels, 240,108 cookies and 17,639 conversions. Each converting cookie has exactly one terminal conversion; no later events are recorded for it. Value totals 110,231 units. Non-converting events carry zero value. There are no missing fields.

## Record-quality decisions

- The main analysis removes 4,145 exact duplicate rows, leaving 582,592 events. None of the removed rows is a conversion. With no unique event ID, some duplicates could represent genuine repeated impressions; retaining them is a sensitivity specification.
- There are 609 cookie/timestamp groups with different channels at the same timestamp, involving 557 cookies and 120 conversions. Main ordering uses original file row order to break ties; a sensitivity specification excludes those cookies. That ordering is deterministic, not proof of the true sequence.
- The full-path definition contains every recorded event through conversion or last observation. Its first event is the first event visible in this extract, not necessarily customer acquisition. Every converted path has the conversion channel tag as its last event. These are event-touch models, not last-click models.
- The impressions-only specification removes the conversion event's channel label and attributes only to earlier recorded impressions. It leaves 7,417 conversions with no eligible exposure, so only 10,222 conversions receive credit. Changes combine a different event definition with a different population.
- Shorter windows are anchored to each cookie's conversion or last recorded event. They do not add follow-up after July 31. A later-starting cohort is a boundary diagnostic, not a causal control group.

## Limits on interpretation

Non-converting cookies may convert after the extract ends. Paths may start before July 1; cookie resets and cross-device behavior may split one person's journey. Offline touchpoints, organic/direct visits, targeting, creative, click events and exposure eligibility are absent. Shared intent can explain the association between channels and conversion. No costs, margins, campaign budgets or randomized exposure data are supplied, so neither incremental lift nor ROI, ROAS or a budget optimum can be estimated.

Bootstrap intervals quantify path-sampling variability under a fixed model and definition. They do not correct these coverage or causal limitations. [Model definitions and equations](../METHODS.md) explain the attribution assumptions.
