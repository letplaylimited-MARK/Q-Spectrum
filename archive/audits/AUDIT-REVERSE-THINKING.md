# Reverse-Thinking Probe Audit (R17)

**6/6 probes survived** — targets gaps the existing 12 gates might miss.

| # | Probe | Result | Observation |
|---|---|:---:|---|
| P1 | query flood — 60× identical, deterministic routing | ✅ | 60/60 ok, 0 errs, 100% → ROLE-Q03, 33.5s |
| P2 | emoji-only input — no crash, graceful fallback | ✅ | 5/5 routed, crashed: [] |
| P3 | new-doc drift — semantic_consistency uses glob discovery | ✅ | uses rglob: True, hardcoded-only: False |
| P4 | silent sabotage — integrity gate catches <200B scripts | ✅ | sabotaged to 10B, gate exit=1, caught=True |
| P5 | 16th failure mode — state confusion on session re-use | ✅ | mismatches: 0 |
| P6 | canonical-number trap — all 15 roles are functionally live | ✅ | 15 rows, 0 hollow: [] |
