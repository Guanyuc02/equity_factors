import numpy as np
import pandas as pd
import sys
import os
import functools
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.dataimport import load_data
from functions.DS import DS

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken: {end_time - start_time} seconds")
        return result
    return wrapper

@timer
def main():
    seed_num = 100
    np.random.seed(seed_num)
    
    # Load data
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    data = load_data(data_dir)
    
    date = data['date']
    rf = data['rf']
    factors = data['factors']
    L = data['L']
    P = data['P']
    
    # Use filtered 3x2 portfolios (already filtered in data loader)
    port_3x2b = data['port_3x2b']
    Ri = port_3x2b.T  # Transpose to (n, T)
    
    factorname = data['factorname']
    factorname_full = data['factorname_full']
    year_pub = data['year_pub']
    
    print(f"   Loaded {P} factors over {L} time periods")
    print(f"   Test portfolios shape: {Ri.shape}")
    
    print("\n2. Loading tuning parameters...")
    tune_file_csv = os.path.join(os.path.dirname(__file__), 'tune_main_py.csv')
    
    if os.path.exists(tune_file_csv):
        tune_df = pd.read_csv(tune_file_csv)
        tune_center = tune_df[['lambda1', 'lambda2']].values
        print(f"   Loaded tune_center from CSV with shape {tune_center.shape}")
    else:
        print(f"   WARNING: {tune_file_csv} not found!")
        print("   Will use default tuning parameters (may differ from original results)")
        tune_center = None
    
    # Choose control factors (published before 2012)
    ContrlList = np.where(year_pub < 2012)[0]
    ControlFactor = factors[:, ContrlList]
    
    # Test factors (published since 2012)
    TestList = np.where(year_pub >= 2012)[0]
    TestFactor = factors[:, TestList]
    
    print(f"\n3. Testing {len(TestList)} factors using {len(ContrlList)} control factors")
    print()
    
    results = []
    

    # Test each factor individually
    for j, test_idx in enumerate(TestList):
        
        gt = TestFactor[:, j].reshape(1, -1)  # Test factor (1, T)
        ht = ControlFactor.T  # Control factors (p, T)
        
        # Get tuning parameters for this factor
        if tune_center is not None:
            # This matches MATLAB: DS(Ri', gt, ht, -log(tune_center(j,1)), -log(tune_center(j,2)), ...)
            tune1 = -np.log(tune_center[j, 0])
            tune2 = -np.log(tune_center[j, 1])
        else:
            print("Warning: tune_main.mat is missing.")
            break
        
        try:
            model_ds = DS(Ri, gt, ht, tune1, tune2, alpha=1.0, seednum=seed_num)
            tstat_ds = model_ds['lambdag_ds'][0] / model_ds['se_ds'][0]
            lambda_ds = model_ds['gamma_ds'][0]
            
        except Exception as e:
            print(f"\n   DS failed: {e}")
            import traceback
            traceback.print_exc()
            tstat_ds = np.nan
            lambda_ds = np.nan
        
        # Store results
        results.append({
            'TestList': test_idx + 1,  # 1-indexed like MATLAB
            'factornames': factorname_full[test_idx],
            'lambda_ds': lambda_ds * 10000,  # Convert to bps
            'tstat_ds': tstat_ds,
        })
    
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 70)
    print("RESULTS TABLE")
    print("=" * 70)
    print("\nColumn descriptions:")
    print("  lambda_ds            : Risk price estimates (basis points)")
    print("  tstat_ds             : t-statistics (Python implementation)")
    print()
    print(results_df.to_string(index=False))
    
    output_file = os.path.join(os.path.dirname(__file__), 'main.csv')
    results_df.to_csv(output_file, index=False)
    print(f"\n{'=' * 70}")
    print(f"Results saved to: {output_file}")
    print("=" * 70)
    
    return results_df

if __name__ == "__main__":
    results = main()
