#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def repository_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [Path.cwd(), *Path.cwd().parents, *here.parents]:
        if (candidate / 'simulations/article/ecouves_a5').exists():
            return candidate
    raise RuntimeError('cannot locate repository root')


ROOT = repository_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulations.article.ecouves_a5.hierarchical_height_diagnostics import (
    YEARS,
    run_hierarchical_diagnostics,
)


def write_csv(path: Path, rows) -> None:
    rows = list(rows)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--simulated-dir',
        type=Path,
        default=ROOT / 'outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020',
    )
    parser.add_argument(
        '--target-dir',
        type=Path,
        default=ROOT / 'outputs/article_scenarios/ecouves_a5_solver_compatibility',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=ROOT / 'outputs/article_scenarios/ecouves_a5_height_hierarchy',
    )
    args = parser.parse_args(argv)

    profiles, comparisons = run_hierarchical_diagnostics(
        args.simulated_dir,
        args.target_dir,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / 'ecouves_a5_height_hierarchy_profiles.csv', profiles)
    write_csv(args.output_dir / 'ecouves_a5_height_hierarchy_comparison.csv', comparisons)

    indexed = {
        (row['year'], row['hierarchy_class']): row
        for row in comparisons
    }
    lines = [
        '# Q-9F.5 - Diagnostic hiérarchique de la structure en hauteur',
        '',
        'Les classes reposent sur le diamètre relatif D/Dg de chaque état. '
        'Les résultats comparent des instantanés eulériens et ne constituent pas '
        'des trajectoires individuelles de croissance.',
        '',
        '| Année | Classe | Écart part de densité | Écart hauteur moyenne (m) | '
        'Écart contribution à Hm (m) |',
        '|---:|:---|---:|---:|---:|',
    ]
    for year in YEARS[1:]:
        for label in (
            'very_suppressed',
            'suppressed',
            'subordinate',
            'co_dominant',
            'dominant',
            'very_dominant',
        ):
            row = indexed[(year, label)]
            lines.append(
                f"| {year} | {label} | "
                f"{row['density_share_difference']:+.5f} | "
                f"{row['mean_height_difference_m']:+.4f} | "
                f"{row['height_contribution_difference']:+.4f} |"
            )
    lines.extend(
        [
            '',
            'La cible en hauteur reste issue du fournisseur provisoire. '
            'Aucun paramètre dynamique ou allométrique n’est ajusté.',
            '',
        ]
    )
    (args.output_dir / 'ecouves_a5_height_hierarchy_report.md').write_text(
        '\n'.join(lines),
        encoding='utf-8',
    )
    print(f'Q-9F.5 outputs written to {args.output_dir}')


if __name__ == '__main__':
    main()
