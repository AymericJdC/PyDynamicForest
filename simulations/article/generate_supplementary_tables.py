#!/usr/bin/env python3
"""Generate LaTeX Tables S1--S5 for Online Resource 1.

Run from the PyDynamicForest repository root after the article trajectory,
initial-state manifest, and interval diagnostic have been generated.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

OBS_ORDER = ["N", "G", "Dm", "Dg", "sigma_D", "Hm", "H0", "H0_minus_Hm"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: Any, digits: int = 2, signed: bool = False) -> str:
    number = as_float(value)
    if number is None:
        return r"\NA"
    spec = f"{'+' if signed else ''}.{digits}f"
    if abs(number) < 0.5 * 10 ** (-digits):
        number = 0.0
    return format(number, spec)


def fmt_age(value: Any) -> str:
    number = as_float(value)
    if number is None:
        return r"\NA"
    return f"{number:g}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def latex_escape(text: Any) -> str:
    value = str(text or "")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def generate_s1(rows: list[dict[str, str]]) -> str:
    body = []
    for row in rows:
        interval = f"{fmt_age(row.get('initial_age'))}--{fmt_age(row.get('final_age'))}"
        status = (row.get("empirical_interpretation_status") or "pending data review").replace("_", " ")
        body.append(
            " & ".join([
                interval,
                fmt(row.get("observed_stem_loss"), 1),
                fmt(row.get("simulated_stem_loss"), 1),
                fmt(100 * as_float(row.get("observed_apparent_mortality_rate")) if as_float(row.get("observed_apparent_mortality_rate")) is not None else None, 2),
                fmt(100 * as_float(row.get("simulated_apparent_mortality_rate")) if as_float(row.get("simulated_apparent_mortality_rate")) is not None else None, 2),
                fmt(100 * as_float(row.get("mortality_rate_difference")) if as_float(row.get("mortality_rate_difference")) is not None else None, 2, signed=True),
                latex_escape(status),
            ]) + r" \\"
        )
    return r"""\begin{table}[htbp]
\centering
\small
\caption{Apparent stem losses and annual rates between consecutive inventories.
The empirical interpretation status remains provisional pending review of the
experimental history.}
\label{tab:supp-stem-loss-intervals}
\begin{tabular}{lrrrrrl}
\toprule
Interval & Observed loss & Simulated loss & Observed rate & Simulated rate & Difference & Status \\
& \multicolumn{2}{c}{(trees $\mathrm{ha}^{-1}$)}
& \multicolumn{3}{c}{(\% $\mathrm{yr}^{-1}$)} & \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}"""


def comparison_matrix(rows: list[dict[str, str]]) -> dict[float, dict[str, dict[str, Any]]]:
    matrix: dict[float, dict[str, dict[str, Any]]] = {}
    for row in rows:
        age = as_float(row.get("requested_age"))
        observable = row.get("observable")
        if age is None or not observable:
            continue
        matrix.setdefault(age, {})[observable] = {
            "observed": as_float(row.get("observed_value")),
            "simulated": as_float(row.get("simulated_value")),
            "unit": row.get("unit", ""),
        }
    return matrix


def generate_s2(matrix: dict[float, dict[str, dict[str, Any]]]) -> str:
    body = []
    for age in sorted(matrix):
        d = matrix[age]
        values = [fmt_age(age)]
        for obs in ["N", "G", "Dm", "Dg", "sigma_D"]:
            values.extend([fmt(d.get(obs, {}).get("observed")), fmt(d.get(obs, {}).get("simulated"))])
        body.append(" & ".join(values) + r" \\ ")
    return r"""\begin{table}[htbp]
\centering
\scriptsize
\setlength{\tabcolsep}{3.2pt}
\caption{Complete age-by-age comparison for stand density, basal area, and DBH
variables. Subscripts $o$ and $s$ denote reported or derived observations and
simulated values, respectively.}
\label{tab:supp-density-diameter}
\begin{tabular}{rrrrrrrrrrr}
\toprule
Age & $N_o$ & $N_s$ & $G_o$ & $G_s$ & $D_{m,o}$ & $D_{m,s}$ & $D_{g,o}$ & $D_{g,s}$ & $\sigma_{D,o}$ & $\sigma_{D,s}$ \\
(yr) & \multicolumn{2}{c}{(trees $\mathrm{ha}^{-1}$)} & \multicolumn{2}{c}{($\mathrm{m}^2\,\mathrm{ha}^{-1}$)} & \multicolumn{6}{c}{(cm)} \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}"""


def generate_s3(matrix: dict[float, dict[str, dict[str, Any]]]) -> str:
    body = []
    for age in sorted(matrix):
        d = matrix[age]
        values = [fmt_age(age)]
        for obs in ["Hm", "H0", "H0_minus_Hm"]:
            values.extend([fmt(d.get(obs, {}).get("observed")), fmt(d.get(obs, {}).get("simulated"))])
        body.append(" & ".join(values) + r" \\ ")
    return r"""\begin{table}[htbp]
\centering
\small
\caption{Complete age-by-age comparison for height variables. Subscripts $o$
and $s$ denote reported or derived observations and simulated values,
respectively. Missing reported heights are retained as missing and are not
interpolated.}
\label{tab:supp-height}
\begin{tabular}{rrrrrrr}
\toprule
Age & $H_{m,o}$ & $H_{m,s}$ & $H_{0,o}$ & $H_{0,s}$ & $\Delta_{H,o}$ & $\Delta_{H,s}$ \\
(yr) & \multicolumn{6}{c}{(m)} \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}"""


def flatten_json(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_json(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            out.update(flatten_json(item, f"{prefix}.{index}"))
    else:
        out[prefix] = value
    return out


def find_value(flat: dict[str, Any], aliases: list[str]) -> Any:
    lowered = {key.lower(): value for key, value in flat.items()}
    for alias in aliases:
        alias_lower = alias.lower()
        exact = [value for key, value in lowered.items() if key == alias_lower or key.endswith("." + alias_lower)]
        if exact:
            return exact[0]
    for alias in aliases:
        alias_lower = alias.lower()
        partial = [value for key, value in lowered.items() if alias_lower in key]
        if partial:
            return partial[0]
    return None


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required JSON not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def generate_s4(payload: dict[str, Any], matrix: dict[float, dict[str, dict[str, Any]]]) -> str:
    initial = payload["initial_condition"]
    observable_rows = {
        row["observable"]: row for row in payload.get("observables", [])
    }

    def observed(name: str) -> float | None:
        return as_float(observable_rows.get(name, {}).get("observed_or_derived_value"))

    def simulated(name: str) -> float | None:
        return as_float(observable_rows.get(name, {}).get("simulated_value"))

    first_age = min(matrix)
    initial_comparison = matrix[first_age]
    target_h0 = initial_comparison.get("H0", {}).get("observed")
    reconstructed_h0 = as_float(payload.get("dominant_height_operator", {}).get("dominant_height_m"))
    target_hm = observed("Hm")
    reconstructed_hm = simulated("Hm")
    target_gap = None if target_h0 is None or target_hm is None else target_h0 - target_hm
    reconstructed_gap = None if reconstructed_h0 is None or reconstructed_hm is None else reconstructed_h0 - reconstructed_hm

    requested_rho = as_float(initial.get("requested_height_dbh_correlation"))
    effective_rho = as_float(initial.get("effective_height_dbh_correlation"))

    specs = [
        ("Total stem number $N$", r"trees $\mathrm{ha}^{-1}$", observed("N"), simulated("N")),
        ("Mean height $H_m$", "m", observed("Hm"), simulated("Hm")),
        ("Mean DBH $D_m$", "cm", observed("Dm"), simulated("Dm")),
        ("Quadratic mean DBH $D_g$", "cm", observed("Dg"), simulated("Dg")),
        (r"DBH standard deviation $\sigma_D$", "cm", observed("sigma_D"), simulated("sigma_D")),
        ("Dominant height $H_0$", "m", target_h0, reconstructed_h0),
        (r"Dominant-minus-mean height $\Delta_H$", "m", target_gap, reconstructed_gap),
        (r"Requested Gaussian correlation $\rho_{\mathrm{req}}$", "--", requested_rho, requested_rho),
        (r"Effective discrete correlation $\rho_{\mathrm{eff}}$", "--", requested_rho, effective_rho),
    ]

    body = []
    for label, unit, target, reconstructed in specs:
        absolute = None if target is None or reconstructed is None else reconstructed - target
        relative = None if target in (None, 0.0) or reconstructed is None else 100.0 * absolute / target
        body.append(" & ".join([
            label, unit, fmt(target, 8), fmt(reconstructed, 8),
            fmt(absolute, 5, signed=True), fmt(relative, 4, signed=True)
        ]) + r" \\ ")

    return r"""\begin{table}[htbp]
\centering
\scriptsize
\caption{Target values and reconstructed discrete quantities for the initial
joint distribution. Differences are reconstructed minus target values. For the
effective correlation, the requested Gaussian correlation is used as the
reference value.}
\label{tab:supp-initial-reconstruction}
\begin{tabular}{llrrrr}
\toprule
Quantity & Unit & Target & Reconstructed & Absolute difference & Relative difference (\%) \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}"""


def generate_s5(config: dict[str, Any], run: dict[str, Any], matrix: dict[float, dict[str, dict[str, Any]]]) -> str:
    height_scale = as_float(config.get("physical_scales", {}).get("height_scale"))
    dbh_scale = as_float(config.get("physical_scales", {}).get("dbh_scale"))
    grid = config.get("grid", {})
    time = config.get("time", {})
    model = config.get("model", {})
    solver = config.get("solver", {})

    t_start = as_float(time.get("t_start"))
    t_end = as_float(time.get("t_end"))
    n_steps = as_float(time.get("n_steps"))
    dt = None if t_start is None or t_end is None or not n_steps else (t_end - t_start) / n_steps

    first_age = min(matrix)
    last_age = max(matrix)
    initial_mass = matrix[first_age]["N"]["simulated"]
    final_mass = matrix[last_age]["N"]["simulated"]

    items = [
        ("Normalized domain", f"$[{grid.get('x_min', 0):g},{grid.get('x_max', 1):g}]\\times[{grid.get('y_min', 0):g},{grid.get('y_max', 1):g}]$"),
        ("Physical height scale", fmt(height_scale, 2) + " m"),
        ("Physical DBH scale", fmt(dbh_scale, 2) + " m"),
        ("Numerical nodes", f"${grid.get('nx', 40)}\\times{grid.get('ny', 40)}$"),
        ("Simulation period", fmt((t_end - t_start) if t_start is not None and t_end is not None else None, 2) + " yr"),
        ("Number of time steps", f"{int(n_steps):,}" if n_steps is not None else r"\NA"),
        ("Time step", fmt(dt, 6) + " yr"),
        ("Height-growth physical rate", fmt(model.get("height_growth", {}).get("physical_rate"), 4) + " m yr$^{-1}$"),
        ("DBH-growth physical rate", fmt(model.get("dbh_growth", {}).get("physical_rate"), 4) + " m yr$^{-1}$"),
        ("Diffusion coefficient", fmt(model.get("diffusion", {}).get("value"), 8) + " normalized$^2$ yr$^{-1}$"),
        ("Mortality coefficient", fmt(model.get("mortality", {}).get("value"), 4) + " yr$^{-1}$"),
        ("Quadrature", "Tensor-product trapezoidal rule"),
        ("Transport", "First-order upwind, explicit"),
        ("Diffusion and mortality", "Implicit in density"),
        ("Linear solver", latex_escape(solver.get("linear_solver", ""))),
        ("Zero-mass regularization", f"{as_float(solver.get('epsilon_zero_mass')):.1e}"),
        ("Positivity tolerance", f"{as_float(solver.get('positivity_tolerance')):.1e}"),
        ("Dominant-height operator", r"Continuous upper-DBH-tail functional containing 100 trees $\mathrm{ha}^{-1}$"),
        ("Initial discrete mass", fmt(initial_mass, 4) + r" trees $\mathrm{ha}^{-1}$"),
        ("Final discrete mass", fmt(final_mass, 4) + r" trees $\mathrm{ha}^{-1}$"),
        ("Full horizon completed", "yes" if run.get("completed_full_horizon") else "no"),
    ]
    body = [label + " & " + value + r" \\ " for label, value in items]
    return r"""\begin{table}[htbp]
\centering
\small
\caption{Numerical configuration and selected implementation checks for the
reported experiment.}
\label{tab:supp-numerical-configuration}
\begin{tabular}{ll}
\toprule
Item & Value \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
\end{table}"""


def discover_json(directory: Path, patterns: list[str]) -> Path:
    for pattern in patterns:
        matches = sorted(directory.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No JSON matching {patterns} under {directory}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", default="outputs/article_simulation/observations_simulation.csv")
    parser.add_argument("--mortality", default="outputs/article_mortality_intervals/mortality_intervals.csv")
    parser.add_argument("--initial-manifest")
    parser.add_argument("--run-metadata")
    parser.add_argument("--config-metadata")
    parser.add_argument("--output-dir", default="outputs/article_supplementary/tables")
    args = parser.parse_args()

    comparison_path = Path(args.comparison)
    mortality_path = Path(args.mortality)
    output_dir = Path(args.output_dir)

    initial_path = Path(args.initial_manifest) if args.initial_manifest else discover_json(
        Path("outputs"), ["**/*initial*manifest*.json", "**/*initial*condition*.json"]
    )
    run_path = Path(args.run_metadata) if args.run_metadata else discover_json(
        Path("outputs/article_simulation"), ["*metadata*.json", "*reproducibility*.json"]
    )
    config_path = Path(args.config_metadata) if args.config_metadata else Path("outputs/article_simulation/configuration.json")

    mortality_rows = read_csv(mortality_path)
    comparison_rows = read_csv(comparison_path)
    matrix = comparison_matrix(comparison_rows)
    initial_payload = load_json(initial_path)
    run_payload = load_json(run_path)
    config_payload = load_json(config_path)

    outputs = {
        "table_S1_stem_loss.tex": generate_s1(mortality_rows),
        "table_S2_density_diameter.tex": generate_s2(matrix),
        "table_S3_height.tex": generate_s3(matrix),
        "table_S4_initial_reconstruction.tex": generate_s4(initial_payload, matrix),
        "table_S5_numerical_configuration.tex": generate_s5(config_payload, run_payload, matrix),
    }
    for name, text in outputs.items():
        write(output_dir / name, text)

    summary = {
        "comparison_csv": str(comparison_path),
        "mortality_csv": str(mortality_path),
        "initial_manifest": str(initial_path),
        "run_metadata": str(run_path),
        "config_metadata": str(config_path),
        "n_comparison_rows": len(comparison_rows),
        "n_ages": len(matrix),
        "n_intervals": len(mortality_rows),
        "generated_files": list(outputs),
    }
    write(output_dir.parent / "supplementary_table_generation.json", json.dumps(summary, indent=2))

    if len(matrix) != 15:
        raise RuntimeError(f"Expected 15 inventory ages, found {len(matrix)}")
    if len(mortality_rows) != 14:
        raise RuntimeError(f"Expected 14 inventory intervals, found {len(mortality_rows)}")

    print("[OK] generated Tables S1--S5")
    for name in outputs:
        print(output_dir / name)


if __name__ == "__main__":
    main()
