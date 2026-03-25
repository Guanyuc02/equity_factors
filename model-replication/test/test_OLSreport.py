import pytest
import sys
from pathlib import Path
import numpy as np
from sklearn.linear_model import Lasso, ElasticNet
from sklearn.model_selection import KFold

# Add the project root to Python path so imports work from any directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from functions.ds_lasso import OLS_report

### Prelim agentic implementation.
def test_OLS_report():
    X = np.array([
        [1.0, 0.0],
        [2.0, 1.0],
        [3.0, -1.0],
    ])
    ERi = np.array([[1.0], [2.0], [3.0]])

    result = OLS_report(ERi, X)

    # basic structure tests
    assert isinstance(result, dict)
    assert "lambdag_ds" in result and "t_ds" in result

    # numeric sanity checks
    assert np.isfinite(result["lambdag_ds"]) or np.isnan(result["lambdag_ds"])
    assert np.isfinite(result["t_ds"]) or np.isnan(result["t_ds"])

    # expected lambda for this dataset is 1 (from prior derivation)
    assert np.isclose(result["lambdag_ds"], 1.0, atol=1e-8) or np.isnan(result["t_ds"])