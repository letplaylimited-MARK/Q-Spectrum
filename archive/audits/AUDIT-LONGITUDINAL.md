# Longitudinal Drift Audit

**200 queries in one session** over 107.6s.

## Invariants

- DB size bounded: ✅ (458,752→458,752, Δ+0B)
- No essential role silenced: ✅ (silenced: set())
- No runaway dominance: ✅ (top: ROLE-Q01 @ 14.0%)
- Latency stable: ✅ (drift +3%)
- Crisis routing intact: ✅ (3/3)

## Role distribution

| Role | Count | % |
|---|---:|---:|
| ROLE-Q01 | 28 | 14.0% |
| ROLE-T03 | 24 | 12.0% |
| ROLE-Q03 | 22 | 11.0% |
| ROLE-S03 | 21 | 10.5% |
| ROLE-T01 | 15 | 7.5% |
| ROLE-T02 | 15 | 7.5% |
| ROLE-Q06 | 14 | 7.0% |
| ROLE-T04 | 10 | 5.0% |
| ROLE-Q08 | 10 | 5.0% |
| ROLE-Q04 | 9 | 4.5% |
| ROLE-S01 | 8 | 4.0% |
| ROLE-Q07 | 8 | 4.0% |
| ROLE-S02 | 7 | 3.5% |
| ROLE-Q02 | 6 | 3.0% |
| ROLE-Q05 | 3 | 1.5% |
