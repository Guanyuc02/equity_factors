"""
Quick test script to verify Python replication installation.
"""

import sys
import os

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing package imports...")
    
    packages = {
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'sklearn': 'scikit-learn',
        'statsmodels': 'statsmodels',
        'matplotlib': 'Matplotlib',
        'scipy': 'SciPy',
        'joblib': 'joblib'
    }
    
    failed = []
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            failed.append(name)
    
    if failed:
        print(f"\nMissing packages: {', '.join(failed)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✓ All packages installed successfully!")
    return True


def test_data_loading():
    """Test that data can be loaded."""
    print("\nTesting data loading...")
    
    try:
        from data.dataimport import load_data
        
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        data = load_data(data_dir)
        
        print(f"  ✓ Loaded {data['P']} factors")
        print(f"  ✓ Loaded {data['L']} time periods")
        print(f"  ✓ port_3x2b shape: {data['port_3x2b'].shape}")
        print(f"  ✓ port_5x5b shape: {data['port_5x5b'].shape}")
        print(f"  ✓ port_202 shape: {data['port_202'].shape}")
        
        print("\n✓ Data loading successful!")
        return True
        
    except Exception as e:
        print(f"  ✗ Data loading failed: {e}")
        return False


def test_functions():
    """Test that core functions work."""
    print("\nTesting core functions...")
    
    try:
        import numpy as np
        from functions.PriceRisk_OLS import PriceRisk_OLS
        
        # Create small test data
        np.random.seed(42)
        n, T, p = 10, 50, 5
        Ri = np.random.randn(n, T) * 0.01
        gt = np.random.randn(1, T) * 0.01
        ht = np.random.randn(p, T) * 0.01
        
        # Test OLS
        result = PriceRisk_OLS(Ri, gt, ht)
        print(f"  ✓ PriceRisk_OLS: lambda = {result['lambdag_ols'][0]:.6f}")
        
        # Test DS (quick version)
        from functions.DS import DS
        result_ds = DS(Ri, gt, ht, tune1=3.0, tune2=3.0, alpha=1.0, seednum=100)
        print(f"  ✓ DS: lambda = {result_ds['lambdag_ds'][0]:.6f}")
        print(f"  ✓ DS: selected {len(result_ds['select'])} factors")
        
        print("\n✓ Core functions working!")
        return True
        
    except Exception as e:
        print(f"  ✗ Function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Factor Zoo Python Replication - Installation Test")
    print("="*60)
    print()
    
    tests = [
        ("Package Imports", test_imports),
        ("Data Loading", test_data_loading),
        ("Core Functions", test_functions)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(success for _, success in results)
    
    print("="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("\nYou can now run the main analysis scripts:")
        print("  cd main && python main.py")
        print("  cd main && python plot_figure1.py")
        print("  cd robustness && python robustness.py")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease fix the issues above before running the analysis.")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

