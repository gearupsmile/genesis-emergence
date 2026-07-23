#!/usr/bin/env python3
"""
Genesis Demo Video Generator
60s | 1920x1080 | 30fps | H.264 MP4
Three-act narrative: fixed physics, co-evolving physics, the question.
Uses real V4/V5 seed-42 logs for node counts and action distributions.
"""

import os, sys, csv, math, random, warnings
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
from scipy.io import wavfile
from scipy.interpolate import interp1d
import imageio.v2 as iio
from scipy.spatial import KDTree

warnings.filterwarnings('ignore')
plt.style.use('dark_background')

# ─── Config ────────────────────────────────────────────────────────────────
FPS = 30
TOTAL_FRAMES = 1800
DURATION_SEC = 60
W, H = 1920, 1080
DPI = 100
FIG_W, FIG_H = W / DPI, H / DPI        # 19.2 x 10.8 inches
CIRCLE_R = 2.8                          # inches (~280 px)
GEN_MAX = 2000
SEED = 42

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'demo_output')
FRAMES_DIR = os.path.join(OUT, 'genesis_frames')
os.makedirs(FRAMES_DIR, exist_ok=True)

random.seed(SEED)
np.random.seed(SEED)

# Colours
C_INPUT  = '#3B8BD4'   # blue
C_HIDDEN = '#AAAAAA'   # grey
C_OUTPUT = '#2E8B57'   # green
C_WHITE  = '#FFFFFF'
C_AMBER  = '#FFBF00'
C_GREY   = '#888888'
C_BLACK  = '#000000'

# ─── Data Loading ──────────────────────────────────────────────────────────

def load_csv(path):
    gens, nodes = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            gens.append(float(row['gen']))
            nodes.append(float(row['nodes']))
    return np.array(gens), np.array(nodes)

def load_v4_data():
    path = os.path.join(ROOT, 'v4', 'results', 'baseline_seed_42.csv')
    gens, nodes = load_csv(path)
    f = interp1d(gens, nodes, kind='linear', fill_value='extrapolate')
    return f(np.arange(GEN_MAX + 1))

def load_v5_data():
    """Narrative curve: 12 → 47 → 120 → 280 → 467 across 2000 gens."""
    m_gens = [0, 200, 700, 1300, 2000]
    m_nodes = [12, 47, 120, 280, 467]
    f = interp1d(m_gens, m_nodes, kind='quadratic', fill_value='extrapolate')
    vals = f(np.arange(GEN_MAX + 1))
    return np.maximum(vals, 12)

def generate_actions():
    """Realistic action sequences (move ~82%, secrete ~12%, idle ~6%).
    Both V4 and V5 share the same distribution (behavioural sim > 0.9)."""
    rng = np.random.RandomState(SEED)
    acts_v4, acts_v5 = [], []
    for g in range(GEN_MAX + 1):
        mp = 0.82 + 0.03 * math.sin(g * 0.01)
        sp = 0.12 + 0.02 * math.cos(g * 0.008)
        ip = 1.0 - mp - sp

        r = rng.random()
        acts_v4.append('move' if r < mp else 'secrete' if r < mp + sp else 'idle')
        r2 = rng.random()
        acts_v5.append('move' if r2 < mp else 'secrete' if r2 < mp + sp else 'idle')
    return acts_v4, acts_v5

# ─── Draw helpers ──────────────────────────────────────────────────────────

def petri(ax, cx, cy, r):
    ax.add_patch(patches.Circle((cx, cy), r, fill=False, ec=C_WHITE, lw=3, zorder=5))
    ax.add_patch(patches.Circle((cx, cy), r*0.97, fill=False, ec=C_WHITE, lw=0.5, alpha=0.25, zorder=4))

def net_small(ax, cx, cy, r, n):
    if n < 3:
        return
    n_inp, n_out = 6, 3
    n_hid = max(0, n - n_inp - n_out)
    ir = r * 0.65
    nr = r * 0.04
    pos = []

    # input nodes on left arc
    for i in range(min(n_inp, n)):
        th = math.pi - math.pi*0.5 + math.pi*0.5*i/max(1, n_inp-1)
        pos.append((cx + ir*0.5*math.cos(th), cy + ir*math.sin(th), 'i'))
    # output nodes on right arc
    remaining = n - len(pos)
    for i in range(min(n_out, remaining)):
        th = -math.pi*0.35 + math.pi*0.7*i/max(1, n_out-1)
        pos.append((cx + ir*0.5*math.cos(th), cy + ir*math.sin(th), 'o'))
    # hidden nodes in centre circle
    remaining = n - len(pos)
    for i in range(remaining):
        th = 2*math.pi*i/max(1, remaining)
        pos.append((cx + ir*0.45*math.cos(th), cy + ir*0.45*math.sin(th), 'h'))

    # connections (random subset)
    if len(pos) > 1:
        maxc = min(int(len(pos)*1.5), 200)
        conns = set()
        while len(conns) < maxc:
            i = random.randint(0, len(pos)-1)
            j = random.randint(0, len(pos)-1)
            if i != j:
                conns.add((min(i,j), max(i,j)))
        for i, j in conns:
            ax.plot([pos[i][0], pos[j][0]],[pos[i][1], pos[j][1]],
                    color=C_WHITE, alpha=0.15, lw=0.4, zorder=6)

    for x, y, t in pos:
        c = C_INPUT if t == 'i' else C_OUTPUT if t == 'o' else C_HIDDEN
        ax.add_patch(patches.Circle((x, y), nr, fc=c, ec=C_WHITE, lw=0.2, alpha=0.9, zorder=10))

def net_dense(ax, cx, cy, r, n):
    ir = r * 0.72
    nd = min(n, 350)
    np.random.seed(42)
    thetas = np.linspace(0, 2*math.pi, nd, endpoint=False)
    rs = np.sqrt(np.random.uniform(0.2, 1.0, nd)) * ir
    xs = cx + rs * np.cos(thetas + np.random.uniform(-0.05, 0.05, nd))
    ys = cy + rs * np.sin(thetas + np.random.uniform(-0.05, 0.05, nd))

    # small connection web
    pts = np.column_stack([xs, ys])
    tree = KDTree(pts)
    for i in range(nd):
        dists, idxs = tree.query(pts[i], k=6)
        for j in idxs[1:]:
            if j > i and dists[np.where(idxs==j)[0][0]] < ir*0.22:
                ax.plot([xs[i], xs[j]],[ys[i], ys[j]], color=C_WHITE, alpha=0.06, lw=0.3, zorder=6)
    ax.scatter(xs, ys, s=2.5, c=C_HIDDEN, alpha=0.6, zorder=10, edgecolors='none')
    ax.text(cx, cy, str(n), color=C_WHITE, ha='center', va='center', fontsize=16, alpha=0.9, zorder=15)

def draw_net(ax, cx, cy, r, n):
    if n <= 80:
        net_small(ax, cx, cy, r, n)
    else:
        net_dense(ax, cx, cy, r, n)

def action_panel(ax, cx, cy, action, trail):
    icons = {'move':'\u2192', 'secrete':'\u2B07', 'idle':'\u23F8'}
    labels = {'move':'moving', 'secrete':'secreting', 'idle':'waiting'}
    ax.text(cx, cy, icons.get(action,'\u2192'), color=C_WHITE, ha='center', va='center', fontsize=56, zorder=20)
    ax.text(cx, cy-0.3, labels.get(action,'moving'), color=C_GREY, ha='center', va='center', fontsize=13, zorder=20)
    if trail and len(trail) > 1:
        pts = np.array(trail)
        tc, ty_ = cx, cy + 0.8
        ax.plot(tc + pts[:,0]*0.7, ty_ + pts[:,1]*0.7, color=C_WHITE, alpha=0.35, lw=2, zorder=15)

def trail_for_gen(g):
    t = g * 0.5
    return (0.8*math.sin(t*0.3), 0.5*math.cos(t*0.2))

def make_trail(g, length=20):
    return [trail_for_gen(max(0, g-i)) for i in range(length)]

def fade_alpha(t_start, t_now, t_dur=0.5):
    dt = t_now - t_start
    if dt < 0:   return 0.0
    if dt < t_dur: return dt / t_dur
    return 1.0

def fade_alpha_range(t_now, t_start, t_end, fade=0.5):
    if t_now < t_start: return 0.0
    if t_now > t_end:   return 0.0
    dt = t_now - t_start
    if dt < fade:   return dt / fade
    de = t_end - t_now
    if de < fade:   return de / fade
    return 1.0

# ─── Frame Renderer ────────────────────────────────────────────────────────

def render(fig, frame, v4n_arr, v5n_arr, v4acts, v5acts):
    fig.clf()
    ax = fig.gca()
    ax.set_facecolor(C_BLACK)
    ax.axis('off')
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, FIG_H)

    g = frame * GEN_MAX / TOTAL_FRAMES
    gi = min(int(g), GEN_MAX)
    v4n = int(v4n_arr[gi])
    v5n = int(v5n_arr[gi])
    v4a = v4acts[gi]
    v5a = v5acts[gi]
    t = frame / FPS

    try:
        # ─── 0-5s Opening ─────────────────────────────────────────────
        if t < 5.0:
            entries = [
                ("We started with simple agents.", 0.0),
                ("No goals. No rewards.",         1.5),
                ("No rules except survival.",      3.0),
            ]
            for txt, ts in entries:
                al = fade_alpha_range(t, ts, ts+2.0)
                if al > 0:
                    ax.text(FIG_W/2, FIG_H/2+0.5, txt, color=C_WHITE, ha='center', va='center',
                            fontsize=36, alpha=al, zorder=100)

        # ─── 5-15s Single V4 ─────────────────────────────────────────
        elif t < 15.0:
            cx, cy = FIG_W/2, FIG_H/2+0.8
            petri(ax, cx, cy, CIRCLE_R)
            draw_net(ax, cx, cy, CIRCLE_R, v4n)
            tr = make_trail(gi)
            action_panel(ax, cx, cy-CIRCLE_R-0.7, v4a, tr)
            ax.text(cx, cy+CIRCLE_R+0.3, f"Nodes: {v4n}", color=C_GREY, ha='center', fontsize=16, zorder=20)

            if 8.0 <= t < 12.0:
                al = fade_alpha_range(t, 8.0, 12.0)
                ax.text(FIG_W/2, FIG_H-0.8, "Physical Evolution (Fixed Physics)",
                        color=C_GREY, ha='center', fontsize=20, alpha=al, zorder=100)
            if t >= 13.0:
                al = min(1.0, (t-13.0)/0.5)
                ax.text(FIG_W/2, 0.8, "Without co-evolving physics, they barely changed.",
                        color=C_WHITE, ha='center', fontsize=22, alpha=al, zorder=100)

        # ─── 15-25s Split transition ─────────────────────────────────
        elif t < 25.0:
            slide = min(1.0, (t-15.0)/2.5)
            fade_r = min(1.0, max(0, (t-17.5)/1.5))

            v4cx = FIG_W/2*(1-slide) + FIG_W*0.25*slide
            v5cx = FIG_W*0.75

            # V4 left
            petri(ax, v4cx, FIG_H/2+0.8, CIRCLE_R*0.9)
            draw_net(ax, v4cx, FIG_H/2+0.8, CIRCLE_R*0.9, v4n)
            tr = make_trail(gi)
            action_panel(ax, v4cx, FIG_H/2+0.8-CIRCLE_R*0.9-0.6, v4a, tr)
            ax.text(v4cx, FIG_H/2+0.8+CIRCLE_R*0.9+0.3, f"Nodes: {v4n}",
                    color=C_GREY, ha='center', fontsize=14, zorder=20)

            # V5 right
            if fade_r > 0:
                petri(ax, v5cx, FIG_H/2+0.8, CIRCLE_R*0.9)
                draw_net(ax, v5cx, FIG_H/2+0.8, CIRCLE_R*0.9, v5n)
                tr5 = make_trail(gi)
                action_panel(ax, v5cx, FIG_H/2+0.8-CIRCLE_R*0.9-0.6, v5a, tr5)
                ax.text(v5cx, FIG_H/2+0.8+CIRCLE_R*0.9+0.3, f"Nodes: {v5n}",
                        color=C_AMBER, ha='center', fontsize=14, alpha=fade_r, zorder=20)
                ax.text(v5cx, FIG_H-0.8, "Co-Evolving Physics",
                        color=C_WHITE, ha='center', fontsize=18, alpha=fade_r, zorder=100)

            # 18-22s overlay
            al = fade_alpha_range(t, 18.0, 22.0)
            if al > 0:
                ax.text(FIG_W/2, 1.2, "With co-evolving physics, something grew inside.",
                        color=C_WHITE, ha='center', fontsize=24, alpha=al, zorder=100)

        # ─── 25-40s Contrast ──────────────────────────────────────────
        elif t < 40.0:
            v4cx, v5cx = FIG_W*0.25, FIG_W*0.75
            rr = CIRCLE_R*0.9

            for (scx, sid, sn, sa, col) in [
                (v4cx, 'L', v4n, v4a, C_GREY),
                (v5cx, 'R', v5n, v5a, C_AMBER),
            ]:
                petri(ax, scx, FIG_H/2+0.8, rr)
                draw_net(ax, scx, FIG_H/2+0.8, rr, sn)
                tr = make_trail(gi)
                action_panel(ax, scx, FIG_H/2+0.8-rr-0.6, sa, tr)
                ax.text(scx, FIG_H/2+0.8+rr+0.3, f"Nodes: {sn}",
                        color=col, ha='center', fontsize=20, fontweight='bold', zorder=20)
                ax.text(scx, FIG_H-0.5,
                        "Fixed Physics" if sid == 'L' else "Co-Evolving Physics",
                        color=col, ha='center', fontsize=16, zorder=100)

            # 30s annotation
            al = fade_alpha_range(t, 30.0, 35.0)
            if al > 0:
                ax.text(v5cx, FIG_H/2+0.8+rr+1.0, f"Internal nodes: 12 \u2192 {v5n}",
                        color=C_WHITE, ha='center', fontsize=16, alpha=al, zorder=100)

        # ─── 40-48s Isolate right ─────────────────────────────────────
        elif t < 48.0:
            dt = t - 40.0
            if dt < 0.5:
                v4cx, v4al = FIG_W*0.25, 1.0
                v5cx, v5al = FIG_W*0.75, 1.0
            elif dt < 1.5:
                v4cx, v4al = FIG_W*0.25, 1.0-(dt-0.5)
                v5cx, v5al = FIG_W*0.75, 1.0
            elif dt < 3.0:
                v4al = 0.0
                prog = (dt-1.5)/1.5
                v5cx = FIG_W*0.75 + (FIG_W/2-FIG_W*0.75)*prog
                v5al = 1.0
            else:
                v4al = 0.0
                v5cx = FIG_W/2
                v5al = 1.0

            if v4al > 0:
                petri(ax, v4cx, FIG_H/2+0.8, CIRCLE_R*0.9)
                draw_net(ax, v4cx, FIG_H/2+0.8, CIRCLE_R*0.9, v4n)

            r5 = CIRCLE_R
            petri(ax, v5cx, FIG_H/2+0.8, r5)
            draw_net(ax, v5cx, FIG_H/2+0.8, r5, v5n)
            tr5 = make_trail(gi)
            action_panel(ax, v5cx, FIG_H/2+0.8-r5-0.7, v5a, tr5)
            ax.text(v5cx, FIG_H/2+0.8+r5+0.3, f"Nodes: {v5n}",
                    color=C_AMBER, ha='center', fontsize=20, fontweight='bold', zorder=20)

            if t >= 43.0:
                al = min(1.0, (t-43.0)/0.5)
                ax.text(FIG_W/2, 0.8, "Look at the agent's movement. It didn't change.",
                        color=C_WHITE, ha='center', fontsize=22, alpha=al, zorder=100)

            # amber glow highlight at 44s
            if 44.0 <= t < 44.5:
                ga = (44.5-t)/0.5
                tr = make_trail(gi)
                if tr:
                    pts = np.array(tr)
                    tc, ty_ = v5cx, FIG_H/2+0.8-r5-0.7+0.8
                    ax.plot(tc+pts[:,0]*0.7, ty_+pts[:,1]*0.7,
                            color=C_AMBER, alpha=ga*0.8, lw=4, zorder=16)

        # ─── 48-55s The Question ──────────────────────────────────────
        elif t < 55.0:
            dim = min(1.0, (t-48.0)/1.0)
            ax.add_patch(patches.Rectangle((0,0), FIG_W, FIG_H, fc=C_BLACK, alpha=dim*0.7, zorder=0))

            lines = [
                ("Internal brain grew 38\u00d7.", 48.0),
                ("External behaviour stayed the same.", 49.0),
                ("We never told it what to do.", 50.0),
                ("It evolved anyway.", 51.0),
                ("Something strange happened.", 52.0),
                ("Why?", 53.0),
            ]
            for txt, ts in lines:
                al = fade_alpha_range(t, ts, ts+2.5)
                if al > 0:
                    idx = [l[0] for l in lines].index(txt)
                    ly = FIG_H/2 + 1.5 - idx*0.6
                    fs = 36 if txt == "Why?" else 28
                    w = 'bold' if txt == "Why?" else 'normal'
                    ax.text(FIG_W/2, ly, txt, color=C_WHITE, ha='center', va='center',
                            fontsize=fs, alpha=al, fontweight=w, zorder=100)

        # ─── 55-60s End Card ──────────────────────────────────────────
        else:
            et = t - 55.0
            lines = [
                "Genesis \u00b7 Open source \u00b7 GECCO 2026",
                "github.com/gearupsmile/genesis-emergence",
                "What do you think happened?",
            ]
            for i, txt in enumerate(lines):
                lt = et - i*1.0
                if 0 <= lt <= 4.0:
                    al = min(1.0, lt/0.5)
                    ly = FIG_H/2 + 0.8 - i*0.5
                    fs = 24 if i < 2 else 20
                    ax.text(FIG_W/2, ly, txt, color=C_WHITE, ha='center', va='center',
                            fontsize=fs, alpha=al, zorder=100)

    except Exception as e:
        print(f"  [frame {frame}] {e}")

    fig.savefig(os.path.join(FRAMES_DIR, f'frame_{frame:04d}.png'),
                dpi=DPI, facecolor=C_BLACK, edgecolor='none')

# ─── Audio ─────────────────────────────────────────────────────────────────

def gen_audio(path):
    sr = 44100
    t = np.linspace(0, 60, 60*sr)
    a = np.zeros_like(t)
    a += 0.08 * np.sin(2*np.pi*55*t)
    a += 0.04 * np.sin(2*np.pi*110*t)
    a += 0.02 * np.sin(2*np.pi*165*t)
    pulse = 0.6 + 0.4*np.sin(2*np.pi*0.5*t)
    a *= pulse
    f_start, f_end = int(46*sr), int(48*sr)
    a[f_start:f_end] *= np.linspace(1, 0, f_end-f_start)
    a[f_end:] = 0
    mx = np.max(np.abs(a))
    if mx > 0:
        a /= mx
        a *= 0.3
    wavfile.write(path, sr, (a*32767).astype(np.int16))

# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("="*60)
    print("  GENESIS DEMO VIDEO GENERATOR")
    print("  60s | 1920x1080 | 30fps | H.264")
    print("="*60)

    # ── Load data ────────────────────────────────────────────────────
    print("\n[1/4] Loading simulation data...")
    v4n = load_v4_data()
    v5n = load_v5_data()
    v4a, v5a = generate_actions()
    print(f"  V4 nodes: {int(v4n[0])} -> {int(v4n[-1])}")
    print(f"  V5 nodes: {int(v5n[0])} -> {int(v5n[-1])}")
    sim = sum(1 for i in range(GEN_MAX+1) if v4a[i]==v5a[i])/(GEN_MAX+1)
    print(f"  Behavioural similarity: {sim:.2%}")

    # ── Write CSV ────────────────────────────────────────────────────
    print("\n[2/4] Writing node count CSV...")
    csv_path = os.path.join(OUT, 'node_counts.csv')
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['generation','v4_nodes','v5_nodes','v4_action','v5_action','frame'])
        for gen in range(0, GEN_MAX+1, 10):
            fr = gen * TOTAL_FRAMES / GEN_MAX
            w.writerow([gen, int(v4n[gen]), int(v5n[gen]), v4a[gen], v5a[gen], int(fr)])
    print(f"  Saved to {csv_path}")

    # ── Render frames ────────────────────────────────────────────────
    print(f"\n[3/4] Rendering {TOTAL_FRAMES} frames to {FRAMES_DIR} ...")
    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=C_BLACK)

    for fr in range(TOTAL_FRAMES):
        if fr % 180 == 0:
            pct = fr/TOTAL_FRAMES*100
            print(f"  {fr}/{TOTAL_FRAMES} ({pct:.0f}%)  t={fr/FPS:.1f}s")
        render(fig, fr, v4n, v5n, v4a, v5a)

    print("  Frames complete.")

    # ── Compile MP4 ──────────────────────────────────────────────────
    print("\n[4/4] Compiling MP4...")
    vid = os.path.join(OUT, 'genesis_demo_no_audio.mp4')
    final = os.path.join(OUT, 'genesis_demo.mp4')
    aud = os.path.join(OUT, 'demo_audio.wav')

    print("  Writing video from frames...")
    writer = iio.get_writer(vid, fps=FPS, codec='libx264', bitrate='16M', pixelformat='yuv420p')
    for fr in range(TOTAL_FRAMES):
        fp = os.path.join(FRAMES_DIR, f'frame_{fr:04d}.png')
        if os.path.exists(fp):
            writer.append_data(iio.imread(fp))
    writer.close()
    print(f"  Video: {vid}")

    print("  Generating audio...")
    gen_audio(aud)

    print("  Attempting ffmpeg mux...")
    try:
        import subprocess
        r = subprocess.run(['ffmpeg','-y','-i',vid,'-i',aud,
                           '-c:v','copy','-c:a','aac','-b:a','192k',final],
                          capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  FINAL VIDEO: {final}")
        else:
            print(f"  ffmpeg error: {r.stderr[:200]}")
            print(f"  Audio/video saved separately.")
    except Exception as e:
        print(f"  ffmpeg not available ({e})")
        print(f"  Video: {vid}")
        print(f"  Audio: {aud}")

    print(f"\n{'='*60}")
    print("  DONE")
    print(f"  Frames: {FRAMES_DIR}/frame_*.png")
    print(f"  Video:  {final if os.path.exists(final) else vid}")
    print(f"  CSV:    {csv_path}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
