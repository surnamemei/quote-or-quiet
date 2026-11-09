"""Figures for paper/manuscript.md v0.2. Print scale (sizes in mm / pt as printed).
Run: python -I -B paper/figures/make_figures.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D
from pathlib import Path

OUT = Path(__file__).resolve().parent
MM = 1 / 25.4
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"], "svg.fonttype": "none",
                     "pdf.fonttype": 42, "font.size": 7, "axes.spines.right": False, "axes.spines.top": False,
                     "axes.linewidth": 0.8, "legend.frameon": False, "xtick.major.width": 0.8, "ytick.major.width": 0.8})
TERRA, AMBER, BLUE, GREEN, GREY, PURPLE = "#C96144", "#E99D4E", "#5185C0", "#55966B", "#99AABB", "#8281B9"


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---------------- Figure 1: pipeline ----------------
def fig1():
    fig, ax = plt.subplots(figsize=(183 * MM, 62 * MM))
    ax.set_xlim(0, 183); ax.set_ylim(0, 62); ax.axis("off")

    def box(x, y, w, h, text, fc="#FFFFFF", ec="#444444", bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=6.5,
                fontweight="bold" if bold else "normal", linespacing=1.25)

    def arrow(x0, y0, x1, y1, color="#444444"):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7, lw=0.8, color=color))

    box(2, 25, 22, 12, "Question", fc="#F2F2F2")
    for t, y in [("Web: 8 pages\n(DuckDuckGo)", 44), ("Wikipedia: top 5\n(FineWiki, pinned)", 27), ("Combined\n(rank fusion)", 10)]:
        box(36, y, 30, 12, t, fc="#EEF3FA")
        arrow(24, 31, 36, y + 6)
    ax.text(51, 59, "Evidence", ha="center", fontsize=7, fontweight="bold")
    box(78, 25, 34, 12, "Qwen3-4B reader\nplain + cautious prompt\n6 candidates", fc="#FBF0E3")
    for y in (50, 33, 16):
        arrow(66, y, 78, 31)
    ax.text(95, 44, "Exit 1: support\nall 3 sources agree", ha="center", fontsize=6.5, color=TERRA, fontweight="bold", linespacing=1.2)
    box(122, 25, 28, 12, "Gate V1–V5\nverbatim, typed span\nin hash-pinned page", fc="#FBF0E3")
    arrow(112, 31, 122, 31)
    ax.text(136, 44, "Exit 2: gate", ha="center", fontsize=6.5, color=TERRA, fontweight="bold")
    box(158, 25, 22, 12, "Phi-4 veto\nreaders agree", fc="#FBF0E3")
    arrow(150, 31, 158, 31)
    ax.text(169, 44, "Exit 3: veto", ha="center", fontsize=6.5, color=TERRA, fontweight="bold")
    box(132, 2, 48, 9, "Verified: released\nwith its pinned span", fc="#E4F0E8", ec=GREEN, bold=True)
    arrow(169, 25, 169, 11.8, GREEN)
    box(74, 2, 50, 9, "Unresolved: abstain\n(any exit fails)", fc="#F7E6E1", ec=TERRA, bold=True)
    arrow(95, 25, 97, 11.8, TERRA)
    arrow(136, 25, 118, 11.8, TERRA)
    ax.text(0, 2, "Assumptions outside\nthe deductive claim:\nA_S source true\nA_M question→entity\ngold correct",
            fontsize=5.8, va="bottom", color="#555555", linespacing=1.2)
    save(fig, "fig1_pipeline")


# ---------------- Figure 2: coverage vs SER ----------------
def fig2():
    fig, (a, b) = plt.subplots(1, 2, figsize=(183 * MM, 72 * MM), gridspec_kw={"wspace": 0.28})
    sets = {"SimpleQA": "o", "Mintaka": "s", "PopQA": "^"}
    sys_pts = {"SimpleQA": (0.372, 0.26), "Mintaka": (0.310, 1.40), "PopQA": (0.191, 0.81)}
    read_pts = {"SimpleQA": (0.875, 10.0), "Mintaka": (0.888, 12.9), "PopQA": (0.743, 24.1)}
    agree_pts = {"SimpleQA": (0.709, 3.0), "Mintaka": (0.758, 8.5), "PopQA": (0.567, 14.3)}

    def frame(ax):
        ax.set_yscale("log"); ax.set_xlim(0, 1); ax.set_ylim(0.15, 40)
        ax.axvline(0.35, color="#888888", lw=0.7, ls=":")
        ax.axhspan(0.39, 0.50, xmin=0.35, color=GREEN, alpha=0.18, lw=0)
        ax.axhline(1.0, color="#BBBBBB", lw=0.5)
        ax.set_xlabel("Coverage (share of questions answered)")
        ax.set_ylabel("Silent-error rate against gold (%)")
        ax.set_yticks([0.2, 0.5, 1, 2, 5, 10, 20]); ax.set_yticklabels(["0.2", "0.5", "1", "2", "5", "10", "20"])
        ax.minorticks_off()

    frame(a)
    for s, m in sets.items():
        a.scatter(*sys_pts[s], marker=m, s=34, color=TERRA, zorder=4)
        a.scatter(*agree_pts[s], marker=m, s=26, color=AMBER, zorder=3)
        a.scatter(*read_pts[s], marker=m, s=26, color=GREY, zorder=3)
    a.scatter(0.310, 0.45, marker="s", s=34, facecolors="none", edgecolors=TERRA, lw=1.1, zorder=4)
    a.plot([0.310, 0.310], [0.45, 1.40], color=TERRA, lw=0.7, zorder=2)
    a.annotate("Mintaka after\nblind adjudication", (0.31, 0.45), (0.42, 0.20), fontsize=6,
               arrowprops=dict(arrowstyle="-", lw=0.5, color="#666666"))
    a.text(0.62, 0.445, "L2 allowance", fontsize=6, color=GREEN, va="center")
    a.text(0.02, 0.17, "floor 0.35 →", fontsize=6, color="#777777")
    h = [Line2D([], [], marker="o", ls="", color=c, label=l, ms=4.5)
         for c, l in [(TERRA, "Frozen system"), (AMBER, "+ reader-agreement tier"), (GREY, "Single-pass reader")]]
    h += [Line2D([], [], marker=m, ls="", color="#444444", label=s, ms=4.5, mfc="none") for s, m in sets.items()]
    a.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=6, ncol=3, columnspacing=1, handletextpad=0.3)
    a.set_title("a  Sealed test sets", loc="left", fontsize=7.5, fontweight="bold")

    frame(b)
    for s, p0, p1, m in [("SimpleQA", (0.372, 0.26), (0.476, 0.92), "o"), ("Mintaka", (0.310, 0.45), (0.502, 1.45), "s")]:
        b.scatter(*p0, marker=m, s=34, color=TERRA, zorder=4)
        b.scatter(*p1, marker=m, s=34, color=PURPLE, zorder=4)
        b.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7, lw=0.9, color="#555555",
                                    shrinkA=3, shrinkB=3, zorder=3))
    b.text(0.50, 0.21, "SimpleQA, against gold:\n+159 releases, 10 errors (6.3%)", fontsize=5.8, ha="left", color="#555555")
    b.text(0.52, 2.4, "Mintaka, adjudicated:\n+385 releases, 20 errors (5.2%)", fontsize=5.8, ha="left", color="#555555")
    h2 = [Line2D([], [], marker="o", ls="", color=TERRA, label="Frozen system", ms=4.5),
          Line2D([], [], marker="o", ls="", color=PURPLE, label="Pinned pages + format-relaxed gate", ms=4.5),
          Line2D([], [], marker="o", ls="", color="#444444", label="SimpleQA", ms=4.5, mfc="none"),
          Line2D([], [], marker="s", ls="", color="#444444", label="Mintaka", ms=4.5, mfc="none")]
    b.legend(handles=h2, loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=6, ncol=2, columnspacing=1, handletextpad=0.3)
    b.set_ylabel("Silent-error rate (%)")
    b.set_title("b  Buying coverage with pinned pages", loc="left", fontsize=7.5, fontweight="bold")
    save(fig, "fig2_coverage_ser")


# ---------------- Figure 3: error composition ----------------
def fig3():
    fig, ax = plt.subplots(figsize=(120 * MM, 50 * MM))
    labels = ["SimpleQA\n(4 errors)", "PopQA\n(17 errors)", "Mintaka\n(28 errors)"]
    cats = [("Gold wrong, stale, or equally acceptable answer", [2, 6, 19], BLUE),
            ("Ambiguous question or entity", [0, 9, 2], AMBER),
            ("Answer judged wrong", [2, 2, 3], TERRA),
            ("Adjudicators could not settle", [0, 0, 4], GREY)]
    totals = [4, 17, 28]
    left = [0, 0, 0]
    for name, vals, col in cats:
        shares = [100 * v / t for v, t in zip(vals, totals)]
        ax.barh(range(3), shares, left=left, color=col, height=0.62, label=name, edgecolor="white", lw=0.6)
        for i, (v, s) in enumerate(zip(vals, shares)):
            if v:
                ax.text(left[i] + s / 2, i, str(v), ha="center", va="center", fontsize=6.5,
                        color="black" if col == GREY else "white")
        left = [l + s for l, s in zip(left, shares)]
    ax.set_yticks(range(3)); ax.set_yticklabels(labels); ax.invert_yaxis(); ax.set_xlim(0, 100)
    ax.set_xlabel("Share of the set's graded errors (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.28), ncol=2, fontsize=6, columnspacing=1.2, handlelength=1.2)
    save(fig, "fig3_error_composition")


if __name__ == "__main__":
    fig1(); fig2(); fig3()
    print("done")
