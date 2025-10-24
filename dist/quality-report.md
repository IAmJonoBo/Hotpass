# Hotpass Quality Report

## Quality Metrics

| Metric | Value |
| --- | ---: |
| Total records | 653 |
| Invalid records | 0 |
| Expectations passed | Yes |
| Mean quality score | 0.26 |
| Min quality score | 0.00 |
| Max quality score | 1.00 |

## Source Breakdown

| Source | Records |
| --- | ---: |
| Contact Database | 426 |
| Reachout Database | 173 |
| SACAA Cleaned | 188 |

## Schema Validation Errors

None

## Expectation Failures

None

## Recommendations

- CRITICAL: Average data quality score is below 50%. Consider reviewing data sources and validation rules.
- Missing primary email in 74% of records. Consider enriching data from additional sources.
- Missing primary phone in 81% of records. Consider enriching data from additional sources.
- 96% of records have quality flags. Review flagged records to identify systematic issues.
- 423 records have quality score below 40%. Consider manual review or additional data sources for these records.

## Conflict Resolutions

| Field | Chosen Source | Value | Alternatives |
| --- | --- | --- | --- |
| organization_category | SACAA Cleaned | Flight School | 1 alternatives |
| organization_type | SACAA Cleaned | Active | 1 alternatives |
| contact_primary_email | SACAA Cleaned | eloize@360aviation.co.za | 3 alternatives |
| contact_secondary_emails | Reachout Database | andries@360aviation.co.za;tamryn@360aviation.co.za | 2 alternatives |
| contact_primary_name | SACAA Cleaned | Eloize (Director) | 4 alternatives |
| contact_primary_role | Reachout Database | Founder and Managing Director | 3 alternatives |
| organization_category | SACAA Cleaned | Flight School | 1 alternatives |
| organization_type | SACAA Cleaned | Active | 1 alternatives |
| contact_primary_email | SACAA Cleaned | info@4aviators.com | 2 alternatives |
| contact_secondary_emails | Reachout Database | gerhard@4aviators.com;info@4aviators.com. | 1 alternatives |
| ... | ... | ... | 151 more conflicts |

## Performance Metrics

| Metric | Value |
| --- | ---: |
| Load seconds | 0.7602 |
| Aggregation seconds | 0.6004 |
| Expectations seconds | 0.0049 |
| Write seconds | 0.9876 |
| Total seconds | 2.4065 |
| Rows per second | 271.3503 |
| Load rows per second | 1035.3131 |

### Source Load Durations

| Loader | Seconds |
| --- | ---: |
| load_contact_database | 0.4129 |
| load_reachout_database | 0.2994 |
| load_sacaa_cleaned | 0.0435 |
