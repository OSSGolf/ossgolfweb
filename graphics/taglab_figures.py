#!/usr/bin/env python3
"""Draw the figures for the OSSTagLab post from OSSTagLab's own test recordings.

    python3 graphics/taglab_figures.py [path to osstaglab checkout]

Reads test/fixtures/*.wav from the OSSTagLab repo (default: ../osstaglab) and writes PNGs into
_site/images/. /images is cached as immutable (_site/_headers), so bump VERSION whenever a figure's
look changes and update the names in posts.json.

Needs numpy, scipy and matplotlib.
"""
import sys
import wave
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy.signal import spectrogram

ROOT = Path(__file__).resolve().parent.parent
LAB = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "osstaglab"
OUT = ROOT / "_site" / "images"
VERSION = "v1"

PAPER, INK, MUTED, HAIR = "#0e1712", "#e6ead9", "#8fa094", "#33443a"
OUTLINE = [pe.withStroke(linewidth=3.5, foreground="#07090c")]   # keeps text readable on a bright trace
WAKE, REST, TAP, HIT = "#8fd46b", "#6fb1ff", "#ff7ad9", "#ffd84d"   # label colours, as in the bench screenshots

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "sans-serif"], "font.size": 11,
    "text.color": INK, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": HAIR, "figure.facecolor": PAPER, "axes.facecolor": "#07090c", "savefig.facecolor": PAPER,
})


def load(name):
    with wave.open(str(LAB / "test" / "fixtures" / f"{name}.wav")) as w:
        rate = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
    return x, rate


def spec(x, rate, lo, hi):
    """Spectrogram with a 10 ms window (one tag symbol long), 1 ms steps, in dB."""
    win = int(rate * 0.010)
    f, t, s = spectrogram(x, rate, window="hann", nperseg=win, noverlap=win - rate // 1000, nfft=4096,
                          scaling="spectrum", mode="psd")
    keep = (f >= lo) & (f <= hi)
    return f[keep], t, 10 * np.log10(s[keep] + 1e-20)


def draw(ax, x, rate, lo, hi, t0=0.0, t1=None):
    f, t, db = spec(x, rate, lo, hi)
    t1 = t[-1] if t1 is None else t1
    cols = (t >= t0) & (t <= t1)
    top = db[:, cols].max() + 3
    ax.imshow(db[:, cols], origin="lower", aspect="auto", cmap="magma", vmin=top - 37, vmax=top,
              extent=(t[cols][0] * 1000, t[cols][-1] * 1000, f[0] / 1000, f[-1] / 1000), interpolation="bilinear")
    ax.set_ylabel("kHz")
    ax.set_xlabel("ms")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def box(ax, t0, t1, f0, f1, color, label, where="above"):
    ax.add_patch(Rectangle((t0, f0), t1 - t0, f1 - f0, fill=False, edgecolor=color, linewidth=1.6))
    y, va = (f1 + 0.06, "bottom") if where == "above" else (f0 - 0.06, "top")
    ax.text((t0 + t1) / 2, y, label, color=color, ha="center", va=va, fontsize=11, fontweight="bold")


def track(x, rate, lo, hi):
    """Loudest frequency per millisecond."""
    f, t, db = spec(x, rate, lo, hi)
    return t, f[np.argmax(db, axis=0)], db.max(axis=0)


def save(fig, name):
    path = OUT / f"osstaglab-{name}-{VERSION}.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def timeline():
    """9 iron: wake tone, resting frame, the hit, the hop pattern."""
    x, rate = load("iron9-wake-tap-hop")
    fig, ax = plt.subplots(figsize=(9.6, 3.9), constrained_layout=True)
    draw(ax, x, rate, 16800, 20200)
    box(ax, 170, 610, 18.55, 19.05, WAKE, "Wake tone\n18.80 kHz")
    box(ax, 1090, 3570, 17.35, 18.45, REST, "Resting frame, repeated every 172 ms\nrest tone 17.91 kHz", "below")
    box(ax, 3575, 3640, 16.85, 20.15, TAP, "")
    ax.text(3560, 19.95, "Hit", color=TAP, ha="right", va="top", fontsize=11, fontweight="bold")
    box(ax, 3650, 4095, 18.7, 19.5, HIT, "")
    ax.text(4095, 19.58, "Hop pattern\n18.91 kHz", color=HIT, ha="right", va="bottom", fontsize=11, fontweight="bold")
    ax.set_ylim(16.8, 20.2)
    save(fig, "9-iron-timeline")


def resting_frame():
    """One 9 iron frame, with the 100 Hz grid and the six symbols."""
    x, rate = load("iron9-wake-tap-hop")
    rest, symbols, slot, period = 17909.0, (4, -1, -2, 1, -4, -3), 20.6, 171.65
    t, hz, _ = track(x, rate, 17300, 18500)
    after = (t > 1.30) & (np.abs(hz - rest) > 250)       # the first symbol of a frame is +4 steps
    start = t[after][0] * 1000 - 1.5
    fig, ax = plt.subplots(figsize=(9.6, 4.2), constrained_layout=True)
    draw(ax, x, rate, 17300, 18680, (start - 45) / 1000, (start + period + 150) / 1000)
    for step in range(-4, 5):
        ax.axhline((rest + 100 * step) / 1000, color=INK, alpha=0.5 if step == 0 else 0.16, linewidth=0.8,
                   linestyle="-" if step == 0 else ":")
    ax.text(start - 43, rest / 1000 + 0.13, "rest tone 17.91 kHz", color=INK, fontsize=10, va="bottom",
            path_effects=OUTLINE)
    for k, s in enumerate(symbols):
        at = start + k * slot + 5
        y = (rest + 100 * s) / 1000
        ax.text(at, y + (0.085 if s > 0 else -0.085), f"{s:+d}".replace("-", "−"), color=HIT, ha="center",
                va="bottom" if s > 0 else "top", fontsize=14, fontweight="bold", path_effects=OUTLINE)
    ax.annotate("", xy=(start + period, 18.56), xytext=(start, 18.56),
                arrowprops=dict(arrowstyle="<->", color=MUTED, linewidth=1))
    ax.text(start + period / 2, 18.575, "172 ms to the next frame", color=MUTED, ha="center", va="bottom", fontsize=10)
    ax.set_ylim(17.3, 18.68)
    ax.set_yticks([17.4, 17.6, 17.8, 18.0, 18.2, 18.4])
    save(fig, "resting-frame")


def hop_patterns():
    """Two clubs after a hit: same kind of signal, different jump and interval."""
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 5.4), constrained_layout=True, sharex=True)
    rows = (("iron9-wake-tap-hop", 3.60, "9 iron: +409 Hz every 61 ms", 18909),
            ("sandwedge-wake-tap-hop", 2.86, "56° wedge: +302 Hz every 122 ms", 18816))
    for ax, (name, t0, title, rest) in zip(axes, rows):
        x, rate = load(name)
        f, t, db = spec(x, rate, rest - 400, rest + 800)
        cols = (t >= t0) & (t <= t0 + 0.49)
        top = db[:, cols].max() + 3
        ax.imshow(db[:, cols], origin="lower", aspect="auto", cmap="magma", vmin=top - 37, vmax=top,
                  extent=(0, 490, f[0] / 1000, f[-1] / 1000), interpolation="bilinear")
        ax.axhline(rest / 1000, color=INK, alpha=0.45, linewidth=0.8)
        ax.set_ylabel("kHz")
        ax.set_title(title, loc="left", color=HIT, fontsize=11, fontweight="bold")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[1].set_xlabel("ms after the hit")
    save(fig, "hop-patterns")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    timeline()
    resting_frame()
    hop_patterns()
