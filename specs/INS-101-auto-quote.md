# INS-101: Online auto insurance quote

**Type:** Story · **Epic:** Digital Quote & Bind · **Status:** Ready for Dev

## User story
As a prospective customer, I want an instant auto insurance quote online so that
I can see my annual premium without calling an agent.

## Rating rules
| Tier | Base premium | Coverage limit | Deductible |
|---|---|---|---|
| basic | $600 | $25,000 | $1,000 |
| standard | $900 | $50,000 | $500 |
| premium | $1,300 | $100,000 | $250 |

`annual_premium = (base + 2% of vehicle value) × age factor × (1 + 0.20 × prior accidents)`, rounded to cents.

- Age factor: under 25 → **1.5**; 25–64 → **1.0**; 65 and over → **1.2**.
- Minimum driver age is 18.
- More than 3 prior accidents cannot be quoted online.
- Quotes are valid for 30 days.

## Acceptance criteria
- **AC1** Given a 30-year-old driver, a $20,000 vehicle, 0 prior accidents and the standard tier,
  when they request a quote (`POST /quotes`), then the response is `201` with
  `annual_premium = 1300.00`, `coverage_limit = 50000`, `deductible = 500`, and
  `expires_on` 30 days from today.
- **AC2** Given a 22-year-old driver (otherwise as AC1), then `annual_premium = 1950.00`.
- **AC3** Given a 70-year-old driver (otherwise as AC1), then `annual_premium = 1560.00`.
- **AC4** Given 2 prior accidents (otherwise as AC1), then `annual_premium = 1820.00`.
- **AC5** Given a 17-year-old driver, then the response is `422` with error code `DRIVER_TOO_YOUNG`.
- **AC6** Given 4 prior accidents, then the response is `422` with error code `TOO_MANY_ACCIDENTS`.
- **AC7** Given an unknown tier such as `gold`, then the response is `422`.
- **AC8 (UI)** Given a customer on the quote page (`/`), when they enter age 30, vehicle value
  20000, 0 accidents, choose Standard and click **Get quote**, then they see the annual premium
  **$1,300.00** and tier **Standard**.
- **AC9 (UI)** Given a customer aged 17 on the quote page, when they click **Get quote**, then
  they see an error explaining drivers must be at least 18.
