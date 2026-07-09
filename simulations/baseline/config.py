# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Central configuration for the baseline reduced scenario.

This module gathers the main numerical, contextual and initial-condition
settings used by the baseline scenario.

The goal is not yet to provide a fully generic configuration system, but to
avoid scattering core scenario values across several files.
"""

from copy import deepcopy

BASELINE_CONFIG = {
    "name": "baseline_reduced",
    "description": (
        "Baseline reduced scenario corresponding to the reduced legacy "
        "reference case. The scenario runs from stand age 18 to stand age 69 "
        "on a 20 x 20 normalized height-DBH grid."
    ),

    # ------------------------------------------------------------------
    # Stand age and simulation horizon
    # ------------------------------------------------------------------
    "ages": {
        "initial_age": 18.0,
        "final_age": 69.0,
    },

    # ------------------------------------------------------------------
    # Initial condition
    # ------------------------------------------------------------------
    "initial_condition": {
        "name": "baseline_gaussian_initial_condition",
        "mass_target": 2154.6,
        "distribution_kind": "gaussian_2d",
        "source": "reduced_legacy_reference",

        # Physical Gaussian parameters before normalization.
        # Height is in meters, DBH is in meters.
        "h0_physical": 10.50887557,
        "d0_physical": 0.1176045686,
        "sigma_h_physical": 1.5,
        "sigma_d_physical": 0.04,
    },

    # ------------------------------------------------------------------
    # Physical scales used to normalize height and DBH
    # ------------------------------------------------------------------
    "physical_scales": {
        "height_scale": 50.0,
        "dbh_scale": 0.9,
    },

    # ------------------------------------------------------------------
    # Numerical grid
    # ------------------------------------------------------------------
    "grid": {
        "nx": 20,
        "ny": 20,
        "x_min": 0.0,
        "x_max": 1.0,
        "y_min": 0.0,
        "y_max": 1.0,
    },

    # ------------------------------------------------------------------
    # Time discretization
    # ------------------------------------------------------------------
    "time": {
        "t_start": 0.0,
        "t_end": 51.0,
        "n_steps": 1000,
    },

    # ------------------------------------------------------------------
    # Model coefficients
    # ------------------------------------------------------------------
    "model": {
        "diffusion": {
            "name": "constant_diffusion",
            "value": 0.00001,
        },
        "mortality": {
            "name": "constant_mortality",
            "value": 0.0365,
        },
        "height_growth": {
            "name": "linear_height_growth",
            "physical_rate": 1.78,
        },
        "dbh_growth": {
            "name": "linear_dbh_growth",
            "physical_rate": 0.0135,
        },
        "status": {
            "name": "cumulative_status",
            "description": "Status based on the normalized cumulative distribution.",
        },
    },

    # ------------------------------------------------------------------
    # Numerical solver configuration
    # ------------------------------------------------------------------
    "solver": {
        "scheme_name": "legacy_semi_implicit_sparse_reduced",
        "matrix_storage": "sparse",
        "linear_solver": "scipy.sparse.linalg.spsolve",
        "epsilon_zero_mass": 1e-15,
        "positivity_tolerance": 1e-12,
    },

    # ------------------------------------------------------------------
    # Output / observation configuration
    # ------------------------------------------------------------------
    "output": {
        "observation_ages": [18.0, 45.0, 69.0],
        "save_full_trajectory": False,
        "compute_time_series": True,
        "save_figures": False,
        "save_tables": False,
    },
}

def copy_baseline_config() -> dict:
    """
    Return a deep copy of the baseline configuration.

    This is useful for creating scenario variants without mutating
    the global baseline configuration.
    """

    return deepcopy(BASELINE_CONFIG)