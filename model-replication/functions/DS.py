import numpy as np
from glmnet import ElasticNet as GLMElasticNet

def nancov(X):
    '''
    Mimic MATLAB nancov for [X', Y'] input usage in this code
    '''
    X = np.asarray(X, dtype=float)
    mask = ~np.isnan(X).any(axis=1)
    if mask.sum() == 0:
        return np.full((X.shape[1], X.shape[1]), np.nan)
    return np.cov(X[mask].T)

def _glmnet_fit(X, y, family="gaussian", intr=True, standardize=True, lambda_path=None, alpha=1.0):
    '''
    Used to obtain the beta path and lambda path from the glmnet model.
    '''

    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).ravel()

    if lambda_path is None:
        lambda_path = None
    else:
        lambda_path = np.asarray(lambda_path, dtype=float).ravel().tolist()

    # Key: disable internal CV/scoring to prevent fit() from calling
    # _score_lambda_path → predict → squeeze, which would raise an error
    try:
        mdl = GLMElasticNet(
            alpha=alpha,
            lambda_path=lambda_path,
            fit_intercept=intr,
            standardize=standardize,
            tol=1e-7,
            max_iter=100000,
            n_splits=0,      # ← Disable internal KFold CV (some versions require 0/1 to skip CV)
            scoring=None,    # ← Disable scoring
            n_jobs=1,
            verbose=0,
        )
    except TypeError:
        # Backward compatibility: if these parameters are not supported,
        # initialize without them; we still won't call predict afterwards
        mdl = GLMElasticNet(
            alpha=alpha,
            lambda_path=lambda_path,
            fit_intercept=intr,
            standardize=standardize,
            tol=1e-7,
            max_iter=100000,
        )

    mdl.fit(X, y)

    # Retrieve the full coefficient path: shape (p x L)
    if hasattr(mdl, "coef_path_"):
        beta = np.asarray(mdl.coef_path_)
    elif hasattr(mdl, "coef_"):
        beta = np.asarray(mdl.coef_).reshape(-1, 1)
    else:
        raise RuntimeError("glmnet model has no coef_path_ / coef_.")

    # Retrieve lambda path
    if hasattr(mdl, "lambda_path_"):
        lam = np.asarray(mdl.lambda_path_).ravel()
    elif lambda_path is not None:
        lam = np.asarray(lambda_path, dtype=float).ravel()
    else:
        lam = np.array([])

    # Intercept path (only used in step 1/2)
    if hasattr(mdl, "intercept_path_"):
        a0 = np.asarray(mdl.intercept_path_).ravel()
    elif hasattr(mdl, "intercept_"):
        a0 = np.array([float(mdl.intercept_)])
    else:
        a0 = np.zeros(beta.shape[1])

    return {"beta": beta, "lambda": lam, "a0": a0}

def TSCV(Ri, gt, ht, lambda_grid, Kfld, Jrep, alpha, seednum):
    '''
    Used to perform time-series cross-validation for the 3rd selection.
    '''
    if seednum is None:
        seednum = 101

    p, T = ht.shape
    L = len(lambda_grid)

    cvm3 = np.full((L, Kfld, Jrep), np.nan)
    cvm33_list = []

    nomissing = (np.sum(np.isnan(np.vstack([ht, gt.reshape(1, -1)])), axis=0) == 0)

    for j in range(Jrep):
        rng = np.random.RandomState(seednum + j)
        indices = np.arange(T)
        rng.shuffle(indices)
        folds = np.array_split(indices, Kfld)

        for k in range(Kfld):
            test_mask = np.zeros(T, dtype=bool)
            test_mask[folds[k]] = True
            train_mask = ~test_mask

            # train uses (train & nomissing), test uses original 'test'
            ht_train = ht[:, train_mask & nomissing]
            gt_train = gt[train_mask & nomissing]

            ht_test = ht[:, test_mask]
            gt_test = gt[test_mask]

            model3 = _glmnet_fit(
                ht_train.T, gt_train,
                family="gaussian",
                intr=False,
                standardize=True,
                lambda_path=lambda_grid,
                alpha=alpha
            )

            B = model3["beta"]  # shape (p, L)
            gt_pred = ht_test.T @ B  # (n_test, L)

            LL3 = B.shape[1]
            if gt_test.size > 0:
                diff = gt_test.reshape(-1, 1) - gt_pred
                mse_cols = np.nanmean(diff * diff, axis=0)  # (L,)
                cvm3[0:LL3, k, j] = mse_cols.reshape(-1)
            # else leave as NaN (same effect as MATLAB nanmean over empty)

        cvm33_list.append(cvm3[:, :, j])

    cvm33 = np.concatenate(cvm33_list, axis=1)  # (L, Kfld*Jrep)
    cv_sd3 = np.std(cvm33, axis=1, ddof=0) / np.sqrt(Kfld * Jrep)
    cvm333 = np.nanmean(cvm33, axis=1)
    l_sel3 = int(np.nanargmin(cvm333))

    cvm33ub = cvm333[l_sel3] + cv_sd3[l_sel3]
    left = cvm333[: l_sel3 + 1]
    idx = np.where(left >= cvm33ub)[0]
    if idx.size == 0:
        l3_1se = l_sel3
    else:
        l3_1se = int(idx[-1])

    # refit on all data with both lambdas [l3_1se, l_sel3]
    lam_refit = [lambda_grid[l3_1se], lambda_grid[l_sel3]]
    model3_all = _glmnet_fit(
        ht[:, nomissing].T, gt[nomissing],
        family="gaussian",
        intr=False,
        standardize=True,
        lambda_path=lam_refit,
        alpha=alpha
    )

    B_all = model3_all["beta"]  # (p, 2)
    sel3 = np.where(B_all[:, 1] != 0)[0]
    sel3_1se = np.where(B_all[:, 0] != 0)[0]

    return {
        "sel3": sel3,
        "lambda3": float(lambda_grid[l_sel3]),
        "sel3_1se": sel3_1se,
        "lambda3_1se": float(lambda_grid[l3_1se]),
    }


def infer(Ri, gt, ht, sel1, sel2, sel3):
    '''
    Used to perform estimation and inference for the DS method.
    '''
    n = Ri.shape[0]
    p = ht.shape[0]
    if gt.ndim == 1:
        gt = gt.reshape(1, -1)
    d = gt.shape[0]

    tmp1 = nancov(np.vstack([gt, Ri]).T)
    cov_g = tmp1[d:, :d]
    tmp2 = nancov(np.vstack([ht, Ri]).T)
    cov_h = tmp2[p:, :p]

    ER = np.mean(Ri, axis=1)

    M0 = np.eye(n) - np.ones((n, 1)) @ np.linalg.inv(np.ones((1, n)) @ np.ones((n, 1))) @ np.ones((1, n))

    nomissing = np.where(np.sum(np.isnan(np.vstack([ht, gt])), axis=0) == 0)[0]
    Lnm = len(nomissing)
    select = np.union1d(sel1, sel2)

    if select.size > 0:
        X = np.column_stack([cov_g, cov_h[:, select.astype(int)]])
    else:
        X = cov_g

    lambda_full = np.linalg.inv(X.T @ M0 @ X) @ (X.T @ M0 @ ER)
    lambdag = lambda_full[:d]

    # For double selection inference: AVAR
    zthat = np.full((d, Lnm), np.nan)
    for i in range(d):
        if sel3.size > 0:
            H = ht[sel3.astype(int)[:, None], :][:, :, nomissing].reshape(len(sel3), Lnm)
            M_mdl = np.eye(Lnm) - H.T @ np.linalg.inv(H @ H.T) @ H
        else:
            M_mdl = np.eye(Lnm)
        zthat[i, :] = (M_mdl @ gt[i, nomissing])

    Sigmazhat = zthat @ zthat.T / Lnm

    temp2 = np.zeros((d, d))
    ii = 0
    for l in nomissing:
        ii += 1
        if select.size > 0:
            vec = np.concatenate([gt[:d, l], ht[select.astype(int), l]])
        else:
            vec = gt[:d, l]
        mt = 1 - lambda_full @ vec
        temp2 = temp2 + mt ** 2 * (np.linalg.inv(Sigmazhat) @ (zthat[:, ii - 1][:, None] @ zthat[:, ii - 1][None, :]) @ np.linalg.inv(Sigmazhat))

    avar_lambdag = np.diag(temp2) / Lnm
    se = np.sqrt(avar_lambdag / Lnm)

    # scaled lambda for DS
    if select.size > 0:
        vt = np.vstack([gt[:, nomissing], ht[select.astype(int), :][:, nomissing]])
    else:
        vt = gt[:, nomissing]
    V_bar = vt - np.mean(vt, axis=1, keepdims=True)
    var_v = V_bar @ V_bar.T / Lnm
    gamma = np.diag(var_v) * lambda_full

    return {"lambdag": lambdag, "se": se, "gamma": gamma}


def DS(Ri, gt, ht, tune1, tune2, alpha=1.0, seednum=None):
    '''
    Used to perform the DS method (no CV in 1st and 2nd selections).
    '''
    if alpha is None:
        alpha = 1.0 # Lasso

    n, T = Ri.shape
    p = ht.shape[0]
    if gt.ndim == 1:
        gt = gt.reshape(1, -1)
    d = gt.shape[0]

    tmp1 = nancov(np.vstack([gt, Ri]).T)
    cov_g = tmp1[d:, :d]
    tmp2 = nancov(np.vstack([ht, Ri]).T)
    cov_h = tmp2[p:, :p]

    ER = np.nanmean(Ri, axis=1)

    beta = np.full((n, p), np.nan)
    for i in range(p):
        beta[:, i] = cov_h[:, i] / np.nanvar(ht[i, :])
    penalty = np.nanmean(beta ** 2, axis=0)
    penalty = penalty / np.nanmean(penalty)  # normalize the level

    lambda0 = np.exp(np.linspace(0, -35, 100))

    # 1st selection in cross-sectional regression
    lam1 = float(np.exp(-tune1))
    X1 = cov_h * penalty
    model1 = _glmnet_fit(
        X1, ER,
        family="gaussian",
        intr=True,
        standardize=False,
        lambda_path=[lam1],
        alpha=alpha
    )

    if model1["a0"].size > 0:
        a0_1 = float(model1["a0"][0])
    else:
        a0_1 = 0.0
    b1 = model1["beta"][:, 0]
    sel1 = np.where(b1 != 0)[0]
    err1 = np.mean((ER - (a0_1 + X1 @ b1)) ** 2)

    # 2nd selection
    sel2_list = []
    err2 = np.full(d, np.nan)
    lam2 = float(np.exp(-tune2))
    for i in range(d):
        model2 = _glmnet_fit(
            X1, cov_g[:, i],
            family="gaussian",
            intr=True,
            standardize=False,
            lambda_path=[lam2],
            alpha=alpha
        )
        if model2["a0"].size > 0:
            a0_2 = float(model2["a0"][0])
        else:
            a0_2 = 0.0
        b2 = model2["beta"][:, 0]
        sel2_list.extend(np.where(b2 != 0)[0].tolist())
        err2[i] = np.mean((cov_g[:, i] - (a0_2 + X1 @ b2)) ** 2)
    sel2 = np.unique(np.array(sel2_list, dtype=int))

    # 3rd selection for avar zt
    sel3_all = []
    for i in range(d):
        TSCVout = TSCV(Ri, gt[i, :], ht, lambda0, 10, 1, alpha, seednum if seednum is not None else 101)
        sel3_all.extend(TSCVout["sel3_1se"].tolist())
    sel3 = np.unique(np.array(sel3_all, dtype=int))

    # post-selection estimation and inference
    dsout = infer(Ri, gt, ht, sel1, sel2, sel3)
    ssout = infer(Ri, gt, ht, sel1, np.array([], dtype=int), sel3)

    # outputs
    result = {
        "lambdag_ds": dsout["lambdag"],
        "se_ds": dsout["se"],
        "gamma_ds": dsout["gamma"],
        "sel1": sel1,
        "sel2": sel2,
        "sel3": sel3,
        "select": np.union1d(sel1, sel2).astype(int),
        "err1": err1,
        "err2": err2,
    }
    return result