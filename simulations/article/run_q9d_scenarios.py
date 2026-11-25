# SPDX-License-Identifier: LGPL-3.0-or-later
"""Command-line runner for the six selected Q-9D article scenarios."""

from __future__ import annotations

import argparse
from pathlib import Path

from simulations.article.q9d_full_run import run_q9d_scenario
from simulations.article.scenarios import selected_q9d_scenarios


def _scenario_map(q9c_root: str | Path):
    scenarios = selected_q9d_scenarios(q9c_root=q9c_root)
    return {scenario.name: scenario for scenario in scenarios}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        action="append",
        help="Scenario name to run; repeat the option for several scenarios.",
    )
    parser.add_argument(
        "--q9c-root",
        default="outputs/article_initial_copula",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/article_scenarios",
    )
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    available = _scenario_map(args.q9c_root)
    if args.list:
        for name in available:
            print(name)
        return

    selected_names = args.scenario or list(available)
    unknown = [name for name in selected_names if name not in available]
    if unknown:
        raise SystemExit(
            f"Unknown scenario(s): {unknown}. Use --list to show valid names."
        )

    for name in selected_names:
        result = run_q9d_scenario(
            available[name],
            output_root=args.output_root,
            max_steps=args.max_steps,
            progress=not args.no_progress,
            overwrite=args.overwrite,
        )
        metadata = result["metadata"]
        print(
            f"{name}: steps={metadata['steps_run']} "
            f"final_age={metadata['final_age_reached']:.9f} "
            f"output={result['paths']['metadata'].parent.resolve()}"
        )


if __name__ == "__main__":
    main()
