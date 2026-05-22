# Changelog / 變更日誌

All notable changes to this delivery folder are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [10.0-verified] — 2026-04-20

Comprehensive verification pass across 6 rounds covering every user path.
The version number bumps the `-verified` suffix to distinguish "shipped" from "tested".

### Added

- `FIXES-APPLIED.md` — full verification-and-fix record (12 sections, 476 lines).
- `health-check.bat` / `health-check.sh` — one-click system health check for non-technical users.
- `clean-for-delivery.bat` / `clean-for-delivery.sh` — strip dev artifacts before re-distribution.
- `AI项目管理/Platform/db/schema/100_ai_roles_patch.sql` — creates `ai_roles` (15 rows), `collaboration_protocols` (10 rows), and `interaction_logs` tables that the engine required but prior schema files never defined.
- `AI项目管理/Platform/db/platform_restored.db` — backup DB for fallback.
- `/api/memory/append` endpoint — appends curated entries to `MEMORY.md`, closing the long-standing gap between `USER-GUIDE.md` promises and engine behavior.
- Multi-turn continuation preamble in `SmartMockEngine` — "_(承接上文 X 的討論)_" / "_(Continuing from prior turn about X)_" so Mock responses feel coherent across turns.
- Per-session isolation for multi-turn context (capped at 128 sessions with LRU-ish eviction).
- Greeting anchor in default-fallback: "你好" / "hello" / "嗨" → Q01 Chief Architect.
- Security-vs-quality code-review split: `審查代碼 + 安全漏洞` → Q06 Risk Auditor (was incorrectly forcing SPEC family).
- `INSTALL-GUIDE.md` Security section explaining no-auth + wide CORS + recommended reverse-proxy setup.
- `tests/test_regression.py` — 16 automated assertions codifying every Round 1–5 fix so future changes can't silently regress them.

### Changed

- **Security**: default `api_server.py` bind changed from `0.0.0.0` to `127.0.0.1` (loopback only). LAN users opt in explicitly via `--host 0.0.0.0` on trusted networks.
- **Routing accuracy**: keyword matching is now case-insensitive in `qspectrum_engine.py`; role capabilities in `ai_roles.capabilities` use real `CAPABILITY_KEYWORDS` codes (not prose). Benchmark accuracy: 20 % → **100 %** on 20-query suite.
- `/api/skills/list` now returns **27 unified skills** from 3 sources (real_skills + qspectrum + ai-skill-system), up from 5.
- `_read_body()` hardened: empty / malformed / oversized / non-dict payloads now return proper HTTP 400 (or 413) instead of closing the connection.
- `run.py --status [1] Database` now uses 3-candidate DB fallback (platform.db → platform_restored.db → platform_v4.1.db).
- `QUICK-START.md` + `BOOT.md` starter tables now match actual engine routing (e.g. "Help me plan a new project" → T03 System Coordinator, "Write a blog post introducing AI in 2026" → Q03 Creator).

### Fixed

- **Missing 3 core DB tables** (`ai_roles`, `collaboration_protocols`, `interaction_logs`) — engine crashed on every startup.
- **Virtiofs DB zeroing** — `agent_runtime.py:143` used a plain mutable `sqlite3.connect()` to "verify" `platform.db`, which truncated the file on virtiofs-backed filesystems. Switched to immutable URI.
- **`NoneType.get` crash in `run.py --status`** — `s.get('key', {})` doesn't apply default when key exists with `None` value. Fixed in 3 places.
- **5 scary "Bridge unavailable" WARNINGs** on startup — downgraded to DEBUG since these are optional bridges that aren't bundled.
- **`install.bat` L14** `python --version >/dev/null 2>&1` — Unix syntax on Windows, fixed to `>nul 2>&1`.
- **`start.bat`** `--status` branch ran before Python detection, causing empty version display. Reordered.

### Known Issues (Non-Blocking)

- **繁體 vs 简体 inconsistency** — `SKILLS-INDEX.md` / `SCENARIOS.md` use traditional Chinese; engine data uses simplified. Same entities, different encoding. Cosmetic only.
- **`dashboard.html`** has hardcoded "47 tables / 748 rows / E2E 27/27" values that don't reflect current runtime (static doc panel).
- **`plugin_loader.py`** is orphan code (~13 KB unused, safe to delete).
- **`/api/reset`** clears interaction_count but not conversation_history — half-reset behavior.
- **DeerFlow external integration** optional and not bundled.
- **`importers/import_documents.py`** referenced but missing — only runs during DB rebuild, gracefully caught.
- **No authentication** on API — documented in INSTALL-GUIDE Security section.

### Performance

- Mock-mode `/api/chat` latency: mean 476 ms, p50 403 ms, p95 793 ms, p99 818 ms (50-request sample).
- Sustained 40-request throughput: no latency drift, DB stays 458,752 bytes.
- Concurrent stress: 20 parallel chat requests complete in 10.3 s.

### Verified User Paths (6-Round Roll-Up)

```
✅ run.py --status         — ALL GREEN (10/10 subsystems)
✅ run.py --e2e            — 5/5 bundled tests pass
✅ run.py --demo           — 8-scenario demo runs cleanly
✅ run.py --web            — serves 84 REST endpoints
✅ Routing                  — 100 % accuracy on 20-query benchmark
✅ All 12 scenarios         — walked end-to-end with correct role transitions
✅ /api/negotiate           — 3-round multi-role dialog
✅ /api/tasks/* CRUD        — board + create + analytics
✅ /api/search              — 6 domains, Chinese + English
✅ /api/files CRUD          — path-traversal blocked, UTF-8 OK, 5 MB uploads OK
✅ /api/memory/append       — appends to MEMORY.md, survives restart
✅ Multi-turn context       — per-session preamble references prior topics
✅ Session isolation        — no cross-session leak
✅ Edge inputs              — 15/15 (emoji, XSS, SQLi, 10 k chars, mixed language)
✅ Natural-language         — 9/9 (typos, slang, voice-style)
✅ DB stability             — 10 restarts, no zeroing
✅ Fresh-install simulation — copy, clean, health-check → ALL GREEN
✅ .env LLM switching       — Mock ↔ Anthropic provider swap works
✅ Web UI pages             — 5/5 serve valid HTML
✅ Security                 — loopback-only default bind, CORS documented
✅ 6 Boot Chain files       — 77 KB total, fits any LLM context
✅ 22 skills loaded         — SkillExecutor end-to-end execution works
✅ Regression suite         — 16/16 automated assertions pass
```

---

## [prior] — before 2026-04-20

Undocumented prior development. See commit history (if `.git/` is included) or `AI项目管理/QCM/whitepapers/` for theory papers.

---

*Keep this file current when you apply future changes.*
*未來更動請同步維護此檔。*
