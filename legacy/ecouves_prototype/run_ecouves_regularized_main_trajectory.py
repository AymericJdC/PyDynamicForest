#!/usr/bin/env python3
"""Run the final Écouves A5 trajectory from the regularized 1985 target.

This wrapper keeps the calibrated dynamic parameters unchanged by invoking the
article runner already versioned in PyDynamicForest. It then compares the new
trajectory with the frozen reference trajectory and writes one compact report.

Run from the PyDynamicForest repository root.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

METRICS = (
    "N", "G", "Dm", "Dg", "sigma_D", "Hm", "H0", "H0_minus_Hm", "rho_HD"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unique_csv(directory: Path, suffix: str) -> Path:
    matches = sorted(directory.glob(f"*{suffix}"))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one '*{suffix}' in {directory}; found {len(matches)}: {matches}"
        )
    return matches[0]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def index_comparison(rows: list[dict[str, str]]) -> dict[tuple[int, str], dict[str, str]]:
    return {
        (int(float(row["year"])), row["metric"]): row
        for row in rows
    }


def run_logged(command: list[str], log_path: Path, cwd: Path) -> None:
    with log_path.open("w", encoding="utf-8") as stream:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    if completed.returncode:
        raise RuntimeError(
            f"Command failed with code {completed.returncode}; see {log_path}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.home() / "Downloads" / "ECOUVES_NUM_2026-11-18",
    )
    parser.add_argument(
        "--target-state-dir",
        type=Path,
        default=Path("outputs/article_scenarios/ecouves_a5_solver_compatibility"),
    )
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    root = args.root.resolve()
    new_targets = (
        root
        / "02_CALIBRATION_A_CONSERVER"
        / "ecouves_multiyear_regularized_targets"
        / "02_constructed_targets"
        / "03_native_states"
    )
    initial_state = new_targets / "ecouves_a5_native_initial_state_1985.npz"
    baseline = (
        root
        / "01_REFERENCE_FINALE"
        / "ecouves_A5_frozen_1985_2020_81c6b67"
    )
    output = (
        root
        / "02_CALIBRATION_A_CONSERVER"
        / "ecouves_multiyear_regularized_targets"
        / "03_main_trajectory"
    )
    simulation_dir = output / "trajectory_K0377_cphi0165_D1e-5"
    log_dir = output / "logs"

    runner = repo / "scripts/article/run_ecouves_a5_main_1985_2020.py"
    for required in (initial_state, baseline, runner, args.target_state_dir):
        if not required.exists():
            raise FileNotFoundError(required)
    if output.exists():
        raise FileExistsError(f"Refusing existing output directory: {output}")
    log_dir.mkdir(parents=True)

    command = [
        sys.executable,
        str(runner),
        "--initial-state", str(initial_state),
        "--target-state-dir", str(args.target_state_dir.resolve()),
        "--output-dir", str(simulation_dir),
        "--no-progress",
    ]
    run_logged(command, log_dir / "trajectory.log", repo)

    baseline_csv = unique_csv(baseline, "_comparison.csv")
    new_csv = unique_csv(simulation_dir, "_comparison.csv")
    old = index_comparison(read_rows(baseline_csv))
    new = index_comparison(read_rows(new_csv))

    detailed = []
    summary = []
    for metric in METRICS:
        metric_rows = []
        for key in sorted(set(old) & set(new)):
            year, key_metric = key
            if key_metric != metric:
                continue
            old_value = float(old[key]["simulated_value"])
            new_value = float(new[key]["simulated_value"])
            target_value = float(new[key]["reconstructed_target_value"])
            relative_change = (
                (new_value - old_value) / old_value if old_value else float("nan")
            )
            row = {
                "year": year,
                "metric": metric,
                "frozen_simulation": old_value,
                "regularized_simulation": new_value,
                "regularized_minus_frozen": new_value - old_value,
                "relative_change_vs_frozen": relative_change,
                "regularized_target": target_value,
                "regularized_residual": new_value - target_value,
            }
            detailed.append(row)
            metric_rows.append(row)
        if metric_rows:
            summary.append(
                {
                    "metric": metric,
                    "max_abs_relative_change_vs_frozen": max(
                        abs(row["relative_change_vs_frozen"])
                        for row in metric_rows
                        if math.isfinite(row["relative_change_vs_frozen"])
                    ),
                    "relative_rmse_vs_regularized_target": math.sqrt(
                        sum(
                            ((row["regularized_simulation"] - row["regularized_target"])
                             / row["regularized_target"]) ** 2
                            for row in metric_rows
                            if row["regularized_target"]
                        ) / sum(1 for row in metric_rows if row["regularized_target"])
                    ),
                }
            )

    detailed_path = output / "regularized_main_trajectory_comparison.csv"
    with detailed_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(detailed[0]))
        writer.writeheader()
        writer.writerows(detailed)

    summary_path = output / "regularized_main_trajectory_summary.json"
    summary_path.write_text(
        json.dumps({row["metric"]: row for row in summary}, indent=2) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# Trajectoire principale depuis la cible 1985 régularisée",
        "",
        "Les paramètres dynamiques sont inchangés : `K=0.0377`, `c_phi=0.0165`, `c_h=1.66`, `D=1e-5`.",
        "",
        "| Variable | Changement maximal par rapport à la trajectoire gelée | RMSE relative face aux nouvelles cibles |",
        "|---|---:|---:|",
    ]
    for row in summary:
        report_lines.append(
            f"| `{row['metric']}` | "
            f"{100 * row['max_abs_relative_change_vs_frozen']:.3f}% | "
            f"{100 * row['relative_rmse_vs_regularized_target']:.3f}% |"
        )
    report_lines += [
        "",
        "## Traçabilité",
        "",
        f"- État initial régularisé : `{initial_state}`",
        f"- SHA-256 : `{sha256(initial_state)}`",
        f"- Runner : `{runner}`",
        f"- SHA-256 : `{sha256(runner)}`",
        f"- Trajectoire : `{simulation_dir}`",
    ]
    report = output / "regularized_main_trajectory_report.md"
    report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"[OK] {report}")
    print("[VERDICT] " + ", ".join(
        f"{row['metric']}={100 * row['max_abs_relative_change_vs_frozen']:.3f}%"
        for row in summary
    ))


if __name__ == "__main__":
    main()
