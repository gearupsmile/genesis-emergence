"""
LZ Diagnostic Script (v2 - ASCII safe)
1. Print 10 random agents' last 200 actions from Real and Sham
2. Show action trace patterns (transition matrix)
3. Run 1000-gen test with secretion_rate=10x, compare LZ
"""
import sys, os, random, collections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from engine.genesis_engine import GenesisEngine


def _lz76(s: str) -> float:
    """Normalized LZ76 complexity."""
    if not s or len(s) < 2:
        return 0.0
    n = len(s)
    c, i, l = 1, 0, 1
    while i + l <= n:
        if s[i:i+l] in s[max(0, i+l-l-1):i+l]:
            l += 1
        else:
            c += 1
            i += l
            l = 1
    denom = n * np.log2(n) if n > 1 else 1
    return c / denom


def run_and_inspect(mode_label, enable_secretion, generations=500, sim_steps=20):
    """Run N generations and inspect raw action traces."""
    random.seed(42)
    np.random.seed(42)

    engine = GenesisEngine(
        population_size=20,
        mutation_rate=0.1,
        simulation_steps=sim_steps,
        enable_secretion=enable_secretion
    )

    for g in range(generations):
        engine.run_cycle()

    recorder = engine.behavioral_tracker.action_recorder

    print(f"\n{'='*60}")
    print(f"MODE: {mode_label}  |  Gens={generations} | sim_steps={sim_steps}")
    print(f"{'='*60}")
    print(f"Total agent histories tracked: {len(recorder.agent_histories)}")

    # Get histories sorted by trace length (descending)
    all_traces = sorted(
        [(aid, list(hist.action_trace))
         for aid, hist in recorder.agent_histories.items()
         if len(hist.action_trace) > 0],
        key=lambda x: len(x[1]),
        reverse=True
    )

    if not all_traces:
        print("  No traces found!")
        return recorder, []

    print(f"Agents with traces: {len(all_traces)}")
    lengths = [len(t) for _, t in all_traces]
    print(f"Trace lengths  ->  max={max(lengths)}  min={min(lengths)}  avg={np.mean(lengths):.1f}")

    # Sample 10 (prefer longest)
    sample = all_traces[:10]
    all_action_strings = []

    print(f"\nTop 10 longest traces:")
    print(f"-" * 60)

    for i, (agent_id, trace) in enumerate(sample):
        # trace elements: (gen, action_code)
        action_str = ''.join(a for _, a in trace)
        all_action_strings.append(action_str)
        last = action_str[-200:]
        lz = _lz76(action_str)
        cntr = collections.Counter(action_str)
        freq_str = '  '.join(f"{k}:{v}" for k, v in sorted(cntr.items()))
        short_id = agent_id[:20] if len(agent_id) > 20 else agent_id
        print(f"\n[{i+1}] {short_id}  len={len(action_str)}  LZ={lz:.3f}")
        print(f"     Freqs: {freq_str}")
        print(f"     Last200: {last}")

    return recorder, all_action_strings


def plot_transitions(traces_real, traces_sham, out_path):
    """Plot action transition heatmaps."""
    chars = ['M', 'I', 'S']

    def build_mat(strings):
        idx = {c: i for i, c in enumerate(chars)}
        mat = np.zeros((len(chars), len(chars)))
        for s in strings:
            for a, b in zip(s, s[1:]):
                if a in idx and b in idx:
                    mat[idx[a], idx[b]] += 1
        rs = mat.sum(axis=1, keepdims=True).clip(min=1)
        return mat / rs

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Action Transition Probabilities: Real vs Sham", fontsize=14)

    for ax, strings, title in [
        (axes[0], traces_real, "Real (Secretion ON)"),
        (axes[1], traces_sham, "Sham (Secretion OFF)")
    ]:
        mat = build_mat(strings) if strings else np.zeros((3, 3))
        im = ax.imshow(mat, vmin=0, vmax=1, cmap='Blues')
        ax.set_xticks(range(3)); ax.set_xticklabels(chars)
        ax.set_yticks(range(3)); ax.set_yticklabels(chars)
        ax.set_xlabel("Next"); ax.set_ylabel("Current")
        ax.set_title(title)
        for r in range(3):
            for c in range(3):
                ax.text(c, r, f"{mat[r,c]:.2f}", ha='center', va='center', fontsize=11)
        plt.colorbar(im, ax=ax)

    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    print(f"Transition heatmap saved -> {out_path}")


def run_10x_secretion_test(generations=1000, sim_steps=20):
    """Run 1x vs 10x secretion rate and compare LZ distributions."""
    print(f"\n{'='*60}")
    print(f"SECRETION RATE TEST: 1x vs 10x,  {generations} gens")
    print(f"{'='*60}")

    import engine.structurally_evolvable_agent as sea_mod

    for label, mult in [("1x (baseline)", 1.0), ("10x (amplified)", 10.0)]:
        random.seed(42)
        np.random.seed(42)

        engine = GenesisEngine(
            population_size=20, mutation_rate=0.1,
            simulation_steps=sim_steps, enable_secretion=True
        )

        if mult != 1.0:
            _orig = sea_mod.StructurallyEvolvableAgent.secrete
            def _make(m, orig):
                def _patched(self, substrate, amount=None):
                    if amount is None:
                        amount = max(0.01, self.genome.metabolic_cost * 0.1) * m
                    # Call deposit directly to avoid recursion
                    if not hasattr(self, 'x') or not hasattr(self, 'y'):
                        return
                    x, y = int(self.x), int(self.y)
                    substrate.deposit_secretion(x, y, amount)
                    self.genome.metabolic_energy = max(
                        0, getattr(self.genome, 'metabolic_energy', 10) - amount * 0.5
                    )
                return _patched
            sea_mod.StructurallyEvolvableAgent.secrete = _make(mult, _orig)

        for g in range(generations):
            engine.run_cycle()

        recorder = engine.behavioral_tracker.action_recorder
        lz_scores, lengths = [], []
        for hist in recorder.agent_histories.values():
            if len(hist.action_trace) > 5:
                s = ''.join(a for _, a in hist.action_trace)
                lengths.append(len(s))
                lz_scores.append(_lz76(s))

        s_mean = np.mean(engine.substrate.S)
        print(f"\n  [{label}]")
        print(f"    Agents with traces:  {len(lz_scores)}")
        print(f"    Avg trace length:    {np.mean(lengths):.1f}" if lengths else "    N/A")
        print(f"    Avg LZ:              {np.mean(lz_scores):.4f}" if lz_scores else "    N/A")
        print(f"    LZ std:              {np.std(lz_scores):.4f}" if lz_scores else "    N/A")
        print(f"    S field mean:        {s_mean:.4f}")

        # Restore
        if mult != 1.0:
            sea_mod.StructurallyEvolvableAgent.secrete = _orig


if __name__ == "__main__":
    print("PART 1 & 3: Trace Inspection (Real vs Sham, 500 gens, 20 steps/gen)")

    _, traces_real = run_and_inspect("REAL", True,  generations=500, sim_steps=20)
    _, traces_sham = run_and_inspect("SHAM", False, generations=500, sim_steps=20)

    plot_transitions(traces_real, traces_sham, "diagnostic_transitions.png")

    print("\nPART 2: 10x Secretion Rate LZ Comparison (1000 gens)")
    run_10x_secretion_test(generations=1000, sim_steps=20)

    print("\nDiagnostic complete.")
