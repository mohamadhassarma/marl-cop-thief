"""Visualization — generate analysis graphs from game results."""

import json
import sys
from pathlib import Path

# Allow running as script
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))


def load_results(path: str) -> dict:
    """Load game results from JSON file."""
    with open(path) as f:
        return json.load(f)


def plot_scores(results: dict, output_dir: Path) -> None:
    """Bar chart of Cop vs Thief scores per sub-game."""
    import matplotlib.pyplot as plt

    sub_games = results["sub_games"]
    indices = [f"G{g['sub_game_index'] + 1}" for g in sub_games]
    cop_scores = [g["cop_score"] for g in sub_games]
    thief_scores = [g["thief_score"] for g in sub_games]

    x = range(len(indices))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    bars1 = ax.bar([i - width/2 for i in x], cop_scores, width, label="Cop", color="#2196F3")
    bars2 = ax.bar([i + width/2 for i in x], thief_scores, width, label="Thief", color="#F44336")

    ax.set_xlabel("Sub-game")
    ax.set_ylabel("Points")
    ax.set_title("Scores per Sub-game")
    ax.set_xticks(list(x))
    ax.set_xticklabels(indices)
    ax.legend()
    ax.bar_label(bars1, padding=3)
    ax.bar_label(bars2, padding=3)

    total_cop = results["totals"]["cop"]
    total_thief = results["totals"]["thief"]
    ax.set_title(f"Scores per Sub-game | Total: Cop {total_cop} — Thief {total_thief}")

    plt.tight_layout()
    out = output_dir / "scores_per_subgame.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_moves(results: dict, output_dir: Path) -> None:
    """Line chart of moves taken per sub-game."""
    import matplotlib.pyplot as plt

    sub_games = results["sub_games"]
    indices = [f"G{g['sub_game_index'] + 1}" for g in sub_games]
    moves = [g["moves_taken"] for g in sub_games]
    colors = ["#F44336" if g["result"] == "thief_win" else "#2196F3" for g in sub_games]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(indices, moves, color=colors)
    ax.axhline(y=25, color="gray", linestyle="--", label="Max moves (25)")
    ax.set_xlabel("Sub-game")
    ax.set_ylabel("Moves taken")
    ax.set_title("Moves per Sub-game (Blue=Cop Win, Red=Thief Win)")
    ax.legend()

    for i, (idx, m) in enumerate(zip(indices, moves)):
        ax.text(i, m + 0.3, str(m), ha="center", fontsize=10)

    plt.tight_layout()
    out = output_dir / "moves_per_subgame.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_cumulative(results: dict, output_dir: Path) -> None:
    """Line chart of cumulative scores over sub-games."""
    import matplotlib.pyplot as plt

    sub_games = results["sub_games"]
    indices = [f"G{g['sub_game_index'] + 1}" for g in sub_games]

    cop_cum = []
    thief_cum = []
    cop_total = 0
    thief_total = 0

    for g in sub_games:
        cop_total += g["cop_score"]
        thief_total += g["thief_score"]
        cop_cum.append(cop_total)
        thief_cum.append(thief_total)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(indices, cop_cum, marker="o", label="Cop", color="#2196F3", linewidth=2)
    ax.plot(indices, thief_cum, marker="o", label="Thief", color="#F44336", linewidth=2)
    ax.set_xlabel("Sub-game")
    ax.set_ylabel("Cumulative points")
    ax.set_title("Cumulative Score Progression")
    ax.legend()

    plt.tight_layout()
    out = output_dir / "cumulative_scores.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved: {out}")


def plot_win_rate(results: dict, output_dir: Path) -> None:
    """Pie chart of win rates."""
    import matplotlib.pyplot as plt

    sub_games = results["sub_games"]
    cop_wins = sum(1 for g in sub_games if g["result"] == "cop_win")
    thief_wins = len(sub_games) - cop_wins

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        [cop_wins, thief_wins],
        labels=[f"Cop wins ({cop_wins})", f"Thief wins ({thief_wins})"],
        colors=["#2196F3", "#F44336"],
        autopct="%1.0f%%",
        startangle=90,
    )
    ax.set_title("Win Rate Distribution")

    plt.tight_layout()
    out = output_dir / "win_rate.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved: {out}")


def main():
    """Generate all visualizations from game results."""
    results_path = "results/game_results.json"
    output_dir = Path("assets")
    output_dir.mkdir(exist_ok=True)

    try:
        import matplotlib
        matplotlib.use("Agg")
    except ImportError:
        print("Installing matplotlib...")
        import subprocess
        subprocess.run(["uv", "add", "matplotlib"], check=True)
        import matplotlib
        matplotlib.use("Agg")

    results = load_results(results_path)
    print(f"Loaded results: {len(results['sub_games'])} sub-games")

    plot_scores(results, output_dir)
    plot_moves(results, output_dir)
    plot_cumulative(results, output_dir)
    plot_win_rate(results, output_dir)

    print("\nAll graphs saved to assets/")


if __name__ == "__main__":
    main()
