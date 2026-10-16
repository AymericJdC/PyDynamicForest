from copy import deepcopy

import pytest

from simulations.article.config import ARTICLE_CONFIG
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG


def test_article_configuration_is_separate_from_historical_reproduction():
    historical = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    assert ARTICLE_CONFIG is not ARTICLE_SUBMISSION_CONFIG
    assert ARTICLE_CONFIG["name"] == "article"
    assert ARTICLE_CONFIG["initial_condition"]["height_dbh_correlation"] == pytest.approx(
        0.8490113967
    )
    assert "height_dbh_correlation" not in ARTICLE_SUBMISSION_CONFIG["initial_condition"]
    assert ARTICLE_SUBMISSION_CONFIG == historical
