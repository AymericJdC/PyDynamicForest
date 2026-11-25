# SPDX-License-Identifier: LGPL-3.0-or-later
"""Run the numerical simulation retained for the manuscript."""

from pydynamicforest.solver import simulate
from simulations.article.context import build_context
from simulations.article.initial_condition import build_initial_condition
from simulations.article.parameters import build_parameters


def run_article_simulation(max_steps: int | None = None, solver_name: str = "sparse"):
    """Return simulation results without writing publication outputs."""
    return simulate(
        build_initial_condition(),
        build_parameters(),
        build_context(),
        max_steps=max_steps,
        solver_name=solver_name,
    )


def main() -> None:
    results = run_article_simulation()
    state = results.final_state
    print(f"final_time: {state.time}")
    print(f"final_age: {state.age}")
    print(f"steps: {state.step_index}")


if __name__ == "__main__":
    main()
