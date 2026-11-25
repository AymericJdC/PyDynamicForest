# SPDX-License-Identifier: LGPL-3.0-or-later
"""Run the Écouves A5 study of the JoMB article.

Usage, from the repository root::

    python -m studies.ecouves_a5.run_all --data-dir DATA --output-dir OUT

Steps, in order (each reads the outputs of the previous ones in OUT, so a run
can be resumed with ``--from``):

    heights       complete missing heights            -> heights/
    regularise    regularised observations            -> regularised/
    calibrate     sequential calibration of K, c_phi  -> calibration/
    simulate      trajectory 1985-2020                -> simulation/
    completion    sensitivity to height completion    -> completion/
    bootstrap     sampling uncertainty of observations -> bootstrap/
    sensitivity   grid study and height-status exponent (long) -> sensitivity/
    figures       figures 1 to 3                      -> figures/

``sensitivity`` runs only with ``--with-sensitivity``; ``calibrate`` re-estimates
the parameters only if ``[calibration] enabled = true`` or ``--recalibrate``,
otherwise it records the values of ``[model]``. A ``manifest.json`` in OUT
records the configuration, the git commit, the library versions, the input
checksums and the outputs of every step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import bootstrap as bootstrap_mod
from . import completion as completion_mod
from . import heights as heights_mod
from .calibration import calibrate
from .dynamics import comparison_rows, mean_status, simulate_inventories, summarize
from .regularise import regularise_inventory
from .settings import DEFAULT_CONFIG, StudyConfig, build_parameters, load_config

STEPS = ("heights", "regularise", "calibrate", "simulate", "completion", "bootstrap", "sensitivity", "figures")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout.strip()
        return out.stdout.strip() + ("-dirty" if dirty else "")
    except Exception:
        return None


class Pipeline:
    def __init__(self, config: StudyConfig, output_dir: Path, grid_nodes: int | None = None, log=print):
        self.config = config
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.grid_nodes = int(grid_nodes or config.model["grid_nodes"])
        self.log = log
        self.manifest_path = self.out / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text()) if self.manifest_path.exists() else {}
        self.manifest.update({
            "study": "Ecouves A5 (JoMB article)",
            "config_file": str(config.path),
            "config": config.raw,
            "grid_nodes": self.grid_nodes,
            "git_commit": git_commit(),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        })
        self.manifest.setdefault("steps", {})

    # ------------------------------------------------------------------ utils
    def dir(self, name: str) -> Path:
        d = self.out / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def parameters(self, grid_nodes: int | None = None, **changes):
        values = {**self.config.model, **self.calibrated(), **changes}
        return build_parameters(grid_nodes or self.grid_nodes, values["mortality"], values["dbh_growth_rate"],
                                values["height_growth_rate"], values.get("diffusion_scale", 1.0))

    def calibrated(self) -> dict:
        path = self.out / "calibration" / "parameters.json"
        if path.exists():
            data = json.loads(path.read_text())
            return {"mortality": data["mortality"], "dbh_growth_rate": data["dbh_growth_rate"]}
        return {}

    def assigned(self) -> pd.DataFrame:
        return heights_mod.read_assigned_heights(self.out / "heights" / "assigned_heights.csv")

    def load_states(self, folder: str, prefix: str) -> dict[int, np.ndarray]:
        states = {}
        for year in self.config.years:
            with np.load(self.out / folder / f"{prefix}_{year}.npz") as z:
                states[year] = np.array(z["U"])
        return states

    def record(self, step: str, outputs: list[Path], started: float, **extra) -> None:
        self.manifest["steps"][step] = {
            "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "seconds": round(time.time() - started, 1),
            "outputs": {str(p.relative_to(self.out)): sha256(p) for p in outputs if p.is_file()},
            **extra,
        }
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False, default=float) + "\n")

    # ------------------------------------------------------------------ steps
    def heights(self) -> None:
        t0 = time.time()
        c = self.config
        out = self.dir("heights")
        inputs = {}
        prepared = c.data_path("assigned_heights")
        if prepared is not None:
            assigned = heights_mod.read_assigned_heights(prepared)
            inputs["assigned_heights"] = sha256(prepared)
            summary = None
            self.log(f"heights: using the prepared table {prepared}")
        else:
            paths = {k: c.data_path(k) for k in ("inventory_long", "gis", "francois")}
            for k, path in paths.items():
                if path is None or not path.is_file():
                    raise FileNotFoundError(f"[data] {k}: {path}")
                inputs[k] = sha256(path)
            hc = c.section("heights")
            population = heights_mod.read_population(paths["inventory_long"], c.years)
            measured = pd.concat([
                heights_mod.read_gis_measured_heights(paths["gis"], hc["plot_codes"]),
                heights_mod.read_francois_measured_heights(paths["francois"], list(hc["plot_codes"])),
            ], ignore_index=True)
            source = {int(k): int(v) for k, v in hc["allometry_source_year"].items()}
            assigned, summary = heights_mod.complete_heights(population, measured, source, hc["minimum_sample"])
        expected = c.raw["data"].get("sha256", {})
        mismatches = {k: v for k, v in inputs.items() if k in expected and expected[k] != v}
        assigned.to_csv(out / "assigned_heights.csv", index=False)
        outputs = [out / "assigned_heights.csv"]
        if summary is not None:
            summary.to_csv(out / "completion_summary.csv", index=False)
            outputs.append(out / "completion_summary.csv")
        if mismatches:
            self.log(f"heights: WARNING input checksums differ from the article inputs: {sorted(mismatches)}")
        self.record("heights", outputs, t0, inputs=inputs, checksum_mismatches=sorted(mismatches))

    def regularise(self) -> None:
        t0 = time.time()
        rc = self.config.section("regularisation")
        p = self.parameters()
        assigned = self.assigned()
        out = self.dir("regularised")
        outputs, rows = [], []
        for year in self.config.years:
            U = regularise_inventory(assigned, year, p, rc["half_width_height_m"], rc["half_width_dbh_cm"])
            path = out / f"observed_state_{year}.npz"
            np.savez_compressed(path, U=U, year=year)
            outputs.append(path)
            rows.append({"year": year, **summarize(U, p), "mean_status": mean_status(U, p)})
        pd.DataFrame(rows).to_csv(out / "observed_summary.csv", index=False)
        outputs.append(out / "observed_summary.csv")
        self.record("regularise", outputs, t0)

    def calibrate(self, force: bool = False) -> None:
        t0 = time.time()
        cc = self.config.section("calibration")
        out = self.dir("calibration")
        m = self.config.model
        if cc.get("enabled", False) or force:
            observed = self.load_states("regularised", "observed_state")
            result = calibrate(
                observed[self.config.initial_year], observed, self.config.ages,
                lambda K, cphi: build_parameters(self.grid_nodes, K, cphi, m["height_growth_rate"], m.get("diffusion_scale", 1.0)),
                m["mortality"], m["dbh_growth_rate"], cc["passes"], cc["relative_bracket"], cc["relative_tolerance"],
                m.get("linear_solver", "cg"), self.log)
            pd.DataFrame(result.pop("history")).to_csv(out / "history.csv", index=False)
            result["source"] = "calibrated"
        else:
            result = {"mortality": m["mortality"], "dbh_growth_rate": m["dbh_growth_rate"], "source": "config [model]"}
        (out / "parameters.json").write_text(json.dumps(result, indent=2) + "\n")
        self.record("calibrate", sorted(out.iterdir()), t0, **result)

    def simulate(self) -> None:
        t0 = time.time()
        p = self.parameters()
        observed = self.load_states("regularised", "observed_state")
        out = self.dir("simulation")
        every = max(1, int(round(0.5 / p.numerics.time.dt)))
        states, series = simulate_inventories(observed[self.config.initial_year], p, self.config.ages,
                                              self.config.model.get("linear_solver", "cg"), record_every=every,
                                              progress=self._progress("simulate"))
        outputs = []
        for year, U in states.items():
            path = out / f"simulated_state_{year}.npz"
            np.savez_compressed(path, U=U, year=year)
            outputs.append(path)
        pd.DataFrame(series).to_csv(out / "time_series.csv", index=False)
        pd.DataFrame(comparison_rows(states, observed, p)).to_csv(out / "comparison.csv", index=False)
        outputs += [out / "time_series.csv", out / "comparison.csv"]
        self.record("simulate", outputs, t0, dt=p.numerics.time.dt)

    def completion(self) -> None:
        t0 = time.time()
        p = self.parameters()
        rows = completion_mod.completion_sensitivity(self.assigned(), self.load_states("simulation", "simulated_state"),
                                                     p, self.config.initial_year)
        out = self.dir("completion")
        pd.DataFrame(rows).to_csv(out / "completion_sensitivity.csv", index=False)
        self.record("completion", [out / "completion_sensitivity.csv"], t0)

    def bootstrap(self) -> None:
        t0 = time.time()
        bc = self.config.section("bootstrap")
        rc = self.config.section("regularisation")
        out = self.dir("bootstrap")
        samples = bootstrap_mod.bootstrap_diagnostics(
            self.assigned(), self.config.years, self.parameters(), rc["half_width_height_m"], rc["half_width_dbh_cm"],
            int(bc["replicates"]), int(bc["seed"]), progress=self._progress("bootstrap"))
        samples.to_csv(out / "bootstrap_samples.csv.gz", index=False)
        comparison = pd.read_csv(self.out / "simulation" / "comparison.csv")
        table = bootstrap_mod.percentile_intervals(samples, comparison, float(bc["level"]))
        table.to_csv(out / "bootstrap_intervals.csv", index=False)
        self.record("bootstrap", [out / "bootstrap_samples.csv.gz", out / "bootstrap_intervals.csv"], t0,
                    replicates=int(bc["replicates"]), seed=int(bc["seed"]))

    def sensitivity(self) -> None:
        t0 = time.time()
        sc = self.config.section("sensitivity")
        rc = self.config.section("regularisation")
        assigned = self.assigned()
        out = self.dir("sensitivity")
        solver = self.config.model.get("linear_solver", "cg")
        grid = {}
        for n in sc["grid_nodes"]:
            q = self.parameters(grid_nodes=n)
            obs = {y: regularise_inventory(assigned, y, q, rc["half_width_height_m"], rc["half_width_dbh_cm"]) for y in self.config.years}
            sim, _ = simulate_inventories(obs[self.config.initial_year], q, self.config.ages, solver)
            grid[n] = {"simulated": {y: summarize(sim[y], q) for y in sim}, "observed": {y: summarize(obs[y], q) for y in obs}}
            self.log(f"sensitivity: grid {n} done")
            (out / "grid_study.json").write_text(json.dumps(grid, indent=1, default=float))
        p = self.parameters()
        observed = self.load_states("regularised", "observed_state")
        gamma = {}
        for g in sc["height_status_exponents"]:
            sim, _ = simulate_inventories(observed[self.config.initial_year], p, self.config.ages, solver, height_status_exponent=g)
            gamma[g] = {y: summarize(sim[y], p) for y in sim}
            self.log(f"sensitivity: height-status exponent {g} done")
            (out / "height_status_sensitivity.json").write_text(json.dumps(gamma, indent=1, default=float))
        self.record("sensitivity", sorted(out.iterdir()), t0)

    def figures(self) -> None:
        t0 = time.time()
        from .figures import YEARS, make_figures

        if tuple(YEARS) != self.config.years:
            raise ValueError("the figures are laid out for the five article inventories")
        files = make_figures(self.out / "regularised", self.out / "simulation", self.dir("figures"),
                             self.parameters(), usetex=self.config.section("figures").get("usetex", False))
        self.record("figures", files, t0)

    def _progress(self, step: str):
        last = [0.0]

        def report(k: int, total: int) -> None:
            now = time.time()
            if now - last[0] > 60 or k == total:
                last[0] = now
                self.log(f"{step}: step {k}/{total}")

        return report

    def run(self, steps, recalibrate: bool = False) -> None:
        for step in steps:
            self.log(f"== {step}")
            if step == "calibrate":
                self.calibrate(force=recalibrate)
            else:
                getattr(self, step)()


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--from", dest="start", choices=STEPS, default=STEPS[0])
    parser.add_argument("--to", dest="stop", choices=STEPS, default=STEPS[-1])
    parser.add_argument("--grid-nodes", type=int, default=None, help="override [model] grid_nodes (quick checks)")
    parser.add_argument("--recalibrate", action="store_true")
    parser.add_argument("--with-sensitivity", action="store_true", help="run the long grid and exponent studies")
    args = parser.parse_args(argv)

    config = load_config(args.config, args.data_dir)
    steps = list(STEPS[STEPS.index(args.start):STEPS.index(args.stop) + 1])
    if not args.with_sensitivity and "sensitivity" in steps:
        steps.remove("sensitivity")
    Pipeline(config, args.output_dir, args.grid_nodes).run(steps, recalibrate=args.recalibrate)


if __name__ == "__main__":
    main()
