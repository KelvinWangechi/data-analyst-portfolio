# Cleaning Enquiry to Job Profit

A fictional cleaning owner sees $9,500 in completed jobs. Two jobs still have
missing costs. How much profit can the owner confidently report, and who needs
to follow up?

[Open the interactive case](https://kelvinwangechi.github.io/data-analyst-portfolio/project-showcases/cleaning-enquiry-job-profit/)

The Salesforce core connects validated enquiries, customer contacts and estimator
tasks to human quote approval, customer acceptance, jobs and verified owner reports.
Unique enquiry and accepted-quote keys prevent duplicate handoffs and jobs.

The public experience provides a separate browser simulation of the enquiry
journey, job completion date filters, a missing-cost what-if exercise and an owner
briefing generated from the same selected records. Browser actions do not write
to Salesforce. The reporting baseline is a saved, reconciled snapshot.

## Synthetic cohort

- 25 enquiry scenarios: 23 validated CRM enquiries and two rejected intake events.
- 15 won, six lost, two open: close rate 15 / (15 + 6) = 71.43%.
- Fictional enquiry dates: 5–7 October 2026; completed job dates: 6–11 October 2026.
- 15 jobs: 12 completed and three scheduled. Completed revenue: USD 9,500.
- Ten verified jobs: USD 8,000 revenue, 100 person-hours and USD 4,800 direct costs.
- Weighted direct margin: 40%, before overhead and tax. Revenue/person-hour: USD 80.
- JOB-011 lacks other direct cost; JOB-012 lacks material cost. Unknown costs
  remain absent from verified profit metrics.

## Actual integration example

Authenticated Salesforce REST queries through MCP extracted the synthetic CRM,
job and rejected-event records. Captured responses were transformed into SQLite,
where verification status, direct costs and direct profit were independently
compared with the Salesforce formulas before producing the reporting snapshot.

`metrics.sql` contains the reporting model used in that reconciliation.
`verified-reporting.json` is the sanitized output, extracted on 11 October 2026
at 18:58:09 UTC. It contains no Salesforce record IDs or customer contacts.
Job-level direct costs and loaded hourly rates were added from the same captured
REST response to support the browser what-if calculation.

This is a Salesforce integration example, not Workiz. Refresh was on demand;
the page has no live Salesforce connection, scheduled sync or outbound Slack delivery.
Historical approvals are synthetic fixture values, not evidence of a live review.

## Run locally

From this directory, run `python -m http.server 8000` and open
`http://localhost:8000/`. Serve the directory over HTTP so the JSON fetch works.
