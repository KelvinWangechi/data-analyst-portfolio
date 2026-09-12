# Data and research design

## Provenance

This is an original, reproducible meal-subscription scenario generated with seed 4817. Customer records, survey responses and orders are synthetic; feedback wording and reference theme assignments are authored. There is no client engagement, independent human-labelled validation set or measured business improvement behind these figures. The dataset demonstrates a research workflow, and its distributions reflect the generator's assumptions. The kitchen artwork is an original generated illustration. Source hashes are recorded in `manifest.json`.

## The question

When customers select “Too expensive,” what additional information do their words provide about what to investigate? Compare explicit budget pressure with value, portions, delivery, pausing and billing. Absence of a theme is not evidence that the customer does not experience it. Several themes can appear in a single response.

## Instrument

The question order is defined by `open-first-1`:

1. Open feedback: “Think about the last time you used the service. What worked well, and what got in your way?” Optional, before suggested reasons.
2. Structured reason: “Which of these best describes your main concern?” Too expensive / Does not fit my week / Service issue / Other. The coarse categories are intentionally examined for information loss.
3. Satisfaction: a five-point item about the most recent experience. It is retained in the schema but is not used to support the published decision.

One record per responding customer. Do not imply the instrument has been field-tested. For deployment with actual respondents, obtain permission to analyse linked records and separate permission to quote, redact identifiers before inference, and record question versions. The scenario contains no personal contact data.

## Grain and coverage

| File | Grain | Records |
|---|---|---:|
| customers.csv | Customer | 1,200 |
| invitations.csv | One invitation per sampled customer | 500 |
| responses.csv | One structured response per responding customer | 303 |
| assignments.csv | One theme and sentiment per response-theme pair | See file |
| orders.csv | Customer-week across 12 relative weeks | 14,400 |

Of the 303 responses, 280 include open text. The main comparison is restricted to the 152 non-empty responses whose selected reason is “Too expensive.” Blank text is missing feedback, not neutral sentiment. The remaining invited customers did not respond. Relative week numbers carry the order chronology.

## Generation assumptions

`generate_data.py` fixes all probabilities before sampling. Approximately 40% of customers have changing schedules. Invitation response probability is set to 0.62 for that group and 0.48 for regular schedules. The realised counts differ from those probabilities: 140/201 and 163/299. Topic weights also differ by schedule. This deliberately exposes response-selection and subgroup-denominator issues; it is not an estimate of a real customer population.

A primary issue is drawn from ten themes; 30% of responses add another issue. Some include a positive food-quality phrase. Feedback can be blank. The structured answer is a lossy mapping from the primary issue, with mappings declared in code. Repeated wording is expected; this is not a corpus for testing generalisation to natural customer language. Do not split repeated phrases across train and test and report the result as independent accuracy.

Weekly orders provide a separate grain for join demonstrations. Order status is not caused by a tested intervention. No retention model or causal effect is estimated.

## Coding and model boundary

The codebook distinguishes affordability from value and preserves sentiment. Published charts count negative assignments only. Reference assignments record exact source quotes. No human review is claimed. The live explorer can exclude assignments locally, but cannot change the source files or reference headline figures.

`coding.py` provides a transparent keyword baseline and a validator for structured model output. `coding-prompt.md` supplies the model-neutral coding contract. A valid JSON object and a real quote can still contain a wrong interpretation. Model output requires semantic review; uncertain meanings should remain unresolved. This release uses saved reference assignments rather than an inference endpoint.

Before deploying an LLM coder, build an independently reviewed natural-language evaluation set, separate development from test material, split repeated/paraphrased records together, and report per-theme precision/recall, abstention, invalid evidence, review time and cost. Do not interpret the present software tests as model-performance evidence.

## Statistics and interpretation

R computes distinct responding customers per negative theme, divided by all non-empty comments in the selected answer/schedule group. Each response contributes at most once to each theme; theme shares can sum above 100%. The displayed 95% Wilson intervals use z=1.959963984540054. They illustrate binomial sampling variation, not uncertainty from authoring, nonresponse or coding mistakes. Overlapping themes are correlated.

SQL independently reconciles the main counts. The browser computes the same quantities for exploration and matches R to numerical tolerance for every published segment. Positive mentions never enter the negative-issue counts. Orders must be aggregated to customer grain before joining to survey responses.

The finding supports which questions to investigate; it does not identify a best treatment or establish that a pause-flow change would improve retention. A real test needs an outcome definition, baseline rate, power calculation, assignment design and margin/support guardrails.

## Influences

Chris Chapman and Elea McDonnell Feit's [R for Marketing Research and Analytics](https://r-marketing.r-forge.r-project.org/) informed the research principles. Desirée De Leon and Hasse Walum's [Teacups, Giraffes, & Statistics](https://tinystats.github.io/teacups-giraffes-and-statistics/) informed the relationship between narrative and exploration. The scenario, text, code and illustration are original.
