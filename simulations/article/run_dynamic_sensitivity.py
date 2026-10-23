# SPDX-License-Identifier: LGPL-3.0-or-later
"""Run selected Q-9E local dynamic-parameter sensitivity cases."""

from __future__ import annotations

import argparse

from simulations.article.dynamic_sensitivity import selected_dynamic_sensitivity_cases
from simulations.article.q9d_full_run import run_q9d_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--q9c-root", default="outputs/article_initial_copula")
    parser.add_argument("--output-root", default="outputs/article_scenarios")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    cases = selected_dynamic_sensitivity_cases(args.q9c_root)
    available = {case.name: case for case in cases}
    if args.list:
        for case in cases:
            print(
                f"{case.name}: {case.parameter} "
                f"{case.baseline_value:.10g} -> {case.perturbed_value:.10g}"
            )
        return

    names = args.case or list(available)
    unknown = [name for name in names if name not in available]
    if unknown:
        raise SystemExit(f"Unknown case(s): {unknown}. Use --list.")

    for name in names:
        case = available[name]
        result = run_q9d_scenario(
            case.scenario,
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
