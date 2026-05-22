-- =====================================================================
-- Q-SpecTrum Platform DB Patch: ai_roles + collaboration_protocols
-- ---------------------------------------------------------------------
-- Restores 3 tables that engine code requires but earlier schema files
-- never defined (ai_roles, collaboration_protocols, interaction_logs).
-- Data is sourced from ROLE-REGISTRY.md (15 roles, 3 families).
-- Applied AFTER setup_platform.py or 010-999 schema files.
-- =====================================================================

-- 15 AI roles (TRUM 4 + SPEC 3 + QCM 8)
CREATE TABLE IF NOT EXISTS ai_roles (
    role_code    TEXT PRIMARY KEY,
    role_name    TEXT NOT NULL,
    family       TEXT NOT NULL CHECK (family IN ('trum','spec','qcm')),
    priority     TEXT NOT NULL DEFAULT 'P2',
    capabilities TEXT NOT NULL DEFAULT '[]',     -- JSON array
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'active',
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Inter-role collaboration protocols
CREATE TABLE IF NOT EXISTS collaboration_protocols (
    protocol_code  TEXT PRIMARY KEY,
    protocol_name  TEXT NOT NULL,
    source_role    TEXT NOT NULL,
    target_role    TEXT NOT NULL,
    trigger_event  TEXT NOT NULL,
    rules          TEXT NOT NULL DEFAULT '{}',   -- JSON
    payload_schema TEXT NOT NULL DEFAULT '{}',   -- JSON
    description    TEXT,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Interaction log used by protocol_executor.py
CREATE TABLE IF NOT EXISTS interaction_logs (
    id            TEXT PRIMARY KEY,
    timestamp     TEXT NOT NULL,
    source_role   TEXT NOT NULL,
    target_role   TEXT NOT NULL,
    protocol_code TEXT,
    status        TEXT NOT NULL DEFAULT 'completed',
    payload       TEXT
);

-- ── Seed the 15 roles (data from ROLE-REGISTRY.md v3.2) ──
-- IMPORTANT: capabilities MUST use the exact codes defined in
-- CAPABILITY_KEYWORDS (qspectrum_engine.py). Role routing reads this JSON
-- list and looks up the codes there, so prose like "Writing" or "Design"
-- will NOT match and the role will get zero keyword score.
INSERT OR IGNORE INTO ai_roles (role_code, role_name, family, priority, capabilities, description) VALUES
  ('ROLE-T01','Platform Sovereign','trum','P0',
   '["platform_governance","policy_decisions","emergency_override","system_audit","value_judgment"]',
   '平台主權者 - platform governance, policy decisions, emergency override, system audit'),
  ('ROLE-T02','Operations Director','trum','P0',
   '["content_sedimentation","operation_promotion"]',
   '運營總監 - content ops, demand management, knowledge assetization, promotion'),
  ('ROLE-T03','System Coordinator','trum','P0',
   '["skill_planning","system_coordination","cross_project_reuse"]',
   '體系協調官 - skill planning, system coordination, cross-project reuse'),
  ('ROLE-T04','Evolution Engineer','trum','P0',
   '["evolution_planning","tech_roadmap","upgrade_strategy","architecture_evolution"]',
   '演化工程師 - system evolution, technology roadmap, upgrade strategy'),

  ('ROLE-S01','Spec Chief Architect / DBA','spec','P1',
   '["db_architecture","system_architecture","path_design","schema_governance","template_maintenance","best_practice_review"]',
   '首席架構師/DBA - system architecture governance, path design, DB schema, mother template maintenance'),
  ('ROLE-S02','Spec Operations Officer','spec','P1',
   '["config_consistency","deployment_verification","ops_standardization","compliance_audit","compliance_check","path_audit"]',
   '運維官 - config consistency, deployment verification, ops standardization, compliance audit'),
  ('ROLE-S03','Spec-QCM Bridge Coordinator','spec','P1',
   '["cross_family_bridge","spec_qcm_sync","standard_alignment","protocol_mediation","qcm_bridge_sync","information_fusion"]',
   '橋接協調官 - cross-family bridge, Spec-QCM sync, standard alignment'),

  ('ROLE-Q01','QCM Chief Architect','qcm','P2',
   '["system_design","tech_selection","architecture_review","context_routing"]',
   '首席架構師 - system design, tech selection, architecture review, general entry (default)'),
  ('ROLE-Q02','QCM Researcher','qcm','P2',
   '["knowledge_retrieval","literature_analysis","information_fusion"]',
   '研究員 - deep research, literature analysis, competitor intel'),
  ('ROLE-Q03','QCM Creator','qcm','P2',
   '["content_generation","creative_output","document_writing","prompt_engineering"]',
   '內容創作者 - writing, design, content generation, creative output'),
  ('ROLE-Q04','QCM Analyst','qcm','P2',
   '["data_insight","trend_analysis","kpi_tracking","flywheel_monitoring"]',
   '數據分析師 - data insights, trend analysis, pattern recognition'),
  ('ROLE-Q05','QCM UX Lead','qcm','P2',
   '["ux_optimization","interface_design","design_consistency","user_growth_guidance"]',
   'UX設計師 - UX optimization, interface design, S1-S5 growth guidance'),
  ('ROLE-Q06','QCM Risk Auditor','qcm','P2',
   '["threat_detection","security_assessment","risk_scoring","quality_gate","quality_acceptance","sandbox_verification"]',
   '風險審計員 - threat detection, security assessment, compliance check'),
  ('ROLE-Q07','QCM AI Companion','qcm','P2',
   '["emotional_support","empathic_interaction","user_companionship"]',
   '情感伙伴 - emotional support, empathic interaction, user companionship'),
  ('ROLE-Q08','AI Companion+','qcm','P2',
   '["growth_coaching","personalized_guidance","learning_paths","emotional_intelligence","s1_s5_progression","motivation_coaching"]',
   'AI伙伴+ - growth coaching, personalized guidance, learning path management');

-- ── Seed 10 collaboration protocols (reasonable default topology) ──
INSERT OR IGNORE INTO collaboration_protocols
  (protocol_code, protocol_name, source_role, target_role, trigger_event, rules, description) VALUES
  ('PROTO-001','QCM to Spec Architecture Review','ROLE-Q01','ROLE-S01','architecture_change',
   '{"review_required":true,"timeout_sec":3600}','QCM proposes architecture change, Spec reviews for compliance'),
  ('PROTO-002','Spec to Trum Platform Decision','ROLE-S01','ROLE-T01','platform_impact',
   '{"approval_required":true,"severity":"high"}','Spec escalates platform-level decisions to Trum'),
  ('PROTO-003','Trum Emergency Override','ROLE-T01','ROLE-S01','security_event',
   '{"immediate":true,"bypass_review":true}','Platform Sovereign can override Spec for security events'),
  ('PROTO-004','Research Handoff to Creator','ROLE-Q02','ROLE-Q03','research_complete',
   '{"include_sources":true}','Researcher hands deliverables to Creator for content production'),
  ('PROTO-005','Risk Audit Trigger','ROLE-Q06','ROLE-S02','risk_detected',
   '{"severity_threshold":"medium"}','Risk Auditor flags ops issues for Operations Officer'),
  ('PROTO-006','Analyst to Trum Report','ROLE-Q04','ROLE-T02','analysis_complete',
   '{"scheduled":"weekly"}','Analyst delivers insights to Operations Director'),
  ('PROTO-007','Bridge Cross-Family Sync','ROLE-S03','ROLE-Q01','standard_drift',
   '{"auto_align":true}','Bridge Coordinator syncs Spec standards with QCM execution'),
  ('PROTO-008','UX to Creator Design Spec','ROLE-Q05','ROLE-Q03','design_spec_ready',
   '{"format":"figma+md"}','UX Lead hands design spec to Creator for implementation'),
  ('PROTO-009','Companion to Companion+ Escalation','ROLE-Q07','ROLE-Q08','growth_readiness',
   '{"readiness_score_min":0.7}','Basic companion escalates to growth coaching when user is ready'),
  ('PROTO-010','Evolution to System Coordinator','ROLE-T04','ROLE-T03','roadmap_update',
   '{"quarterly":true}','Evolution Engineer notifies System Coordinator of roadmap changes');
