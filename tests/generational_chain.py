#!/usr/bin/env python3
"""
Generational Delivery Chain Resilience / 世代交付鏈韌性審計
==========================================================
Simulates 4 generations of receivers. Each generation:
  1. "Extract" the current folder to a fresh temp location
  2. Run verify-delivery static checks (fast subset)
  3. Do 20 interactions using the engine
  4. Run clean-for-delivery.sh to reset ephemeral state
  5. Pass to next generation

Checks:
  - Does each generation start from a health-GREEN state?
  - Does cruft accumulate across generations?
  - Does critical state (DB, routing_keywords) survive the handoff?
  - Does size stay stable (no runaway growth)?

This is the ultimate test of "single-folder delivery" — if a receiver can
pass the folder forward intact, the delivery model works.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class GenResult:
    def __init__(self, gen, path):
        self.gen = gen
        self.path = path
        self.size_before = 0
        self.size_after = 0
        self.interactions_ok = 0
        self.interactions_total = 0
        self.verify_quick_rc = -1
        self.platform_db_intact = False
        self.cleanup_rc = -1
        self.details = []


def dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())


def extract_generation(src: Path, dst: Path, gen: int) -> GenResult:
    """Copy src → dst (simulating ZIP extract)."""
    r = GenResult(gen, dst)
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    # Copy everything excluding .git to simulate a clean zip extract
    for item in src.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.copytree(item, dst / item.name, symlinks=True)
        else:
            shutil.copy2(item, dst / item.name)
    r.size_before = dir_size(dst)
    return r


def verify_quick(r: GenResult):
    """Run verify-delivery.py --quick to confirm static health."""
    p = subprocess.run(
        ["python3", "verify-delivery.py", "--quick"],
        cwd=r.path, capture_output=True, text=True, timeout=30,
    )
    r.verify_quick_rc = p.returncode
    out = p.stdout + p.stderr
    # Check critical markers
    db_ok = "platform.db content" in out and "15 roles" in out
    boot_ok = "Boot Chain 6 core files" in out
    r.platform_db_intact = db_ok and boot_ok
    r.details.append(f"verify_quick: rc={p.returncode}, db_ok={db_ok}, boot_ok={boot_ok}")


def run_interactions(r: GenResult, n: int = 20):
    """Fire N queries via the engine (in-process, no server needed)."""
    queries = [
        "寫一篇文章", "分析數據", "設計 UX", "審查安全", "研究競品",
        "幫我規劃項目", "你好", "教我怎麼開始", "我壓力大", "hello",
    ]
    import sys as _sys
    _sys.path.insert(0, str(r.path))
    # Clear cached modules
    for mod in list(_sys.modules):
        if any(n in mod for n in ["qspectrum_engine", "smart_mock",
                                    "scenario_engine", "skill_executor"]):
            del _sys.modules[mod]
    try:
        from qspectrum_engine import QSpectrumEngine, create_llm_provider
        llm, _ = create_llm_provider("mock")
        engine = QSpectrumEngine(llm_provider=llm)
        r.interactions_total = n
        for i in range(n):
            q = queries[i % len(queries)]
            try:
                result = engine.process(q, {"session_id": f"gen{r.gen}-{i}"})
                if result.get("routing"):
                    r.interactions_ok += 1
            except Exception as e:
                r.details.append(f"interaction {i} err: {str(e)[:60]}")
        engine.close()
    except Exception as e:
        r.details.append(f"engine init failed: {e}")
    # Clean module state
    for mod in list(_sys.modules):
        if any(n in mod for n in ["qspectrum_engine", "smart_mock",
                                    "scenario_engine", "skill_executor"]):
            del _sys.modules[mod]
    if str(r.path) in _sys.path:
        _sys.path.remove(str(r.path))


def run_cleanup(r: GenResult):
    """Run clean-for-delivery.sh (or .bat) to reset ephemeral state."""
    script = r.path / "clean-for-delivery.sh"
    if not script.exists():
        r.details.append("cleanup script missing")
        return
    p = subprocess.run(
        ["bash", "clean-for-delivery.sh"],
        cwd=r.path, capture_output=True, text=True, timeout=30,
    )
    r.cleanup_rc = p.returncode
    r.size_after = dir_size(r.path)


def main():
    print("=" * 72)
    print("  Generational Delivery Chain Resilience — 4 receivers")
    print("=" * 72)
    N_GENS = 4
    N_INTERACTIONS = 20
    base_tmp = Path("/tmp/qspec_gen_chain")
    if base_tmp.exists():
        shutil.rmtree(base_tmp, ignore_errors=True)
    base_tmp.mkdir()

    results = []
    src = ROOT  # First generation's source is the canonical folder

    for gen in range(1, N_GENS + 1):
        dst = base_tmp / f"gen{gen}"
        print(f"\n  ── Generation {gen} ──")
        # 1. Extract
        t0 = time.time()
        r = extract_generation(src, dst, gen)
        print(f"    extracted: {r.size_before:,} bytes")
        # 2. Verify --quick
        verify_quick(r)
        print(f"    verify-quick: rc={r.verify_quick_rc}, db_intact={r.platform_db_intact}")
        # 3. Run interactions
        run_interactions(r, N_INTERACTIONS)
        print(f"    interactions: {r.interactions_ok}/{r.interactions_total}")
        # 4. Clean for delivery
        run_cleanup(r)
        print(f"    cleanup: rc={r.cleanup_rc}, size_after={r.size_after:,}B")
        r.elapsed = time.time() - t0
        results.append(r)
        # Next generation extracts from THIS one
        src = dst

    # ── Analysis ──
    print("\n" + "─" * 72)
    print("  ANALYSIS")
    print("─" * 72)
    print(f"\n  {'Gen':<5}{'before':>12}{'after':>12}{'delta':>10}"
          f"{'verify':>8}{'actions':>10}{'cleanup':>10}")
    for r in results:
        delta = r.size_after - r.size_before if r.size_after else 0
        print(f"  {r.gen:<5}"
              f"{r.size_before:>12,}"
              f"{r.size_after:>12,}"
              f"{delta:>+10,}"
              f"{r.verify_quick_rc:>8}"
              f"{r.interactions_ok}/{r.interactions_total:<7}"
              f"{r.cleanup_rc:>10}")

    # Invariants
    print()
    # Between gen2 and gen4, size should be STABLE (gen1 legitimately shrinks
    # because cleanup strips ephemerals that were present in the source folder).
    sizes_after_gen1 = [r.size_after for r in results[1:] if r.size_after]
    if len(sizes_after_gen1) >= 2:
        growth = max(sizes_after_gen1) - min(sizes_after_gen1)
        growth_ok = growth < 100_000  # <100KB drift across gen2-N = stable
    else:
        growth = 0
        growth_ok = False
    gen1_size = results[0].size_before
    gen_final_size = results[-1].size_after
    total_change = (gen_final_size - gen1_size) if gen_final_size else 0

    all_verify_ok = all(r.verify_quick_rc == 0 for r in results)
    all_db_intact = all(r.platform_db_intact for r in results)
    all_interacted = all(r.interactions_ok >= 15 for r in results)  # ≥75%
    all_cleaned = all(r.cleanup_rc == 0 for r in results)

    print(f"    {'✓' if growth_ok else '✗'} Size stable across gens 2-4 "
          f"(drift across later gens: {growth:,}B)")
    print(f"       Note: gen1 legitimately shrinks ({gen1_size:,}→{results[0].size_after:,}) "
          f"as cleanup strips ephemerals present in source.")
    print(f"    {'✓' if all_verify_ok else '✗'} Every generation passes verify-quick")
    print(f"    {'✓' if all_db_intact else '✗'} platform.db intact in all gens")
    print(f"    {'✓' if all_interacted else '✗'} Each gen runs ≥15/{N_INTERACTIONS} interactions OK")
    print(f"    {'✓' if all_cleaned else '✗'} clean-for-delivery succeeds each gen")

    # Summary
    all_ok = growth_ok and all_verify_ok and all_db_intact and all_interacted and all_cleaned

    print()
    print("=" * 72)
    if all_ok:
        print("  ✅ GENERATIONAL CHAIN: folder survives 4 hand-offs intact")
    else:
        print("  ⚠  GENERATIONAL CHAIN: degradation detected")
        for r in results:
            if r.details:
                print(f"    gen{r.gen}: {r.details[:3]}")
    print("=" * 72)

    # Cleanup temp
    shutil.rmtree(base_tmp, ignore_errors=True)

    # Synthesis
    out = ROOT / "AUDIT-GENERATIONAL.md"
    with out.open("w", encoding="utf-8") as f:
        f.write("# Generational Delivery Chain Resilience\n\n")
        f.write(f"**{N_GENS} generations × {N_INTERACTIONS} interactions each**.\n\n")
        f.write("| Gen | Start size | End size | Δ | verify-quick | actions | cleanup |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for r in results:
            delta = r.size_after - r.size_before if r.size_after else 0
            f.write(f"| {r.gen} | {r.size_before:,} | {r.size_after:,} | {delta:+,} | "
                    f"{r.verify_quick_rc} | {r.interactions_ok}/{r.interactions_total} | "
                    f"{r.cleanup_rc} |\n")
    print(f"\n  ✓ Synthesis: {out}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
