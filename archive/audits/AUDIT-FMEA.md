# FMEA Audit Report

**15 GOOD, 0 PARTIAL, 0 GAP** out of 15 failure modes.

| # | Component | Failure mode | Impact | Mitigation | Verdict |
|---|---|---|---|---|---|
| ✅ | platform.db | file zeroed | engine tries to open empty DB | automatic fallback to platform_restored.db | GOOD |
| ✅ | routing_keywords.json | empty / corrupt | Secretary can't load routing rules | inline TRUM_KEYWORDS / SPEC_KEYWORDS defaults | GOOD |
| ✅ | MEMORY.md | read-only mount / permission denied | /api/memory/append can't write | HTTP 500 with permission error | GOOD |
| ✅ | port 8765 binding | port already in use | second start.bat / start.sh launch | friendly bilingual message + alternate-port hint | GOOD |
| ✅ | CLI args | invalid --provider value | user passes typo / unknown provider | validate against whitelist of 7 providers; exit 2 with hint | GOOD |
| ✅ | CLI args | out-of-range --port | user passes invalid port number | range-check 1-65535; exit 2 with error | GOOD |
| ✅ | /api/chat | empty body POST | user submits empty form | HTTP 400 'Empty message / 消息为空' | GOOD |
| ✅ | any POST endpoint | malformed JSON body | client sends invalid JSON | HTTP 400 'Invalid JSON body' | GOOD |
| ✅ | any POST endpoint | oversized payload (15MB) | malicious or misconfigured client | 10MB cap in _read_body → 413 or connection close | GOOD |
| ✅ | REST API | unknown /api/ path | client hits wrong URL | HTTP 404 | GOOD |
| ✅ | /api/files/read | path traversal attack | attacker accesses parent-dir files | PathGuard v3.1 blocks '..' patterns | GOOD |
| ✅ | DeerFlow | optional integration absent | user sees message at startup | reported as ⚠️ warning, system remains ALL GREEN | GOOD |
| ✅ | /api/memory/append | concurrent writers | multi-user race condition | 10 parallel writes all complete without corruption | GOOD |
| ✅ | /api/skills/execute | unknown skill name | user typo / stale skill reference | HTTP 200 with clean error body | GOOD |
| ✅ | /api/scenarios/sandbox | XSS payload as scenario_id | attacker injects via sandbox endpoint | whitelist-based rejection, HTTP 400 | GOOD |
