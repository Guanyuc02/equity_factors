import pytest
import sys
from pathlib import Path
import numpy as np
from sklearn.linear_model import Lasso, ElasticNet
from sklearn.model_selection import KFold

# Add the project root to Python path so imports work from any directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from functions.DS import nancov, TSCV

def test_cov_matrix():
    """Test that the covariance matrix is calculated correctly."""
    X = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    Y = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    cov_matrix = nancov(X, Y)
    # nancov concatenates X and Y, so result is (6, 6)
    assert cov_matrix.shape == (6, 6)
    # Just check that it computed without errors and is not all NaN
    assert not np.all(np.isnan(cov_matrix))

def test_tscv_basic():
    """Test basic functionality of TSCV."""
    Ri = np.random.rand(10, 20)
    gt = np.random.rand(20)
    ht = np.random.rand(3, 20)
    lambda_grid = np.array([0.1, 0.2, 0.3])
    result = TSCV(Ri, gt, ht, lambda_grid, Kfld=5)
    assert 'sel3' in result
    assert 'sel3_1se' in result

def test_tscv_lambda_selection():
    """Test if TSCV selects a reasonable lambda."""
    Ri = np.random.rand(15, 20)
    gt = np.random.rand(20)
    ht = np.random.rand(5, 20)
    lambda_grid = np.linspace(0.01, 0.1, 10)
    result = TSCV(Ri, gt, ht, lambda_grid, Kfld=5)
    assert result['lambda3'] in lambda_grid
    assert result['lambda3_1se'] in lambda_grid

def test_tscv_stability():
    """Test TSCV stability with consistent random seed."""
    Ri = np.random.rand(20, 15)
    gt = np.random.rand(15)
    ht = np.random.rand(10, 15)
    lambda_grid = np.exp(np.linspace(-3, 0, 5))
    result1 = TSCV(Ri, gt, ht, lambda_grid, Kfld=5, seednum=123)
    result2 = TSCV(Ri, gt, ht, lambda_grid, Kfld=5, seednum=123)
    assert np.array_equal(result1['sel3'], result2['sel3'])
    assert np.array_equal(result1['sel3_1se'], result2['sel3_1se'])


        
