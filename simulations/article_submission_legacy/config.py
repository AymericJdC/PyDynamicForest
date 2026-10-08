# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Central configuration for the manuscript-associated legacy scenario.

This module records the numerical, contextual and initial-condition settings
from the Modele2DImpliciteV3.py script transmitted by Aymeric Jacob de Cordemoy.

The goal is not yet to provide a fully generic configuration system, but to
avoid scattering core scenario values across several files.
"""

from copy import deepcopy

ARTICLE_SUBMISSION_CONFIG = {
    "name": "article_submission_legacy",
    "description": (
        "Manuscript-associated legacy scenario transcribed from "
        "Modele2DImpliciteV3.py. The scenario runs from stand age 18 to "
        "stand age 69 on a 40 x 40 normalized height-DBH grid."
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
        "name": "article_submission_gaussian_initial_condition",
        "mass_target": 1924.34,
        "distribution_kind": "gaussian_2d",
        "source": "manuscript_associated_legacy_script",

        # Physical Gaussian parameters before normalization.
        # Height is in meters, DBH is in meters.
        "h0_physical": 9.61,
        "d0_physical": 0.1169,
        "sigma_h_physical": 1.3,
        "sigma_d_physical": 0.025,
    },

    # ------------------------------------------------------------------
    # Physical scales used to normalize height and DBH
    # ------------------------------------------------------------------
    "physical_scales": {
        "height_scale": 50.0,
        "dbh_scale": 1.0,
    },

    # ------------------------------------------------------------------
    # Numerical grid
    # ------------------------------------------------------------------
    "grid": {
        "nx": 40,
        "ny": 40,
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
        "n_steps": 10000,
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
            "value": 0.033,
        },
        "height_growth": {
            "name": "linear_height_growth",
            "physical_rate": 1.66,
        },
        "dbh_growth": {
            "name": "linear_dbh_growth",
            "physical_rate": 0.0155,
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
        "scheme_name": "legacy_semi_implicit_sparse_article_submission",
        "matrix_storage": "sparse",
        "linear_solver": "scipy.sparse.linalg.spsolve",
        "model_field_evaluation": "legacy",
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
    Return a deep copy of the article-submission configuration.

    This is useful for creating scenario variants without mutating
    the global article-submission configuration.
    """

    return deepcopy(ARTICLE_SUBMISSION_CONFIG)

def make_article_submission_config():
    """
    Return the default baseline reduced configuration.
    """

    return copy_baseline_config()


def make_short_debug_config():
    """
    Return a lightweight article-submission configuration for fast debugging.

    This preset uses a smaller grid and fewer time steps while preserving
    the same model structure.
    """

    config = copy_baseline_config()

    config["name"] = "baseline_short_debug"
    config["description"] = (
        "Short debug version of the baseline reduced scenario."
    )

    config["grid"]["nx"] = 10
    config["grid"]["ny"] = 10

    config["time"]["t_end"] = 2.0
    config["time"]["n_steps"] = 20

    config["ages"]["final_age"] = (
        config["ages"]["initial_age"] + config["time"]["t_end"]
    )

    config["output"]["observation_ages"] = [
        config["ages"]["initial_age"],
        config["ages"]["initial_age"] + 1.0,
        config["ages"]["final_age"],
    ]

    return config


def make_dense_debug_config():
    """
    Return a lightweight dense-solver debug configuration.

    This preset is intended for regression checks and debugging only.
    The dense solver should not be used for practical large simulations.
    """

    config = make_short_debug_config()

    config["name"] = "baseline_dense_debug"
    config["description"] = (
        "Dense-solver debug version of the baseline reduced scenario."
    )

    config["solver"]["scheme_name"] = "legacy_semi_implicit_dense_debug"
    config["solver"]["matrix_storage"] = "dense"
    config["solver"]["linear_solver"] = "numpy.linalg.solve"

    return config

def make_state_debug_config() -> dict:
    """
    Return a lightweight state-aware debug configuration.

    This preset is based on the short debug configuration but uses the
    state-aware model-field evaluation pathway.

    It is intended for testing and future model-law development. It should
    not be considered the default validated production pathway.
    """

    config = make_short_debug_config()

    config["name"] = "baseline_state_debug"
    config["description"] = (
        "State-aware debug version of the baseline reduced scenario."
    )

    config["solver"]["model_field_evaluation"] = "state"

    return config

ARTICLE_SUBMISSION_PRESET_BUILDERS = {
    "article-submission": make_article_submission_config,
    "short-debug": make_short_debug_config,
    "dense-debug": make_dense_debug_config,
    "state-debug": make_state_debug_config,
}


def available_baseline_presets():
    """
    Return the list of available article-submission configuration presets.
    """

    return sorted(ARTICLE_SUBMISSION_PRESET_BUILDERS.keys())


def build_baseline_config_from_preset(preset):
    """
    Build a article-submission configuration from a preset name.
    """

    if preset not in ARTICLE_SUBMISSION_PRESET_BUILDERS:
        available = ", ".join(available_baseline_presets())
        raise ValueError(
            f"Unknown baseline preset: {preset}. "
            f"Available presets are: {available}."
        )

    builder = ARTICLE_SUBMISSION_PRESET_BUILDERS[preset]
    return builder()
