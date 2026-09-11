# Revenue analytics: check the metric before moving the budget

**A portfolio demonstration using simulated marketing and sales data.** [Dataset description](data/README.md).

## The decision

Which channel deserves further investigation before a marketing team reallocates spend?

I started by checking the denominators and the relationship between the two supplied files. The result is a bounded cost-per-lead comparison and a reconciliation issue to resolve before connecting marketing to sales outcomes.

![Recorded spend per lead by channel in simulated data. LinkedIn Ads 70.00, Google Ads 61.81, TikTok Ads 46.29, Facebook Ads 35.77, Email Marketing 2.14, Organic Search 0.00. Currency unspecified; zero recorded spend excludes unrecorded costs.](channel_cost_per_lead.png)

## What the sample supports

Across 108 channel-month rows, recorded spend totals **435,579.51** and recorded leads total **14,607**. Dividing the totals gives **29.82 currency units per lead**. Averaging each row's spend-per-lead ratio equally gives **36.57**, because a small row receives the same weight as a large one.

| Channel | Recorded spend | Recorded leads | Spend per lead |
|---|---:|---:|---:|
| LinkedIn Ads | 87,011.60 | 1,243 | 70.00 |
| Google Ads | 150,506.26 | 2,435 | 61.81 |
| TikTok Ads | 76,849.24 | 1,660 | 46.29 |
| Facebook Ads | 112,633.24 | 3,149 | 35.77 |
| Email Marketing | 8,579.17 | 4,006 | 2.14 |
| Organic Search | 0.00 | 2,114 | 0.00 |

Currency is not explicitly documented in the CSV. The ratio uses the supplied `Ad_Spend` and `Leads_Generated` fields without assuming a currency or that lead counts represent deduplicated people.

This is a lead-cost comparison. Email and organic leads may represent different audiences, intent and costs. Zero recorded organic ad spend does not mean content, labour or acquisition are free. Customer outcomes and attribution are needed before recommending a budget change.

## Three checks that change the interpretation

1. **Name the denominator.** The marketing file includes `Cost_Per_Acquisition`, but no acquired-customer count or definition of acquisition. I recomputed recorded spend per lead instead of presenting that field as customer acquisition cost. In 71 of 108 rows, the supplied value differs from recomputed spend per lead by more than 0.01. The generation method is undocumented, so I retain the source field and report the discrepancy.
2. **Reconcile totals before joining.** Marketing has one row per month and channel. Sales has one row per day, with no channel key. Aggregating both to month shows different lead totals in all 18 months. January 2023 contains 632 marketing leads and 5,457 sales leads. Different definitions or sample generation might explain this; the files do not. A raw month join would also repeat monthly spend for every matching day.
3. **Separate phase labels from evidence of impact.** The files have `Before` and `After` labels. Simulated observations cannot establish that a platform caused higher revenue, saved reporting hours or generated an ROI. Daily revenue also does not establish monthly recurring revenue without subscription and recognition definitions.

## Data and method

| File | Grain and coverage | Key limitations |
|---|---|---|
| [Marketing CSV](data/revenue_analytics_marketing_data.csv) | 108 rows, six channels across 18 months, January 2023 to June 2024 | No customer IDs, acquisition counts, attribution rules or documented currency |
| [Sales CSV](data/revenue_analytics_sales_data.csv) | 547 daily rows, January 1, 2023 to June 30, 2024 | No channel, lead/customer join key or documented conversion denominator |

The analysis uses Python's standard library and SQLite. Checks cover unique source grains, nonempty fields, nonnegative marketing spend and counts, rate ranges, daily date coverage, six channel rows per month, and agreement between channel aggregates and source totals. Structural checks pass; the semantic gaps above remain open.

For a real CRM integration, I would establish the lead/customer identity, source rule, reporting timezone, stage definition and acquisition event with the business owner. I would then deduplicate and reconcile source counts before calculating attribution or conversion. That integration is a proposed next step, not an implemented component of this demonstration.

## Reproduce or inspect

From this directory, with Python 3:

```sh
python run_analysis.py
```

No third-party packages are needed for the analysis. To regenerate the optional chart, install matplotlib and run `python run_analysis.py --chart`.

- [Runnable analysis and checks](run_analysis.py)
- [Channel aggregation SQL](channel_metrics.sql)
- [Calculated channel table](channel_metrics.csv)
- [Monthly lead reconciliation](monthly_reconciliation.csv)
- [Results, limitations and source file hashes](summary.json)
- [Browser-readable chart](channel_cost_per_lead.png)

## Scope

This example covers CSV analysis, SQL aggregation and reporting checks. It runs locally without live CRM connections. The [Power BI visualizations](visualizations/) explore the same simulated scenario; their ROI and business-impact figures are illustrative assumptions, not measured client outcomes.

## Discuss a reporting question

I work on marketing and CRM analytics, reporting and data quality. If your team needs to reconcile campaign and CRM numbers, [message me on LinkedIn](https://www.linkedin.com/in/kelvinwangechi/) with the decision you need the analysis to support.
