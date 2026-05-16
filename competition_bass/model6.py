# m(t)为减法型的竞争模型
# # competition_bass_fit.py
# import numpy as np
# import pandas as pd
# from scipy.optimize import least_squares
# from scipy.stats import t as tdist

# # ----------------- 配置 -----------------
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# BTC_CUM = "btc_cum_users"
# BTC_NEW = "btc_new_developers"
# ETH_CUM = "eth_cum_users"
# ETH_NEW = "eth_new_developers"
# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"
# # -----------------------------------------

# def load_df():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df.loc[(df[DATE_COL] >= START_DATE) & (df[DATE_COL] <= END_DATE)].copy()
#     df = df.sort_values(DATE_COL).reset_index(drop=True)
#     # fill
#     df[[BTC_CUM, BTC_NEW, ETH_CUM, ETH_NEW]] = df[[BTC_CUM, BTC_NEW, ETH_CUM, ETH_NEW]].fillna(0)
#     return df

# # Bass instantaneous given N, p,q,m (m allowed array)
# def bass_instant(N, p, q, m):
#     m = np.asarray(m)
#     rem = np.maximum(m - N, 0)
#     return (p + q * (N / (m + 1e-12))) * rem

# # compute m_B(t), m_E(t) with simple subtractive competition
# def compute_m_t(N_other, m0, gamma):
#     m_t = m0 - gamma * N_other
#     # safety: ensure m_t > current observed N_other (or > min positive)
#     m_t = np.maximum(m_t, 1.0)
#     return m_t

# # residuals: stack btc_resids then eth_resids
# def residuals(params, df):
#     # params: [pB,qB,mB0,gBE,  pE,qE,mE0,gEB]
#     pB,qB,mB0,gBE, pE,qE,mE0,gEB = params
#     N_B = df[BTC_CUM].values
#     N_E = df[ETH_CUM].values
#     # compute time-varying m
#     mB_t = compute_m_t(N_E, mB0, gBE)
#     mE_t = compute_m_t(N_B, mE0, gEB)
#     # predicted instantaneous (dN/dt)
#     dB_pred = bass_instant(N_B, pB, qB, mB_t)
#     dE_pred = bass_instant(N_E, pE, qE, mE_t)
#     # observed instantaneous: use NEW columns (if integer daily counts)
#     dB_obs = df[BTC_NEW].values
#     dE_obs = df[ETH_NEW].values
#     # residual vectors (we can scale them to balance magnitudes)
#     # scale by std to avoid one series dominating:
#     sB = np.std(dB_obs) if np.std(dB_obs)>0 else 1.0
#     sE = np.std(dE_obs) if np.std(dE_obs)>0 else 1.0
#     rB = (dB_obs - dB_pred) / sB
#     rE = (dE_obs - dE_pred) / sE
#     return np.concatenate([rB, rE])

# # initial guesses and bounds
# def fit_coupled(df):
#     # initial guesses (tune as needed)
#     pB0 = 1e-4; qB0 = 0.005; mB0 = max(df[BTC_CUM].max()*1.2, 1000); gBE0 = 0.1
#     pE0 = 1e-4; qE0 = 0.005; mE0 = max(df[ETH_CUM].max()*1.2, 1000); gEB0 = 0.1
#     x0 = [pB0,qB0,mB0,gBE0, pE0,qE0,mE0,gEB0]
#     # bounds: p,q in [0,1], m0 positive, gamma maybe in [-1,1] or wider
#     lower = [0,0,  max(df[BTC_CUM].max(),1.0), -2.0,  0,0, max(df[ETH_CUM].max(),1.0), -2.0]
#     upper = [1,1,  1e7, 2.0,  1,1, 1e7, 2.0]
#     res = least_squares(residuals, x0, bounds=(lower,upper), args=(df,), method='trf', max_nfev=20000)
#     return res

# def approx_se(res, df):
#     # numerical jacobian available in res.jac (2n x k)
#     J = res.jac
#     nrows = J.shape[0]
#     k = J.shape[1]
#     # build residual vector (not scaled here) to compute sigma2: need original residuals unscaled
#     rvec = residuals(res.x, df)
#     # note we scaled residuals by SDs inside residuals(); recompute sigma2 accordingly:
#     sigma2 = np.sum(rvec**2) / (len(rvec) - k)
#     try:
#         cov = sigma2 * np.linalg.inv(J.T.dot(J))
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         cov = np.full((k,k), np.nan)
#         se = np.full(k, np.nan)
#     return se, cov

# def main():
#     df = load_df()
#     res = fit_coupled(df)
#     print("Optimization success:", res.success, "message:", res.message)
#     params = res.x
#     names = ['pB','qB','mB0','gBE','pE','qE','mE0','gEB']
#     for n,v in zip(names, params):
#         print(f"{n:4s} = {v}")
#     se, cov = approx_se(res, df)
#     print("SE:", se)
#     # interpret gamma signs:
#     gBE = params[3]; gEB = params[7]
#     if np.isfinite(gBE):
#         if gBE > 0: print(f"Estimate gamma_BE={gBE:.4g} >0 → ETH 削弱 BTC（竞争）")
#         else: print(f"Estimate gamma_BE={gBE:.4g} <0 → ETH 促进 BTC（互补）")
#     if np.isfinite(gEB):
#         if gEB > 0: print(f"Estimate gamma_EB={gEB:.4g} >0 → BTC 削弱 ETH（竞争）")
#         else: print(f"Estimate gamma_EB={gEB:.4g} <0 → BTC 促进 ETH（互补）")
#     # optional: compute fitted series and plot (omitted here)
#     return res, se, cov

# if __name__ == "__main__":
#     res, se, cov = main()


# =======
# 加入显著性分析
# competition_bass_fit.py
# import numpy as np
# import pandas as pd
# from scipy.optimize import least_squares
# from scipy.stats import t as tdist

# # ----------------- 配置 -----------------
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# BTC_CUM = "btc_cum_users"
# BTC_NEW = "btc_new_developers"
# ETH_CUM = "bsv_cum_users"
# ETH_NEW = "bsv_new_developers"
# START_DATE = "2018-09-01"
# END_DATE = "2024-12-31"
# # -----------------------------------------

# def load_df():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df.loc[(df[DATE_COL] >= START_DATE) & (df[DATE_COL] <= END_DATE)].copy()
#     df = df.sort_values(DATE_COL).reset_index(drop=True)
#     df[[BTC_CUM, BTC_NEW, ETH_CUM, ETH_NEW]] = df[[BTC_CUM, BTC_NEW, ETH_CUM, ETH_NEW]].fillna(0)
#     return df

# # Bass instantaneous given N, p,q,m (m allowed array)
# def bass_instant(N, p, q, m):
#     m = np.asarray(m)
#     rem = np.maximum(m - N, 0)
#     return (p + q * (N / (m + 1e-12))) * rem

# # compute m_B(t), m_E(t) with simple subtractive competition
# def compute_m_t(N_other, m0, gamma):
#     m_t = m0 - gamma * N_other
#     m_t = np.maximum(m_t, 1.0)
#     return m_t

# # residuals: stack btc_resids then eth_resids
# def residuals(params, df):
#     # params: [pB,qB,mB0,gBE,  pE,qE,mE0,gEB]
#     pB,qB,mB0,gBE, pE,qE,mE0,gEB = params
#     N_B = df[BTC_CUM].values
#     N_E = df[ETH_CUM].values
#     mB_t = compute_m_t(N_E, mB0, gBE)
#     mE_t = compute_m_t(N_B, mE0, gEB)
#     dB_pred = bass_instant(N_B, pB, qB, mB_t)
#     dE_pred = bass_instant(N_E, pE, qE, mE_t)
#     dB_obs = df[BTC_NEW].values
#     dE_obs = df[ETH_NEW].values
#     sB = np.std(dB_obs) if np.std(dB_obs)>0 else 1.0
#     sE = np.std(dE_obs) if np.std(dE_obs)>0 else 1.0
#     rB = (dB_obs - dB_pred) / sB
#     rE = (dE_obs - dE_pred) / sE
#     return np.concatenate([rB, rE])

# # initial guesses and bounds
# def fit_coupled(df):
#     pB0 = 1e-5; qB0 = 0.005; mB0 = max(df[BTC_CUM].max()*1.2, 1000); gBE0 = 0.1
#     pE0 = 1e-5; qE0 = 0.005; mE0 = max(df[ETH_CUM].max()*1.2, 1000); gEB0 = 0.1
#     x0 = [pB0,qB0,mB0,gBE0, pE0,qE0,mE0,gEB0]
#     lower = [0,0, max(df[BTC_CUM].max(),1.0), -2.0, 0,0, max(df[ETH_CUM].max(),1.0), -2.0]
#     upper = [1,1, 1e7, 2.0, 1,1, 1e7, 2.0]
#     res = least_squares(residuals, x0, bounds=(lower,upper), args=(df,),
#                         method='trf', max_nfev=20000)
#     return res

# # compute standard errors, t/p values, and condition number
# # def approx_se(res, df):
# #     J = res.jac
# #     n, k = J.shape
# #     rvec = residuals(res.x, df)
# #     sigma2 = np.sum(rvec**2) / max(n - k, 1)  # 防 df< k
# #     JTJ = J.T @ J
# #     try:
# #         # 用伪逆处理奇异
# #         cov = sigma2 * np.linalg.pinv(JTJ)
# #         se = np.sqrt(np.diag(cov))
# #         cond = np.linalg.cond(JTJ)
# #         rank = np.linalg.matrix_rank(JTJ)
# #         print(f"JTJ rank={rank}/{k}, cond={cond:.2e}")  # 诊断
# #     except:
# #         cov = np.full((k,k), np.nan)
# #         se = np.full(k, np.nan)
# #         cond = np.nan
# #         rank = 0
# #     return se, cov, cond

# # 原始函数
# def approx_se(res, df):
#     J = res.jac
#     n, k = J.shape
#     rvec = residuals(res.x, df)
#     sigma2 = np.sum(rvec**2) / (len(rvec) - k)
#     try:
#         JTJ = J.T @ J
#         cov = sigma2 * np.linalg.inv(JTJ)
#         se = np.sqrt(np.diag(cov))
#         cond = np.linalg.cond(JTJ)
#     except np.linalg.LinAlgError:
#         cov = np.full((k,k), np.nan)
#         se = np.full(k, np.nan)
#         cond = np.nan
#     return se, cov, cond


# def main():
#     df = load_df()
#     res = fit_coupled(df)
#     params = res.x
#     names = ['pB','qB','mB0','gBE','pE','qE','mE0','gEB']
#     print("✅ Optimization success:", res.success, "| Message:", res.message)
#     print("Estimated parameters:")
#     for n,v in zip(names, params):
#         print(f"  {n:4s} = {v:,.6g}")

#     # ---- 显著性检验 ----
#     se, cov, cond = approx_se(res, df)
#     n_obs = len(df)*2
#     k = len(params)
#     tvals = params / se
#     pvals = 2*(1 - tdist.cdf(np.abs(tvals), df=n_obs-k))

#     print("\n--- 参数显著性检验 ---")
#     print(f"Hessian 条件数 cond(JᵀJ) = {cond:.2e}\n")
#     for n,v,s,tv,pv in zip(names, params, se, tvals, pvals):
#         pv_fmt = f"{pv:.3e}" if np.isfinite(pv) else "nan"
#         print(f"{n:4s} : {v:12.6g} | SE={s:10.6g} | t={tv:8.3f} | p={pv_fmt}")
        
#     # 诊断 J
#     # J = res.jac
#     # JTJ = J.T @ J
#     # print("J shape:", J.shape)  # (n_obs, k) = (2*len(df), 8)
#     # print("JTJ rank:", np.linalg.matrix_rank(JTJ))  # <8 表示奇异
#     # print("JTJ cond:", np.linalg.cond(JTJ))  # inf/nan 表示病态
#     # print("residuals std:", np.std(res.fun))  # 应 <1 (normalized)

#     # ---- 解读 gamma 竞争效应 ----
#     gBE = params[3]; gEB = params[7]
#     print("\n--- 竞争方向 ---")
#     if np.isfinite(gBE):
#         if gBE > 0: print(f"γ_BE={gBE:.4g} >0 → ETH 削弱 BTC（竞争效应）")
#         else: print(f"γ_BE={gBE:.4g} <0 → ETH 促进 BTC（正溢出）")
#     if np.isfinite(gEB):
#         if gEB > 0: print(f"γ_EB={gEB:.4g} >0 → BTC 削弱 ETH（竞争效应）")
#         else: print(f"γ_EB={gEB:.4g} <0 → BTC 促进 ETH（正溢出）")

#     return res, se, cov
    

# if __name__ == "__main__":
#     res, se, cov = main()


# ==========================
# 只拟合BTC，不拟合BSV/BCH，但考虑BSV/BCH带来的竞争

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.stats import t as tdist

# ----------------- 配置 -----------------
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
DATE_COL = "date"
BTC_CUM = "btc_cum_users"
BTC_NEW = "btc_new_developers"
BSV_CUM = "bch_cum_users"
BSV_NEW = "bch_new_developers"
START_DATE = "2017-05-01"
END_DATE = "2018-08-28"
# -----------------------------------------

def load_df():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df.loc[(df[DATE_COL] >= START_DATE) & (df[DATE_COL] <= END_DATE)].copy()
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df[[BTC_CUM, BTC_NEW, BSV_CUM]] = df[[BTC_CUM, BTC_NEW, BSV_CUM]].fillna(0)
    return df

# Bass instantaneous given N, p,q,m (m allowed array)
def bass_instant(N, p, q, m):
    m = np.asarray(m)
    rem = np.maximum(m - N, 0)
    return (p + q * (N / (m + 1e-12))) * rem

# dynamic potential market under competition
def compute_m_t(N_other, m0, gamma):
    m_t = m0 - gamma * N_other
    m_t = np.maximum(m_t, 1.0)
    return m_t

# residuals only for BTC, but considering competition from BSV
def residuals(params, df):
    pB, qB, mB0, gBE = params
    N_B = df[BTC_CUM].values
    N_E = df[BSV_CUM].values
    mB_t = compute_m_t(N_E, mB0, gBE)
    dB_pred = bass_instant(N_B, pB, qB, mB_t)
    dB_obs = df[BTC_NEW].values
    sB = np.std(dB_obs) if np.std(dB_obs) > 0 else 1.0
    rB = (dB_obs - dB_pred) / sB
    return rB

# fit function
def fit_single_competition(df):
    pB0 = 1e-4
    qB0 = 0.005
    mB0 = max(df[BTC_CUM].max() * 1.2, 1000)
    gBE0 = 0.1
    x0 = [pB0, qB0, mB0, gBE0]
    lower = [0, 0, max(df[BTC_CUM].max(), 1.0), -2.0]
    upper = [1, 1, 1e7, 2.0]

    res = least_squares(residuals, x0, bounds=(lower, upper), args=(df,),
                        method='trf', max_nfev=20000)
    return res

# compute standard errors and significance
def approx_se(res, df):
    J = res.jac
    n, k = J.shape
    rvec = residuals(res.x, df)
    sigma2 = np.sum(rvec**2) / (len(rvec) - k)
    try:
        JTJ = J.T @ J
        cov = sigma2 * np.linalg.inv(JTJ)
        se = np.sqrt(np.diag(cov))
        cond = np.linalg.cond(JTJ)
    except np.linalg.LinAlgError:
        cov = np.full((k, k), np.nan)
        se = np.full(k, np.nan)
        cond = np.nan
    return se, cov, cond

def main():
    df = load_df()
    res = fit_single_competition(df)
    params = res.x
    names = ['pB', 'qB', 'mB0', 'gBE']
    print("✅ Optimization success:", res.success, "| Message:", res.message)
    print("Estimated parameters:")
    for n, v in zip(names, params):
        print(f"  {n:4s} = {v:,.6g}")

    # ---- 显著性检验 ----
    se, cov, cond = approx_se(res, df)
    n_obs = len(df)
    k = len(params)
    tvals = params / se
    pvals = 2 * (1 - tdist.cdf(np.abs(tvals), df=n_obs - k))

    print("\n--- 参数显著性检验 ---")
    print(f"Hessian 条件数 cond(JᵀJ) = {cond:.2e}\n")
    for n, v, s, tv, pv in zip(names, params, se, tvals, pvals):
        pv_fmt = f"{pv:.3e}" if np.isfinite(pv) else "nan"
        print(f"{n:4s} : {v:12.6g} | SE={s:10.6g} | t={tv:8.3f} | p={pv_fmt}")

    # ---- 竞争解释 ----
    gBE = params[3]
    print("\n--- 竞争方向 ---")
    if np.isfinite(gBE):
        if gBE > 0:
            print(f"γ_BE={gBE:.4g} >0 → BCH 削弱 BTC（竞争效应）")
        else:
            print(f"γ_BE={gBE:.4g} <0 → BCH 促进 BTC（正溢出）")

    return res, se, cov

if __name__ == "__main__":
    res, se, cov = main()
