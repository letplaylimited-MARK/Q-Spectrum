"""brain_config.py — Project Brain Configuration Template.

Copy this file to brain_config.py and edit to match your project.
This is the Python equivalent of the architecture's brain.yaml.
"""

BRAIN = {
    # ─── Profile ──────────────────────────────────────────────
    # "minimal"  : graph only, no extras
    # "standard" : graph + mcp_bridge + capabilities (default)
    # "full"     : everything including vector store, protocol bridge
    # "custom"   : manually set each module below
    "profile": "standard",

    # ─── Module Overrides ─────────────────────────────────────
    # Set to True/False to force on/off for specific modules.
    # Leave as None to use profile default.
    "modules": {
        "graph": None,
        "vector_store": None,
        "protocol_bridge": None,
        "project_memory": None,
        "negotiation": None,
        "global_search": None,
        "contact": None,
        "task_manager": None,
        "scenario_engine": None,
    },

    # ─── LLM Provider ─────────────────────────────────────────
    # "mock"     : deterministic stub responses (no API key)
    # "openai"   : OpenAI API (requires OPENAI_API_KEY env)
    # "anthropic": Anthropic API (requires ANTHROPIC_API_KEY env)
    # "ollama"   : local Ollama instance
    # Set to None to read from QSPECTRUM_LLM env var instead.
    "llm_provider": None,

    # ─── MCP Settings ─────────────────────────────────────────
    "mcp": {
        "enabled": True,
        "auto_bridge": True,
        "host": "127.0.0.1",
        "port": 8080,
    },

    # ─── Project Metadata ─────────────────────────────────────
    "project": {
        "name": "My Q-SpecTrum Project",
        "version": "0.1.0",
        "description": "",
    },
}
