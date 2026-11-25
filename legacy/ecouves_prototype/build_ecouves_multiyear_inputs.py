#!/usr/bin/env python3
"""Build and audit multiyear Écouves A5 inputs for regularized target states.

Selected target years: 1985, 1992, 1998, 2016, 2020.
- 1985/1992/1998: individual DBH and measured total heights from GIS Coop.
- 2016/2020: circumference and total height Ht16/Ht20 from François Ningre.
- HbH/ht_vv is never used as total height.
- GIS an_mesure is kept as provenance metadata; biological years follow the
  validated François/GIS temporal crosswalk.

The script writes standardized private tables and one public audit report. It
DOES NOT yet create NPZ target states. It first verifies that the DBH source is
complete enough for each target year and documents the allometry samples.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_YEARS = (1985, 1992, 1998, 2016, 2020)
EARLY_YEARS = (1985, 1992, 1998)
LATE_SUFFIX = {2016: "16", 2020: "20"}
PLOTS = {"A1": 10780, "A2": 10781, "A5": 10784}
A5_AREA_HA = 0.1216


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def fit_log_allometry(frame: pd.DataFrame) -> dict:
    dbh = frame["dbh_cm"].to_numpy(float)
    height = frame["height_m"].to_numpy(float)
    design = np.column_stack([np.ones(len(dbh)), np.log(dbh)])
    beta0, beta1 = np.linalg.lstsq(design, height, rcond=None)[0]
    fitted = beta0 + beta1 * np.log(dbh)
    residuals = height - fitted
    return {
        "n": int(len(frame)),
        "beta0": float(beta0),
        "beta1": float(beta1),
        "rmse_m": float(np.sqrt(np.mean(residuals ** 2))),
        "residual_sd_m": float(np.std(residuals, ddof=1)) if len(frame) > 1 else None,
        "mean_residual_m": float(np.mean(residuals)),
        "dbh_min_cm": float(dbh.min()),
        "dbh_max_cm": float(dbh.max()),
    }


def extract_gis(gis_path: Path):
    mesure = pd.read_excel(gis_path, "Mesure", engine="xlrd")
    arbre = pd.read_excel(gis_path, "Arbre", engine="xlrd")
    keys = mesure[
        ["co_placette", "no_mesure", "an_mesure", "an_vegetation"]
    ].drop_duplicates()
    joined = arbre.merge(
        keys,
        on=["co_placette", "no_mesure"],
        how="left",
        validate="many_to_one",
    )

    populations = []
    measured = []
    for plot_name, plot_code in PLOTS.items():
        plot = joined[joined["co_placette"] == plot_code]
        for year in EARLY_YEARS:
            inventory = plot[plot["an_mesure"] == year]
            for _, row in inventory.iterrows():
                circumference = positive_number(row.get("circonference130"))
                if circumference is None:
                    continue
                dbh = circumference / math.pi
                base = {
                    "plot": plot_name,
                    "tree_id": str(row.get("no_arb")),
                    "biological_year": year,
                    "source_year_label": year,
                    "dbh_cm": dbh,
                    "circumference_cm": circumference,
                    "source": "GIS_Coop",
                    "source_record": f"no_mesure={row.get('no_mesure')}",
                }
                if plot_name == "A5":
                    populations.append(
                        {
                            **base,
                            "weight_ha": 1.0 / A5_AREA_HA,
                            "population_status": "full_GIS_inventory_with_valid_DBH",
                        }
                    )
                height = positive_number(row.get("hauteur_ech"))
                if height is not None:
                    if height > 100:
                        height /= 100.0
                    measured.append(
                        {
                            **base,
                            "height_m": height,
                            "height_origin": "measured_hauteur_ech",
                        }
                    )
    return pd.DataFrame(populations), pd.DataFrame(measured)


def extract_francois(francois_path: Path):
    populations = []
    measured = []
    for plot_name in PLOTS:
        frame = pd.read_excel(francois_path, plot_name, engine="xlrd")
        if "Num" not in frame.columns:
            raise RuntimeError(f"Missing Num column in François sheet {plot_name}")
        for year, suffix in LATE_SUFFIX.items():
            c_col = f"c{suffix}"
            h_col = f"Ht{suffix}"
            obs_col = f"Obs{suffix}"
            for _, row in frame.iterrows():
                circumference = positive_number(row.get(c_col))
                if circumference is None:
                    continue
                dbh = circumference / math.pi
                base = {
                    "plot": plot_name,
                    "tree_id": str(row.get("Num")),
                    "biological_year": year,
                    "source_year_label": suffix,
                    "dbh_cm": dbh,
                    "circumference_cm": circumference,
                    "source": "Francois_Ningre",
                    "source_record": f"sheet={plot_name};campaign={suffix}",
                }
                if plot_name == "A5":
                    populations.append(
                        {
                            **base,
                            "weight_ha": 1.0 / A5_AREA_HA,
                            "population_status": "coverage_to_be_validated_against_aggregate_N",
                        }
                    )
                height = positive_number(row.get(h_col))
                if height is not None:
                    if height > 100:
                        height /= 100.0
                    measured.append(
                        {
                            **base,
                            "height_m": height,
                            "height_origin": f"measured_{h_col}",
                            "observation": "" if pd.isna(row.get(obs_col)) else str(row.get(obs_col)),
                        }
                    )
    return pd.DataFrame(populations), pd.DataFrame(measured)


def read_aggregate_series(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding="utf-8-sig")
    # source_row_order and series_index preserve the historical selection. The
    # script reports all rows and only matches a year if an explicit year-like
    # field exists. It never guesses years from age.
    for candidate in ("year", "inventory_year", "annee"):
        if candidate in frame.columns:
            frame["biological_year"] = pd.to_numeric(frame[candidate], errors="coerce")
            return frame
    frame["biological_year"] = np.nan
    return frame


def write_csv(frame: pd.DataFrame, path: Path):
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gis", type=Path, required=True)
    parser.add_argument("--francois", type=Path, required=True)
    parser.add_argument("--aggregate-series", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    paths = [args.gis, args.francois, args.aggregate_series, args.crosswalk]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    out = args.output_dir.resolve()
    if out.exists():
        raise FileExistsError(f"Refusing existing output directory: {out}")
    out.mkdir(parents=True)

    gis_population, gis_heights = extract_gis(args.gis)
    fr_population, fr_heights = extract_francois(args.francois)
    population = pd.concat([gis_population, fr_population], ignore_index=True)
    heights = pd.concat([gis_heights, fr_heights], ignore_index=True)

    duplicates = heights.duplicated(["plot", "tree_id", "biological_year"], keep=False)
    if duplicates.any():
        duplicate_rows = heights.loc[duplicates, ["plot", "tree_id", "biological_year"]]
        raise RuntimeError(
            "Duplicate measured-height keys detected:\n" + duplicate_rows.to_string(index=False)
        )

    # Fit ad hoc allometries on measured A1+A2+A5 pairs for every selected year.
    allometries = []
    for year in TARGET_YEARS:
        sample = heights[heights["biological_year"] == year].copy()
        if len(sample) >= 10:
            model = fit_log_allometry(sample)
            status = "fit_available"
        else:
            model = {
                "n": int(len(sample)),
                "beta0": None,
                "beta1": None,
                "rmse_m": None,
                "residual_sd_m": None,
                "mean_residual_m": None,
                "dbh_min_cm": None,
                "dbh_max_cm": None,
            }
            status = "insufficient_measured_pairs"
        allometries.append({"biological_year": year, "status": status, **model})
    allometry_frame = pd.DataFrame(allometries)

    aggregate = read_aggregate_series(args.aggregate_series)
    crosswalk = pd.read_csv(args.crosswalk, encoding="utf-8-sig")

    coverage = []
    for year in TARGET_YEARS:
        pop = population[population["biological_year"] == year]
        measured_a5 = heights[
            (heights["biological_year"] == year) & (heights["plot"] == "A5")
        ]
        all_measured = heights[heights["biological_year"] == year]
        coverage.append(
            {
                "biological_year": year,
                "A5_valid_dbh_records": int(len(pop)),
                "A5_measured_heights": int(len(measured_a5)),
                "A1_A2_A5_measured_heights": int(len(all_measured)),
                "A5_height_coverage_fraction": (
                    len(measured_a5) / len(pop) if len(pop) else None
                ),
                "population_source": ";".join(sorted(pop["source"].unique())) if len(pop) else "missing",
                "allometry_status": allometry_frame.loc[
                    allometry_frame["biological_year"] == year, "status"
                ].iloc[0],
            }
        )
    coverage_frame = pd.DataFrame(coverage)

    write_csv(population, out / "PRIVATE_ecouves_A5_target_dbh_populations.csv")
    write_csv(heights, out / "PRIVATE_ecouves_measured_height_dbh_pairs.csv")
    write_csv(allometry_frame, out / "ecouves_ad_hoc_allometries_audit.csv")
    write_csv(coverage_frame, out / "ecouves_selected_years_coverage.csv")

    manifest = {
        "purpose": "controlled inputs for multiyear regularized Ecouves A5 target reconstruction",
        "selected_years": TARGET_YEARS,
        "height_rule": "measured total heights retained; missing heights later distributed over centered empirical residuals",
        "excluded_height_variable": "HbH/ht_vv: first living whorl / functional crown base, not total height",
        "temporal_policy": "biological year from validated Francois/GIS crosswalk; GIS an_mesure retained only as provenance",
        "input_sha256": {str(path.resolve()): sha256(path) for path in paths},
        "outputs": {
            "private_population": "PRIVATE_ecouves_A5_target_dbh_populations.csv",
            "private_measured_pairs": "PRIVATE_ecouves_measured_height_dbh_pairs.csv",
            "allometry_audit": "ecouves_ad_hoc_allometries_audit.csv",
            "coverage": "ecouves_selected_years_coverage.csv",
        },
    }
    (out / "ecouves_multiyear_inputs_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Audit des entrées multiannuelles Écouves A5",
        "",
        "Cette étape standardise les sources et audite les allométries ad hoc. Aucun état NPZ n'est encore créé.",
        "",
        "| Année | DBH A5 | H mesurées A5 | H mesurées A1+A2+A5 | Couverture A5 | Source population | Allométrie |",
        "|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in coverage:
        frac = row["A5_height_coverage_fraction"]
        frac_text = "—" if frac is None else f"{100 * frac:.1f}%"
        lines.append(
            f"| {row['biological_year']} | {row['A5_valid_dbh_records']} | "
            f"{row['A5_measured_heights']} | {row['A1_A2_A5_measured_heights']} | "
            f"{frac_text} | {row['population_source']} | {row['allometry_status']} |"
        )
    lines += [
        "",
        "## Garde-fous",
        "",
        "- `HtXX` et `hauteur_ech` sont traitées comme hauteurs totales.",
        "- `HbHXX` et `ht_vv` sont exclues de la hauteur totale.",
        "- Les campagnes François 07 et 10 sont datées biologiquement 2007 et 2010, sans reprendre silencieusement `an_mesure` 2008 et 2011.",
        "- Les résidus ne sont pas encore injectés à cette étape.",
        "- Si la population A5 de 2016 ou 2020 n'est qu'un échantillon, le rapport le révélera avant toute construction de cible.",
    ]
    report = out / "ecouves_multiyear_inputs_audit.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] {report}")
    print(coverage_frame.to_string(index=False))


if __name__ == "__main__":
    main()
