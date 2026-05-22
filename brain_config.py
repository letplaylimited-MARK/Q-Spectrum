"""Project brain configuration.

Edit this file to control which modules are enabled.
This is the Python equivalent of the architecture's brain.yaml.
"""

BRAIN = {
    # Profile: minimal | standard | full | custom
    "profile": "standard",

    # Module overrides (None = profile default, True/False = force on/off)
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

    # LLM provider: "mock" | "openai" | "anthropic" | "ollama" | None (env)
    "llm_provider": None,

    # MCP settings
    "mcp": {
        "enabled": True,
        "auto_bridge": True,
    },
}
