# Lab 17 - Point-in-Time Audit

Built with AI help. A learning demonstration, not investment advice.

## Question

Was each number in the series knowable on the day of the trading decision,
and may Project 2 use it?

## Run

From PowerShell:

```powershell
cd C:\Users\pmeix\FIN43900-Fall2026
.\.venv\Scripts\python.exe -m streamlit run asof_app.py
```

For a new environment, install `requirements-lab17.txt` with pip first.
The app needs no API key. [App](asof_app.py), [dependencies](requirements-lab17.txt),
[live validation script](validate_lab17.py), [executed results](Lab17-validation.json).
Run validation with `.\.venv\Scripts\python.exe validate_lab17.py`.

## Known answer: verified from live downloads on October 29, 2026

| Series | Last measurement known October 5 | Value |
|---|---|---:|
| BAA | September 2026 | 6.47 |
| FEDFUNDS | September 2026 | 3.75 |
| DGS10 | October 2, 2026 | 5.28 |
| MORTGAGE30US | October 1, 2026 | 7.28 |

All four passed. Monthly observations use the first of the month as their
measurement label, not their publication date.

PAYEMS at January 15, 2025 ends in December 2024 at **159,536** thousand persons.
Today's December 2024 value is **158,316**. There are **381** changed values
on shared dates across the full downloaded histories. The app shows this
December comparison explicitly, separate from today's latest payroll value.

Streamlit AppTest passed the four-series default, date change, PAYEMS addition,
and an invalid ID while retaining the four valid series. These are automated
checks, not a claim that the student completed the classroom exercises.

## Data card: DGS10

The student selected DGS10 for this audit on October 29, 2026.

| Field | Evidence |
|---|---|
| ID and source | [DGS10 on FRED](https://fred.stlouisfed.org/series/DGS10); Board of Governors of the Federal Reserve System, H.15 Selected Interest Rates |
| Historical source | [ALFRED September 30 vintage CSV](https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS10&vintage_date=2026-09-30) |
| Measure | Market yield on U.S. Treasury securities at 10-year constant maturity, quoted on an investment basis |
| Units and frequency | Percent per annum; daily; not seasonally adjusted. 4.99 means 4.99%, not 499% and not a daily investment return. |
| Publication lag | Short business-day lag in this audit: the September 30 vintage ends September 29. Do not equate the measurement date with publication time. |
| Release schedule | [H.15](https://www.federalreserve.gov/releases/h15/) is posted Monday-Friday at 4:15 p.m., excluding holidays or Board closures. The October 28 release includes October 27's observation. |
| Revisions | Zero changed shared dates between the September 30 vintage and the October 29 download. This observed result does not prove revisions are impossible. |
| Download date | October 29, 2026 |
| Missing values | A period or empty numeric cell is missing, never zero; no forward fill. |

ALFRED notes that updates are generally added within one business day of source
release. A date-level vintage does not establish what was available at an
intraday trading time. See [ALFRED help](https://alfred.stlouisfed.org/help).

### Why this rate relates to the Lab 15 universe

Proposed opener: the 10-year Treasury yield provides a long-term interest-rate
reference for BND's bond exposure and for discounting future cash flows in VTI
and SOXX. SGOV holds short Treasury bills, so DGS10 is an indirect context
variable rather than a direct measure of SGOV's yield. This is a rationale
for auditing the series, not evidence of predictive trading performance.

### Last month-end versus today

| As known on | Latest measured date | Value | Later current values | Revised shared dates |
|---|---|---:|---:|---:|
| September 30, 2026 | September 29, 2026 | 5.26 | 19 | 0 |
| October 29, 2026 | October 27, 2026 | 4.99 | 0 | 0 |

The 19 later observations were not present in the September 30 vintage.
This daily rate shows a short lag and no revisions in the tested comparison.

### Three source checks

The assistant compared the downloaded values with the observations displayed
on the linked FRED page; all three match:

| Measured date | CSV | FRED page |
|---|---:|---:|
| October 23, 2026 | 5.00 | 5.00 |
| October 26, 2026 | 5.00 | 5.00 |
| October 27, 2026 | 4.99 | 4.99 |

The student reported personally checking these three values on the FRED page
on October 29, 2026 and confirmed that all three matched.

## Explain the vintage function

1. `@st.cache_data(...)` caches results for one hour, using the function arguments
   as part of the cache key. Different IDs and vintage dates get separate results.
2. `download_asof(series_id, vintage_date, download_day)` receives the selected
   series, historical cutoff, and today's download date. The third argument
   prevents a prior day's cache entry being reused on a new day.
3. `parameters` includes the ID and the cutoff formatted as `YYYY-MM-DD`.
4. `urlencode(parameters)` safely constructs the query string for the ALFRED
   CSV endpoint. This is a historical request, not a cutoff applied to today's CSV.
5. `return read_csv(url)` downloads that vintage in one request and parses it.
   The helper handles missing values and ALFRED's date-suffixed column name,
   converts dates and numbers, and sorts the observations.

Practice question: why not download today's values and remove dates after the
cutoff? Answer: that would still retain revisions to earlier observations and
could include values measured before the cutoff but published afterward.

### Prepared code-explanation dialogue

**Me:** "This function gets the version of a series available on a historical
date. The first line, `@st.cache_data(ttl=3600, show_spinner=False)`, saves the
result for an hour and hides the loading spinner. Changing the series or date
uses a different cache entry."

**Me:** "The `def` line names the function `download_asof`. Its inputs are the
series ID, the vintage date we want, and the download day. The download day
is part of the cache key, so yesterday's cached result won't carry into today."

**Me:** "The triple-quoted line documents the function. It doesn't execute a
download. The `parameters` line creates a dictionary containing the series ID
and the vintage date; `isoformat()` formats the date as year-month-day."

**Me:** "The `url` line combines the ALFRED CSV address with those parameters.
`urlencode` formats them for the URL. For our example, that asks for DGS10
with a vintage date of September 30, 2026."

**Me:** "Finally, `return read_csv(url)` calls our helper to download and parse
that CSV, then returns the table to the app. The helper converts dates and
numbers, preserves missing values, and sorts observations by measurement date."

**Partner question:** "Why does this need ALFRED? Couldn't we just take the
FRED download and remove everything after September 30?"

**Me:** "That would filter measurement dates but keep today's revised values.
It could also keep a September measurement first published in October. The
ALFRED request asks for the version available on the selected date, which is
the information set we need for the historical decision."

## Partner attack: completed exchange (student-reported)

Field challenged: publication date. The student reported this actual exchange:

**Partner:** "You say DGS10 has a short publication lag, but how do you know
September 30's rate was available on September 30?"

**My response:** "Our app's September 30 ALFRED vintage ends with September
29's yield of 5.26%, so it does not establish that September 30's rate was
available that day. For Project 2, I'll use the prior-calendar-day ALFRED
vintage for each trading decision and quarantine the series if that vintage
cannot be verified."

Evidence: the September 30 DGS10 result in [executed validation](Lab17-validation.json).

## Proposed Project 2 call

**Admit conditionally:** use DGS10 as an interest-rate context variable only
from the ALFRED vintage dated before each trading decision day, using its last
nonmissing observation. Do not use today's history with a guessed fixed lag
and do not treat yield levels as fund returns. Quarantine the series for any
decision where the vintage cannot be obtained or verified; revise this call
if an audit shows timing discrepancies or revision handling failures.

## Learn and reflect

A data card records the source, definition, units, frequency, measurement time,
availability rules, revisions, and download date. Those fields make it possible
to decide whether a number belongs in a historical decision. Saying "cleaned
the data" only describes processing; it does not document what a value means
or when it became knowable.

DGS10 has a short observed lag and no changed shared values in our month-end
comparison. A backtest using today's history could nevertheless give itself
observations before they were published. That overstates its information set;
the effect on returns cannot be quantified from this audit alone.

## Remaining student checkout

- The prepared code-explanation dialogue is ready; completion of that separate
  partner exercise has not been reported.
- Submit the files through GitHub and Brightspace Lab 17.
