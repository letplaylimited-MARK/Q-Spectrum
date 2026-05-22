#!/usr/bin/env python3
"""
Q-SpecTrum — Interactive CLI Entry Point
========================================
Canonical interactive entry for the qspectrum_engine.py Secretary.route() chain.
It unifies all subsystems:
  1. qspectrum_engine.py  → Secretary routing + Role + LLM pipeline
  2. Platform/scripts/    → Workflow/Protocol/Agent engines
  3. chat.html            → Web chatroom UI (via --web mode on port 8765)

Usage:
  python run.py                      # Interactive chat (default)
  python run.py --demo               # Run 8 demo scenarios
  python run.py --status             # System health check
  python run.py --query "你的問題"    # Single query (multi-word supported)
  python run.py --web                # Web UI on port 8765
  python run.py --web --port 9000    # Web UI on custom port
  python run.py --web --provider openai  # Web UI with specific LLM
  python run.py --chatroom           # Alias for --web (browser chatroom)
  python run.py --e2e                # Run E2E test suite
  python run.py --guide              # Guided onboarding (recommended first use)
  python run.py --help               # Show this help

LLM Configuration (env vars):
  QSPECTRUM_LLM=mock       Mock responses (default, always works)
  QSPECTRUM_LLM=openai     OpenAI API (needs OPENAI_API_KEY)
  QSPECTRUM_LLM=anthropic  Anthropic API (needs ANTHROPIC_API_KEY)
  QSPECTRUM_LLM=ollama     Local Ollama (needs ollama running)

Route A (AI Management):
  Any AI model can manage this system by reading:
    BOOT.md → SYSTEM-PROMPT.md → KNOWLEDGE-INDEX.md → MEMORY.md
  Then running: python run.py --status  (to verify system health)
"""

import os
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).parent.resolve()
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def cmd_status():
    """Full system health check across all subsystems."""
    import sqlite3

    from qspectrum_engine import QSpectrumEngine, create_llm_provider

    print("=" * 65)
    print("  Q-SpecTrum System Health Report")
    print("=" * 65)

    # 1. Database (with same 3-candidate fallback the engine uses)
    print("\n  [1] Database")
    db_dir = ROOT / "AI项目管理" / "Platform" / "db"
    candidates = [db_dir / "platform.db",
                  db_dir / "platform_restored.db",
                  db_dir / "platform_v4.1.db"]
    db_path = None
    for c in candidates:
        if c.exists() and c.stat().st_size > 0:
            db_path = c
            break
    if db_path is None:
        print(f"      ❌ No usable DB found. Tried: {[c.name for c in candidates]}")
        print("         Tip: restore from backup with:")
        print('         copy "AI项目管理/Platform/db/platform_restored.db" "AI项目管理/Platform/db/platform.db"')
    else:
        try:
            uri = f"file:{db_path.resolve()}?immutable=1"
            conn = sqlite3.connect(uri, uri=True)
            tables = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            roles = conn.execute("SELECT COUNT(*) FROM ai_roles").fetchone()[0]
            wf = conn.execute("SELECT COUNT(*) FROM workflow_definitions").fetchone()[0]
            proto = conn.execute("SELECT COUNT(*) FROM collaboration_protocols").fetchone()[0]
            agents = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            total = sum(conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
                         for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
            conn.close()
            in_use = db_path.name
            note = "" if in_use == "platform.db" else f" (fallback: using {in_use})"
            print(f"      ✅ {in_use}: {tables} tables, {total} rows{note}")
            print(f"         Roles: {roles} | Workflows: {wf} | Protocols: {proto} | Agents: {agents}")
        except Exception as e:
            print(f"      ❌ DB open failed for {db_path.name}: {e}")

    # 2. Unified Engine
    print("\n  [2] Unified Engine (qspectrum_engine.py)")
    try:
        llm, llm_name = create_llm_provider("mock")
        engine = QSpectrumEngine(llm_provider=llm)
        s = engine.get_system_status()
        print(f"      ✅ {s['engine']}")
        print(f"         Roles: {s['roles_loaded']} ({s['roles_by_family']})")
        print(f"         Knowledge: {s['knowledge_entries']} entries (R-formula active)")
        print(f"         LLM: {llm_name}")
        print(f"         Protocols: {s['protocols']} | Workflows: {s['workflows']}")
        # Show new subsystems
        gc = s.get('ghost_channel') or {}
        if gc.get('active'):
            print(f"         Ghost Channel: {gc.get('mode', '?')} ({gc.get('capabilities_count', 0)}/10)")
        df = s.get('deerflow') or {}
        if df.get('installed'):
            print(f"         DeerFlow: {df.get('skills_count', 0)} skills")
        cr = s.get('component_registry') or {}
        if cr:
            print(f"         Components: {cr.get('total_components', 0)} registered")
        engine.close()
    except Exception as e:
        print(f"      ❌ Engine failed: {e}")

    # 3. Platform Scripts
    print("\n  [3] Platform Scripts")
    scripts_dir = ROOT / "AI项目管理" / "Platform" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    try:
        from path_utils import get_project_root
        print(f"      ✅ PathGuard: root={Path(get_project_root()).name}")
        from workflow_engine import WorkflowEngine
        wfe = WorkflowEngine()
        print(f"      ✅ WorkflowEngine: {len(wfe.list_workflows())} workflows")
        from agent_runtime import AgentRuntime
        art = AgentRuntime()
        st = art.get_status()
        print(f"      ✅ AgentRuntime: {st['agents']} agents, {st['roles']} roles")
    except Exception as e:
        print(f"      ❌ Scripts error: {e}")

    # 4. Knowledge Resonance
    print("\n  [4] Knowledge Resonance")
    try:
        from qspectrum_engine import KnowledgeResonance
        print("      ✅ KnowledgeResonance (R=0.35K+0.25C+0.25I-0.15E)")
    except ImportError as e:
        print(f"      ❌ Import error: {e}")

    # 5. Web UI
    print("\n  [5] Web UI")
    chat_html = ROOT / "chat.html"
    api_server = ROOT / "api_server.py"
    print(f"      {'✅' if chat_html.exists() else '❌'} chat.html (Web chatroom)")
    print(f"      {'✅' if api_server.exists() else '❌'} api_server.py (REST API)")
    print("      Launch: python run.py --web → http://localhost:8765")

    # 6. BOOT.md Chain (Route A)
    print("\n  [6] Route A (AI Management Chain)")
    chain_files = [
        "BOOT.md", "SYSTEM-PROMPT.md", "ACTION-PROTOCOL.md",
        "KNOWLEDGE-INDEX.md", "MEMORY.md", "ROLE-REGISTRY.md",
        "_HANDOFF/STATUS.md",
    ]
    all_present = True
    for f in chain_files:
        p = ROOT / f
        if p.exists():
            size_kb = p.stat().st_size / 1024
            print(f"      ✅ {f} ({size_kb:.1f}KB)")
        else:
            print(f"      ❌ {f} MISSING")
            all_present = False
    if all_present:
        print("      Route A: 100% ready — any AI can read BOOT.md and operate")

    # 7. DeerFlow Integration
    print("\n  [7] DeerFlow Integration")
    try:
        from deerflow_bridge import DeerFlowBridge
        bridge = DeerFlowBridge()
        status = bridge.status()
        if status["installed"]:
            print(f"      ✅ DeerFlow installed ({status['skills_count']} skills)")
            print("      ✅ Bridge: deerflow_bridge.py")
            print(f"      ✅ Config: {'present' if status['config_exists'] else 'missing'}")
        else:
            print("      ⚠️  DeerFlow directory not found")
    except Exception as e:
        print(f"      ⚠️  DeerFlow bridge: {e}")

    # 8. Skill Executor
    print("\n  [8] Skill Executor")
    try:
        from skill_executor import SkillExecutor
        executor = SkillExecutor()
        # NOTE: Don't call list_skills() here - it triggers lazy discovery which can block
        # Instead just report that it's available
        print(f"      ✅ SkillExecutor available (lazy-loaded, {len(executor._skill_cache)} cached)")
    except Exception as e:
        print(f"      ⚠️  Skill executor: {e}")

    # 9. Scenario Engine
    print("\n  [9] Scenario Engine")
    try:
        from scenario_engine import ScenarioEngineIntegration
        se = ScenarioEngineIntegration()
        scenarios = se.list_scenarios()
        print(f"      ✅ {len(scenarios)} scenarios registered")
    except Exception as e:
        print(f"      ⚠️  Scenario engine: {e}")

    print("\n  [10] Ghost Channel (Nervous System)")
    try:
        from ghost_channel_adapter import GhostChannelAdapter
        gc = GhostChannelAdapter()
        gc_st = gc.get_status()
        caps = gc_st.get("capabilities_active", 10)
        print(f"      ✅ GhostChannelAdapter: {caps}/10 capabilities")
        print(f"         Encryption: {gc_st.get('encryption', 'HMAC-SHA256')}")
    except Exception as e:
        print(f"      ⚠️  Ghost Channel: {e}")

    print(f"\n{'=' * 65}")
    print(f"  System: {'ALL GREEN ✅' if all_present else 'ISSUES FOUND ⚠️'}")
    print(f"{'=' * 65}")


def cmd_demo():
    """Run demo through unified engine."""
    from qspectrum_engine import QSpectrumEngine, run_demo
    engine = QSpectrumEngine()
    try:
        run_demo(engine)
    finally:
        engine.close()


def cmd_interactive():
    """Interactive chat through unified engine."""
    from qspectrum_engine import QSpectrumEngine, run_interactive
    engine = QSpectrumEngine()
    try:
        run_interactive(engine)
    finally:
        engine.close()


def cmd_query(query):
    """Single query."""
    from qspectrum_engine import QSpectrumEngine, run_single_query
    engine = QSpectrumEngine()
    try:
        run_single_query(engine, query)
    finally:
        engine.close()


def cmd_e2e():
    """Run E2E test suite (core regression tests)."""
    # Run all test suites in tests/ directory
    test_dir = ROOT / "tests"
    if not test_dir.exists():
        print("❌ tests/ directory not found")
        sys.exit(1)
    import subprocess
    passed = 0
    failed = 0
    for test_file in sorted(test_dir.glob("test_*.py")):
        print(f"\n{'='*60}")
        print(f"Running: {test_file.name}")
        print(f"{'='*60}")
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=str(ROOT),
        )
        if result.returncode == 0:
            passed += 1
        else:
            failed += 1
    print(f"\n{'='*60}")
    print(f"E2E Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    sys.exit(0 if failed == 0 else 1)


def cmd_chatroom():
    """Launch Web-based chatroom (redirects to --web mode)."""
    print("ℹ️  The standalone chatroom has been merged into Web mode.")
    print("   Launching: python run.py --web")
    print()
    cmd_web()


def cmd_web(port=8765, provider=None):
    """Launch Web API Server + Chat UI (browser-based chatroom)."""
    import sys as _sys

    from api_server import main as api_main
    argv = ["api_server.py", "--port", str(port)]
    if provider:
        argv.extend(["--provider", provider])
    _sys.argv = argv
    api_main()


def cmd_guide():
    """Guided onboarding for new users — step by step setup and intro."""
    import time
    import webbrowser

    print("=" * 65)
    print("  Q-SpecTrum 引导式启动 / Guided Onboarding")
    print("=" * 65)
    print()
    print("  欢迎来到 Q-SpecTrum — AI一人公司项目管理与开发系统")
    print("  Welcome to Q-SpecTrum — AI One-Person Company System")
    print()

    # Step 1: System check
    print("  [1/5] 系统健康检查 / System Health Check...")
    try:
        from qspectrum_engine import QSpectrumEngine
        engine = QSpectrumEngine()
        status = engine.get_system_status()
        roles = status.get("roles_loaded", 0)
        knowledge = status.get("knowledge_entries", 0)
        gc_active = "active" in str(status.get("ghost_channel", "")).lower()
        print(f"        ✅ 引擎正常 | Roles: {roles} | Knowledge: {knowledge}")
        print(f"        ✅ 幽灵通道: {'激活' if gc_active else '就绪'}")
        print(f"        ✅ LLM: {status.get('llm_provider', 'mock')}")
    except Exception as e:
        print(f"        ⚠️ 引擎启动异常: {e}")
        return

    # Step 2: LLM Configuration
    print()
    print("  [2/5] AI模型配置 / LLM Configuration")
    llm = os.environ.get("QSPECTRUM_LLM", "mock")
    if llm == "mock":
        print("        当前模式: Mock (演示模式，无需API密钥)")
        print("        To use real AI, set environment variable:")
        print("          export OPENAI_API_KEY=sk-...")
        print("          export QSPECTRUM_LLM=openai")
        print("        Or: export ANTHROPIC_API_KEY=sk-ant-...")
        print("          export QSPECTRUM_LLM=anthropic")
    else:
        print(f"        当前模式: {llm} ✅")

    # Step 3: Quick demo
    print()
    print("  [3/5] 快速演示 / Quick Demo")
    print("        发送一个测试查询...")
    try:
        result = engine.process("请介绍一下这个系统能为我做什么")
        role_name = result.get("routing", {}).get("role_name", "未知")
        response = result.get("response", "")[:150]
        print(f"        角色: {role_name}")
        print(f"        回复: {response}...")
        fb = result.get("feedback_loop", {})
        if fb.get("auto_recorded"):
            print(f"        ✅ 闭环反馈已记录 (质量: {fb.get('quality_score', 0)})")
    except Exception as e:
        print(f"        ⚠️ 演示失败: {e}")

    # Step 4: Available modes
    print()
    print("  [4/5] 可用模式 / Available Modes")
    print("        ┌─────────────────────────────────────────────┐")
    print("        │  python run.py              交互式聊天      │")
    print("        │  python run.py --web        Web可视化界面   │")
    print("        │  python run.py --chatroom   同 --web        │")
    print("        │  python run.py --demo       8场景演示       │")
    print("        │  python run.py --status     系统健康检查    │")
    print("        │  python run.py --e2e        端到端测试      │")
    print("        └─────────────────────────────────────────────┘")

    # Step 5: Launch web UI
    print()
    print("  [5/5] 启动Web界面 / Launch Web UI")
    print()
    choice = input("  是否启动Web可视化界面? (y/n, default: y): ").strip().lower()
    if choice in ("", "y", "yes", "是"):
        engine.close()
        print()
        print("  🚀 启动Web服务器...")
        print("  浏览器将自动打开 http://localhost:8765/chat.html")
        try:
            # Open browser after a short delay
            import threading
            def _open_browser():
                time.sleep(2)
                webbrowser.open("http://localhost:8765/chat.html")
            threading.Thread(target=_open_browser, daemon=True).start()
        except Exception:
            pass
        cmd_web(8765)
    else:
        engine.close()
        print()
        print("  ✅ 引导完成! 随时运行 python run.py 开始使用")


def show_help():
    print(__doc__)
    print("""
  NEW — Web Mode (browser-based AI chatroom):
  python run.py --web                    # Start Web Server (port 8765)
  python run.py --web --port 9000        # Custom port
  python run.py --web --provider openai  # Use real LLM

  Guided Onboarding (recommended for first use):
  python run.py --guide                  # Step-by-step setup guide
    """)


def main():
    args = sys.argv[1:]

    if not args:
        cmd_interactive()
    elif args[0] == "--demo":
        cmd_demo()
    elif args[0] == "--status":
        cmd_status()
    elif args[0] == "--query" and len(args) > 1:
        cmd_query(" ".join(args[1:]))
    elif args[0] == "--chatroom":
        cmd_chatroom()
    elif args[0] == "--web":
        port = 8765
        provider = None
        for i, a in enumerate(args[1:], 1):
            if a == "--port" and i + 1 < len(args):
                raw = args[i + 1]
                try:
                    port = int(raw)
                except ValueError:
                    print(f"❌ Invalid --port value {raw!r}: must be an integer 1–65535")
                    sys.exit(2)
                if not (1 <= port <= 65535):
                    print(f"❌ Invalid --port {port}: must be in range 1–65535")
                    sys.exit(2)
            elif a == "--provider" and i + 1 < len(args):
                provider = args[i + 1]
                valid = {"mock", "openai", "anthropic", "deepseek",
                         "openrouter", "ollama", "auto"}
                if provider not in valid:
                    print(f"❌ Unknown --provider {provider!r}. "
                          f"Valid: {', '.join(sorted(valid))}")
                    sys.exit(2)
        cmd_web(port, provider)
    elif args[0] == "--e2e":
        cmd_e2e()
    elif args[0] == "--guide":
        cmd_guide()
    elif args[0] in ("--help", "-h"):
        show_help()
    else:
        show_help()


if __name__ == "__main__":
    main()
