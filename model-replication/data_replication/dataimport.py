import numpy as np
import pandas as pd
import os

def load_data(data_dir=None) -> dict:
    '''
    Load all data files for Factor Zoo analysis.
    '''
    if data_dir is None:
        data_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load factor data
    allfactors = pd.read_csv(os.path.join(data_dir, 'factors.csv'))
    date = allfactors.iloc[:, 0].values
    rf = allfactors.iloc[:, 1].values
    factors = allfactors.iloc[:, 2:].values
    
    L = len(date)
    P = factors.shape[1]
    
    # Load test portfolios
    port_3x2 = pd.read_csv(os.path.join(data_dir, 'port_3x2.csv'), header=None)
    port_3x2 = port_3x2.iloc[:, 1:].values
    port_3x2 = port_3x2 - rf[:, np.newaxis]
    
    # Load other information
    summary = pd.read_csv(os.path.join(data_dir, 'summary.csv'), index_col=0)
    factorname = summary.index.tolist()
    factorname_full = summary['Descpription'].tolist()
    year_pub = summary['Year'].values
    year_end = summary['Year_end'].values
    port_3x2_id = pd.read_csv(os.path.join(data_dir, 'port_3x2_id.csv'))
    
    # Form a smaller set of portfolios for bivariate sorted portfolios
    kk = 10  # minimum number of stocks in a portfolio
    
    include_3x2 = np.where(port_3x2_id['min_stk6'].values >= kk)[0]
    port_3x2b = []
    
    for i in range(P):
        if i in include_3x2:
            start_idx = i * 6
            end_idx = (i + 1) * 6
            port_3x2b.append(port_3x2[:, start_idx:end_idx])
    
    if port_3x2b:
        port_3x2b = np.hstack(port_3x2b)
    else:
        port_3x2b = np.array([]).reshape(L, 0)
    
    return {
        'date': date,
        'rf': rf,
        'factors': factors,
        'L': L,
        'P': P,
        'port_3x2': port_3x2,
        'port_3x2b': port_3x2b,
        'summary': summary,
        'factorname': factorname,
        'factorname_full': factorname_full,
        'year_pub': year_pub,
        'year_end': year_end,
        'port_3x2_id': port_3x2_id,
        'include_3x2': include_3x2,
    }

if __name__ == "__main__":
    # Test data loading
    data = load_data()
    print(f"Loaded {data['P']} factors over {data['L']} time periods")
    print(f"port_3x2b shape: {data['port_3x2b'].shape}")