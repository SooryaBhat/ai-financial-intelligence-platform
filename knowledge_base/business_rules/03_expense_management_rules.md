---
document_id: BR-03
title: "Expense Management Rules"
author: "AI-assisted draft (Claude) for the ALLADIN project"
issuing_organization: "ALLADIN project (internal)"
publication_year: 2026
topic: expense_rules
content_type: AI_assisted_draft
review_status: unreviewed
license_reuse_status: "Internal, project-owned; AI-assisted"
applicable_region: general
---

# Business Rules 03: Expense Management (EXP-001 to EXP-007)

> Status: `proposed` / `configuration_dependent`; none validated. Fields **ASSUMED**. Conventions G-1…G-10 apply. Explanations: Guide 5. **High expenses must never be labelled wasteful or fraudulent automatically.**

## EXP-001 Expense Totals by Period and Category
| Field | Specification |
|---|---|
| Logic | FIN-003 grouped by `category` (and optional sub-category/vendor); share of total; uncategorised reported explicitly |
| Outcome | Table with totals, shares, counts |
| DQ | Uncategorised share > CONFIG (illustrative 10%) ⇒ flag `CATEGORISATION_WEAK` |
| Explanation | "Expenses were <X>; largest categories: <list>. <u>% are uncategorised." |
| Tests | 100 rent, 50 utilities, 50 uncategorised ⇒ shares 50/25/25 and flag. |
| Status | proposed |

## EXP-002 Expense Growth
| Logic | FIN-010 per category and total, normalised for period length; contextualised with revenue growth (SAL-003): produce the 2×2 reading (expenses vs revenue both rising/falling). Alert (CONFIG illustrative): category growth > +25% **and** change ≥ CONFIG minimum amount (illustrative 5% of total expenses). |
|---|---|
| Outcome | "Increase worth reviewing", with revenue context |
| Edge | Annual/irregular payments (annualised or flagged), new business lines, one-offs; prior base 0 ⇒ "new expense category" |
| Explanation | "<Category> rose <x>% to <A>, while revenue changed <y>%. Increases can be legitimate (e.g., growth, new supplier); check the underlying records." |
| Tests | Rent 100→130 with revenue +30% ⇒ informational; marketing 100→200 with revenue −5% ⇒ review. |
| Status | configuration_dependent |

## EXP-003 Budget Variance
FIN-015 applied per category. Overspend alert thresholds CONFIG (illustrative > 10% medium, > 25% high with minimum amount). Distinguish timing variance when payment schedule is known. No budget ⇒ `CANNOT_CALCULATE: no budget`. Explanation must say "over budget" not "wasteful".
| Tests | Actual 120 vs budget 100 ⇒ +20% medium; no budget ⇒ message. |
|---|---|
| Status | configuration_dependent |

## EXP-004 Unusually Large Expenses
| Field | Specification |
|---|---|
| Logic | Per category with ≥ CONFIG history (illustrative 12 observations): flag expense if `amount > Q3 + k×IQR` (k CONFIG, illustrative 3) **or** > CONFIG multiple of category median (illustrative 5×). Categories with fewer observations use only an absolute owner-set limit if configured, else no flag. |
| Outcome | "Larger than usual for this category: worth reviewing" |
| Edge | Capex, annual insurance, tax payments, deposits, one-time repairs, bulk stock purchases |
| Follow-up | Check invoice/supporting document, approval, correct category |
| Tests | Utilities typically 8–12, one record 90 ⇒ flag; 4 prior observations ⇒ no statistical flag. |
| Status | configuration_dependent |

## EXP-005 Repeated Expense Patterns
| Logic | Detect recurring payees/amounts (same vendor, amount within CONFIG tolerance, regular interval) to list **recurring commitments**; also flag possible **duplicates** (see ANO duplicate rule) and **missing expected recurring expense** (e.g., rent absent this month). |
|---|---|
| Outcome | Recurring list with estimated monthly commitment; "possible duplicate" or "expected item missing" as review prompts |
| Edge | Genuine repeated purchases; late entry rather than missing |
| Tests | Rent 40 each month ⇒ recurring; two identical 5,000 records same vendor same day ⇒ possible duplicate. |
| Status | configuration_dependent |

## EXP-006 Expense-to-Revenue Ratio
| Logic | `Expenses ÷ NetRevenue`, same period and basis; operating expense ratio uses operating expenses only. |
|---|---|
| Preconditions | Revenue > 0 and complete expense coverage; otherwise UNDEFINED/insufficient |
| Edge | Low-revenue months inflate ratio; seasonal businesses compare same season |
| Explanation | "Expenses were <r>% of revenue (<prior>% last period)." |
| Tests | 300/1000 ⇒ 30.0%; revenue 0 ⇒ UNDEFINED. |
| Status | configuration_dependent |

## EXP-007 Cost-Control Investigation Suggestions
| Logic | Based on EXP-001…006 outputs, propose investigation steps (not conclusions): verify records, compare with quotes/suppliers, check volume drivers, identify discretionary vs essential, review contracts. Suggestions follow REC structure. Must warn when a suggested saving could affect quality, safety, employees, or compliance. |
|---|---|
| Outcome | Ordered list of checks with evidence references |
| Prohibited wording | "waste", "fraud", "theft", "overspending by staff" |
| Tests | High utilities ⇒ suggestions: check meter/bill, usage change, tariff; no accusation. |
| Status | proposed |

## Schema items to reconcile
Category taxonomy, vendor field, expense status, recurring-expense flags, budgets, supporting-document links, capex flag.
