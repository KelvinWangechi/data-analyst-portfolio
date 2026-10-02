# Schooling histories in Kenya’s refugee-hosting communities

**Status: research protocol and tested analysis scaffold; household data access pending. No new survey estimates have been calculated.**

## Policy question
Among children aged 6–17 in the K-LSRH Wave 1 survey, how do the out-of-school components with no previous attendance and with previous attendance differ between refugee and host samples within supported locations?

An overall rate cannot show whether exclusion reflects non-entry, interruption, or a mixture. This project specifies an auditable descriptive comparison. It cannot establish causes or evaluate later policies.

## What is here
- [Research protocol](docs/protocol.md): population, classification, denominators, geographic comparisons and missingness.
- [Evidence review](docs/evidence_review.md): primary sources read, overlap with the original report and unresolved evidence.
- [Analysis code](scripts/analyze.py): validates inputs and produces private review aggregates, denominator reconciliation, missingness bounds and component gaps.
- [Quality status](docs/qa.md): tests run and gates still open.
- [Results contract](outputs/estimates_schema.csv): headers only; deliberately no demonstration estimates.
- [Data access instructions](raw/README.md): obtain the roster through the official catalog.

The accompanying Word working paper is a separate private practice artifact. This public directory excludes the supplied personal/application brief and restricted microdata.

## Run after approved data access
Use Python 3.12 in an isolated environment. From this directory:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
cp validation.example.json validation.json
# Read the release labels, terms, questionnaire and indicator construction.
# Complete validation.json with actual evidence and sample-status code labels.
python scripts/analyze.py --data raw/hhm.dta --validation validation.json --out outputs/private_run01
```

The validation template intentionally blocks empirical execution. Do not mark gates true just to run the program. The supplied out-of-school indicator's construction still needs producer documentation or a verified derivation. The code does not infer its construction from enrolment alone.

## Interpretation
The World Bank's original report already discusses never-attendance among non-enrolled primary-age children (2024, Figure 22). This project is a proposed focused extension using a common classified denominator and a fixed 6–17 age range, not a claim to have discovered the distinction. The report's published percentages are not substituted for the project's estimates.

## Reproducibility and privacy
Raw inputs are local only. The script retains special-code counts, hashes its input and records package versions. It refuses duplicate IDs, invalid eligible-child weights and inconsistent sample/location mappings. Its output remains private until classification, small-cell and disclosure reviews pass. The n < 30 flag is only a review trigger, not a confidentiality rule. No confidence intervals or significance claims are produced without a defensible design specification.

AI assisted with research notes, initial code and tests. Tests use artificial records only. The project owner must review the code and interpret actual outputs before describing this as completed empirical work.
