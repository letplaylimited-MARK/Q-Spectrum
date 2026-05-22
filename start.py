#!/usr/bin/env python3
"""Q-SpecTrum — Brain bootstrap.

Usage:
  python start.py                  # Interactive chat (default profile)
  python start.py --profile full   # Full profile with vector store
  python start.py --demo           # Run demo scenarios
  python start.py --status         # Show brain status
"""

import json
import sys


def main():
    args = sys.argv[1:]
    profile = "standard"
    demo_mode = False
    show_status = False

    for i, arg in enumerate(args):
        if arg == "--profile" and i + 1 < len(args):
            profile = args[i + 1]
        elif arg == "--demo":
            demo_mode = True
        elif arg == "--status":
            show_status = True

    from brain_core.brain import Brain
    brain = Brain(profile=profile)

    if show_status:
        print(json.dumps(brain.status(), indent=2, ensure_ascii=False, default=str))
        return

    print(f"[Brain] profile={brain.profile}  root={brain.root.name}")
    print(f"[Brain] graph={'✓' if brain.has_graph else '✗'}  "
          f"vector={'✓' if brain.has_vector_store else '✗'}  "
          f"db={'✓' if brain.db_path else '✗'}")

    if demo_mode:
        print("\n[Demonstration Mode]")
        print("  Profile:", brain.profile)
        print("  Root:", brain.root)
        print("  DB:", brain.get_db_path_str() or "(none)")
        print("  Graph:", "available" if brain.has_graph else "unavailable")
        print("  Vector Store:", "available" if brain.has_vector_store else "unavailable")
        print("  Protocol Bridge:", "loaded" if brain.protocol_bridge else "disabled")
        return

    print("\nStarting interactive session (Ctrl+C to exit)...\n")

    try:
        while True:
            user = input(">>> ").strip()
            if user.lower() in ("exit", "quit", "/exit", "/quit"):
                break
            if not user:
                continue
            print(f"[Echo] received {len(user)} chars")
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
