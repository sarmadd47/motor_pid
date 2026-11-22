"""
Plot motor speed-control logs captured from PuTTY.

Each log is one column of the figure: measured speed vs. target on top,
PWM duty underneath. Lines must look like the firmware's output:
    target: 20   rpm: 19.9   duty:  66%

Usage:
    python plot_response.py docs/p_only.log docs/pi.log
    python plot_response.py "P only=docs/p_only.log" "PI=docs/pi.log" --seconds 20 -o docs/step_response.png
"""
import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt

LINE = re.compile(r"target:\s*(\d+)\s+rpm:\s*(-?\d+\.\d)\s+duty:\s*(\d+)%")
SAMPLE_S = 0.1  # firmware prints one line every 100 ms

# Light chart surface and ink
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
MEASURED = "#2a78d6"  # categorical slot 1 (blue)


def read_log(path):
    target, rpm, duty = [], [], []
    for line in Path(path).read_text(errors="ignore").splitlines():
        m = LINE.search(line)
        if m:
            target.append(int(m.group(1)))
            rpm.append(float(m.group(2)))
            duty.append(int(m.group(3)))
    t = [i * SAMPLE_S for i in range(len(rpm))]
    return t, target, rpm, duty


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("logs", nargs="+", help='log files, optionally "Label=path"')
    p.add_argument("--seconds", type=float, default=20, help="how many seconds of each log to plot")
    p.add_argument("-o", "--out", default="docs/step_response.png")
    args = p.parse_args()

    runs = []
    for item in args.logs:
        label, _, path = item.rpartition("=") if "=" in item else (Path(item).stem, "", item)
        t, target, rpm, duty = read_log(path)
        n = min(len(t), int(args.seconds / SAMPLE_S))
        if n == 0:
            raise SystemExit(f"No data lines found in {path}")
        runs.append((label, t[:n], target[:n], rpm[:n], duty[:n]))

    cols = len(runs)
    fig, axes = plt.subplots(2, cols, figsize=(5.2 * cols, 5.6), sharex="col",
                             gridspec_kw={"height_ratios": [2, 1]}, squeeze=False)
    fig.patch.set_facecolor(SURFACE)
    rpm_max = max(max(max(r[3]), max(r[2])) for r in runs) * 1.1

    for c, (label, t, target, rpm, duty) in enumerate(runs):
        top, bottom = axes[0][c], axes[1][c]
        style(top)
        style(bottom)

        top.step(t, target, where="post", color=INK_2, linewidth=1.5, linestyle="--", label="Target", zorder=3)
        top.plot(t, rpm, color=MEASURED, linewidth=2, label="Measured")
        top.set_ylim(0, rpm_max)
        top.set_title(label, color=INK, fontsize=12, loc="left", fontweight="bold")
        if c == 0:
            top.set_ylabel("Output shaft speed (RPM)", color=INK_2, fontsize=10)
            top.legend(frameon=False, fontsize=9, labelcolor=INK_2, loc="upper right")

        bottom.plot(t, duty, color=MEASURED, linewidth=2)
        bottom.set_ylim(0, 105)
        bottom.set_xlabel("Time (s)", color=INK_2, fontsize=10)
        if c == 0:
            bottom.set_ylabel("PWM duty (%)", color=INK_2, fontsize=10)

    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=200, facecolor=SURFACE)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
