import csv
import json

import numpy as np
import pytest

from simulations.article_submission_legacy.full_run import (
    run_article_submission_legacy,
)


@pytest.mark.slow
def test_complete_article_submission_legacy_reference(tmp_path):
    result = run_article_submission_legacy(
        output_dir=tmp_path,
        progress=False,
    )

    final_state = result["final_state"]
    metadata = json.loads(
        (tmp_path / "metadata.json").read_text(encoding="utf-8")
    )

    with (tmp_path / "time_series_legacy.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        rows = list(csv.DictReader(stream))

    assert len(rows) == 10001
    assert final_state.step_index == 10000
    assert final_state.age == pytest.approx(69.0, abs=2.0e-11)
    assert metadata["n_steps_run"] == 10000
    assert metadata["observation_files"] == {
        "18": "state_age_18.npz",
        "45": "state_age_44p9994.npz",
        "69": "state_age_69.npz",
    }

    final = rows[-1]
    assert int(final["step_index"]) == 10000
    assert float(final["legacy_mass"]) == pytest.approx(
        681.8466446739574, rel=1.0e-10, abs=1.0e-8
    )
    assert float(final["trapezoidal_mass"]) == pytest.approx(
        682.5634212614714, rel=1.0e-10, abs=1.0e-8
    )
    assert float(final["legacy_top_height"]) == pytest.approx(
        40.55836824826789, rel=1.0e-10, abs=1.0e-8
    )
    assert float(final["top_height_current"]) == pytest.approx(
        39.645023020989214, rel=1.0e-10, abs=1.0e-8
    )
    assert float(final["basal_area"]) == pytest.approx(
        88.56315851136009, rel=1.0e-10, abs=1.0e-8
    )
    assert int(final["threshold_dbh_index"]) == 22
    assert min(float(row["minimum_density"]) for row in rows) >= 0.0

    state_45 = np.load(tmp_path / "state_age_44p9994.npz")
    assert int(state_45["step_index"]) == 5294
    assert float(state_45["age"]) == pytest.approx(44.9994, abs=1.0e-10)
