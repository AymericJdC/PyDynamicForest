# SPDX-License-Identifier: LGPL-3.0-or-later
"""Published Écouves A5 dataset: export and reading back."""

import math

import pandas as pd

from studies.ecouves_a5 import heights
from studies.ecouves_a5.dataset import TREE_COLUMNS, tree_inventories


def test_measured_heights_round_trip(tmp_path):
    c = [69.0, 58.0, 101.3, 87.7]
    measured = pd.DataFrame({
        "plot": ["A1", "A1", "A5", "A5"], "tree_id": ["2", "3", "12", "40"], "year": [1985, 1985, 2016, 2020],
        "circumference_cm": c, "height_m": [23.1, 23.63, 35.27, 38.1],
        "origin": ["GIS_hauteur_ech", "GIS_hauteur_ech", "Francois_Ht16", "Francois_Ht20"],
    })
    path = tmp_path / "ecouves_measured_heights.csv"
    measured.to_csv(path, index=False)
    back = heights.read_measured_heights(path)
    assert list(back.tree_id) == ["2", "3", "12", "40"]
    assert list(back.dbh_cm) == [x / math.pi for x in c]
    assert list(back.height_m) == list(measured.height_m)


def test_tree_inventories_copy_values_verbatim(tmp_path):
    header = ("site,plot,tree_id,year,age,series_status,circumference_cm,diameter_cm,status,has_measurement,"
              "included_in_reference_state,inclusion_rule,plot_area_ha,expansion_factor_ha\n")
    rows = [
        "Ecouves,Ecouves A5,1,1985,37,reference,74.0,23.55493157760051,rest,True,True,rest_only,0.1216,8.223684210526315\n",
        "Ecouves,Ecouves A5,2,1985,37,reference,,,,False,False,rest_only,0.1216,8.223684210526315\n",
        "Ecouves,Ecouves A5,1,1990,42,audit,80.0,25.464790894703256,rest,True,False,rest_only,0.1216,8.223684210526315\n",
        "Ecouves,Ecouves A5,3,1985,37,reference,61.0,19.41690305721124,sec,True,False,rest_only,0.1216,8.223684210526315\n",
    ]
    src = tmp_path / "inventory_long.csv"
    src.write_text(header + "".join(rows))
    out = tree_inventories(src, [1985, 1992])
    assert list(out.columns) == list(TREE_COLUMNS)
    assert list(out.tree_id) == ["1", "3"]
    assert list(out.diameter_cm) == ["23.55493157760051", "19.41690305721124"]
