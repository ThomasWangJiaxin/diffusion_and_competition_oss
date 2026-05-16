# price+p_event
# 只有线形和log两种形式
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt
# import os

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# EVENT_COL = "btc_p_event"
# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_price_event_new.png"
# OUTPUT_PNG_CUM = "btc_bass_price_event_cum.png"
# OUTPUT_CSV = "btc_bass_price_event_results.csv"
# # ===================================

# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     # keep needed cols
#     cols = [DATE_COL, NEW_COL, CUM_COL, PRICE_COL, EVENT_COL]
#     missing = [c for c in cols if c not in df.columns]
#     if missing:
#         raise ValueError(f"CSV 缺少列: {missing}")
#     df = df[cols].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()

# def zscore_safe(x):
#     x = np.asarray(x, dtype=float)
#     mu = np.nanmean(x)
#     sd = np.nanstd(x)
#     if sd == 0 or np.isnan(sd):
#         return np.zeros_like(x), mu, sd
#     return (x - mu) / sd, mu, sd

# # --------- p(t) 形式（均使用标准化后的输入） ----------
# # Form A: linear additive: p0 + alpha*price_z + beta*event_z
# def p_linear_both(price_z, event_z, p0, alpha, beta):
#     return np.maximum(p0 + alpha * price_z + beta * event_z, 1e-12)

# # Form B: price linear + log(event) (log1p then zscore)
# def p_price_plus_logevent(price_z, logevent_z, p0, alpha, beta):
#     return np.maximum(p0 + alpha * price_z + beta * logevent_z, 1e-12)

# # --------- Bass instantaneous ----------
# def dN_pred(N, p_t, q, m):
#     # p_t can be array (time-varying)
#     remaining = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining

# # --------- compute prediction wrapper ----------
# def compute_prediction_formula(df, params, form):
#     # params vary by form:
#     # form 'linear': params = [p0, alpha, beta, q, m]
#     # form 'logevent': params = [p0, alpha, beta, q, m]
#     p0, alpha, beta, q, m = params
#     # price_z and event_z / logevent_z should be precomputed in df
#     price_z = df['price_z'].values
#     if form == 'linear':
#         event_z = df['event_z'].values
#         p_t = p_linear_both(price_z, event_z, p0, alpha, beta)
#     elif form == 'logevent':
#         logevent_z = df['logevent_z'].values
#         p_t = p_price_plus_logevent(price_z, logevent_z, p0, alpha, beta)
#     else:
#         raise ValueError("Unknown form")
#     N = df[CUM_COL].values
#     dN = dN_pred(N, p_t, q, m)
#     return dN, p_t

# # --------- residuals for least_squares ----------
# def residuals_all(params, df, form):
#     # params: [p0, alpha, beta, q, m]
#     p0, alpha, beta, q, m = params
#     # basic parameter constraints
#     if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
#         return np.ones(len(df)) * 1e6
#     dN_predicted, _ = compute_prediction_formula(df, params, form)
#     dN_true = df[NEW_COL].values
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return dN_true - dN_predicted

# # --------- fit and significance computation ----------
# def fit_and_stats(df, form):
#     # init and bounds
#     m_guess = max(1.2 * df[CUM_COL].max(), df[CUM_COL].max() + 1.0)
#     init = [1e-4, 0.01, 0.01, 0.01, m_guess]  # p0, alpha, beta, q, m
#     lower = [0.0, -10.0, -10.0, 0.0, 0.9*m_guess]
#     upper = [1.0, 10.0, 10.0, 1.0, 20.0*m_guess]

#     res = least_squares(residuals_all, init, bounds=(lower, upper), args=(df, form), method='trf', max_nfev=20000)
#     if not res.success:
#         return None

#     params = res.x.copy()
#     n = len(df)
#     k = len(params)

#     # compute predicted y and numerical jacobian for statistics
#     eps = 1e-6
#     y_pred = df[NEW_COL].values - residuals_all(params, df, form)  # predicted dN
#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps = df[NEW_COL].values - residuals_all(params_eps, df, form)
#         grad = (y_pred_eps - y_pred) / eps
#         J.append(grad)
#     J = np.array(J).T  # n x k

#     # condition number
#     try:
#         JTJ = J.T @ J
#         cond = np.linalg.cond(JTJ)
#     except np.linalg.LinAlgError:
#         JTJ = J.T @ J
#         cond = np.nan

#     # residuals vector and sigma2
#     resid_vec = df[NEW_COL].values - y_pred
#     df_resid = n - k if (n - k) > 0 else 1
#     sigma2 = np.sum(resid_vec**2) / df_resid

#     # covariance: use regularized pseudo-inverse if needed
#     try:
#         reg = 1e-8 * np.eye(J.shape[1])
#         cov = sigma2 * np.linalg.inv(JTJ + reg)
#     except np.linalg.LinAlgError:
#         cov = sigma2 * np.linalg.pinv(JTJ + reg)

#     se = np.sqrt(np.abs(np.diag(cov)))  # ensure non-neg
#     # guard against zero SE
#     se = np.where(se == 0, np.nan, se)
#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

#     # RMSE
#     rmse = np.sqrt(np.mean(resid_vec**2))

#     return {
#         'params': params,
#         'se': se,
#         'tvals': tvals,
#         'pvals': pvals,
#         'cond': cond,
#         'rmse': rmse,
#         'y_pred': y_pred
#     }

# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     # --- 预处理：标准化 price 和 event ---
#     price_arr = df[PRICE_COL].values.astype(float)
#     event_arr = df[EVENT_COL].values.astype(float)

#     # price z
#     price_z, price_mu, price_sd = zscore_safe(price_arr)
#     df['price_z'] = price_z

#     # event z (for linear form)
#     event_z, ev_mu, ev_sd = zscore_safe(event_arr)
#     df['event_z'] = event_z

#     # log(event+1) z (for logevent form)
#     logevent = np.log1p(np.maximum(event_arr, 0.0))
#     logevent_z, logev_mu, logev_sd = zscore_safe(logevent)
#     df['logevent_z'] = logevent_z

#     # models to run
#     forms = {
#         'linear': 'linear',      # p = p0 + alpha*price_z + beta*event_z
#         'logevent': 'logevent'   # p = p0 + alpha*price_z + beta*log1p(event) (both standardized)
#     }

#     results = []

#     for name, form in forms.items():
#         print(f"\n=== 拟合模型：{name} ===")
#         out = fit_and_stats(df, form)
#         if out is None:
#             print(f"❌ {name} 拟合失败")
#             continue

#         params = out['params']
#         se = out['se']
#         tvals = out['tvals']
#         pvals = out['pvals']
#         cond = out['cond']
#         rmse = out['rmse']
#         y_pred = out['y_pred']

#         print(f"✅ {name} 拟合成功： params = {np.round(params,6)}")
#         print(f"RMSE = {rmse:.4f}, cond(J^T J) = {cond:.2e}")
#         names = ['p0','alpha_price','beta_event','q','m']
#         for nm, val, s, tval, pval in zip(names, params, se, tvals, pvals):
#             print(f"{nm:12s}: {val:12.6f} | SE={s:10.6f} | t={tval:8.3f} | p={pval:.6e}")

#         # 保存 result
#         results.append({
#             'model': name,
#             'p0': params[0],
#             'alpha_price': params[1],
#             'beta_event': params[2],
#             'q': params[3],
#             'm': params[4],
#             'se_p0': se[0], 'se_alpha_price': se[1], 'se_beta_event': se[2],
#             't_p0': tvals[0], 't_alpha_price': tvals[1], 't_beta_event': tvals[2],
#             'p_p0': pvals[0], 'p_alpha_price': pvals[1], 'p_beta_event': pvals[2],
#             'cond': cond, 'rmse': rmse
#         })

#         # attach predicted series into df for plotting
#         df[f'pred_new_{name}'] = y_pred
#         # cumulative predicted as N0 + cumsum(dN_pred)
#         df[f'pred_cum_{name}'] = df[CUM_COL].iloc[0] + np.cumsum(y_pred)

#     # save results
#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果已保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效结果可保存。")

#     # --- 绘图：新增 & 累积 ---
#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label='真实新增', color='black', linewidth=2)
#     for name in forms.keys():
#         if f'pred_new_{name}' in df.columns:
#             plt.plot(df[DATE_COL], df[f'pred_new_{name}'], '--', label=f'预测新增 ({name})')
#     plt.xlabel('日期'); plt.ylabel('新增开发者 dN/dt'); plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增拟合图保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12,6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label='真实累积 N(t)', color='black', linewidth=2)
#     for name in forms.keys():
#         if f'pred_cum_{name}' in df.columns:
#             plt.plot(df[DATE_COL], df[f'pred_cum_{name}'], '--', label=f'预测累积 ({name})')
#     plt.xlabel('日期'); plt.ylabel('累积开发者 N(t)'); plt.legend(); plt.grid(True, linestyle='--'); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积拟合图保存至 {OUTPUT_PNG_CUM}")

# if __name__ == "__main__":
#     main()


# =================
# 有四种形式
# price 与 event 都在拟合前经过全样本 z-score 标准化；拟合过程中与交互项、对数项等计算均基于标准化后的数值，没有在拟合后反标准化。

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt


# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"
# PRICE_COL = "btc_price"
# EVENT_COL = "btc_p_event"

# START_DATE = "2016-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_price_eventfit_new.png"
# OUTPUT_PNG_CUM = "btc_bass_price_eventfit_cum.png"
# OUTPUT_CSV = "btc_bass_price_eventfit_results.csv"
# # ===================================


# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, EVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)

#     # ✅ 标准化 price 与 event
#     for col in [PRICE_COL, EVENT_COL]:
#         mean_val, std_val = df[col].mean(), df[col].std()
#         if std_val > 0:
#             df[col] = (df[col] - mean_val) / std_val
#         else:
#             print(f"⚠️ 列 {col} 标准差为0，跳过标准化。")

#     # 交互项
#     df["interaction"] = df[PRICE_COL] * df[EVENT_COL]
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()


# # --------- 模型定义 ----------
# def dN_pred(N, p_t, q, m):
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining_market


# def compute_p_t(df, params, model_type):
#     """
#     四种可选形式:
#       1. linear_add      : p0 + α * price + β * event
#       2. log_event       : p0 + α * price + β * log(event + 1)
#       3. linear_interact : p0 + α * price + β * event + γ * (price * event)
#       4. log_interact    : p0 + α * price + β * log(event + 1) + γ * (price * event)
#     """
#     P = df[PRICE_COL].values
#     E = df[EVENT_COL].values
#     I = df["interaction"].values

#     if model_type == "linear_add":
#         p0, alpha, beta, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * E, 0)

#     elif model_type == "log_event":
#         p0, alpha, beta, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)), 0)

#     elif model_type == "linear_interact":
#         p0, alpha, beta, gamma, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * E + gamma * I, 0)

#     elif model_type == "log_interact":
#         p0, alpha, beta, gamma, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)) + gamma * I, 0)

#     else:
#         raise ValueError("未知模型类型")

#     return p_t


# def compute_prediction(df, params, model_type):
#     p_t = compute_p_t(df, params, model_type)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, params[-2], params[-1]), p_t  # q, m 分别是倒数第二、最后一个参数


# # --------- 残差函数 ----------
# def residuals(params, df, model_type):
#     dN_predicted, _ = compute_prediction(df, params, model_type)
#     dN_true = df[NEW_COL].values

#     # 合理性约束
#     if (params[-1] <= df[CUM_COL].max()) or (params[-2] < 0) or (params[0] < 0):
#         return np.ones(len(df)) * 1e6

#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6

#     return dN_true - dN_predicted


# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, model_type):
#     m_guess = 1.2 * df[CUM_COL].max()

#     # 初始值与边界
#     if "interact" in model_type:
#         init = [1e-4, 0.01, 0.01, 0.01, 0.01, m_guess]
#         bounds = ([0, -10, -10, -10, 0, 0.9*m_guess], [1, 10, 10, 10, 1, 20*m_guess])
#     else:
#         init = [1e-4, 0.01, 0.01, 0.01, m_guess]
#         bounds = ([0, -10, -10, 0, 0.9*m_guess], [1, 10, 10, 1, 20*m_guess])

#     res = least_squares(residuals, init, bounds=bounds, args=(df, model_type), method="trf")
#     if not res.success:
#         return res, None
#     params = res.x

#     # 显著性检验
#     eps = 1e-6
#     n = len(df)
#     k = len(params)
#     y_pred, _ = compute_prediction(df, params, model_type)

#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df, params_eps, model_type)
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T

#     cond = np.linalg.cond(J.T @ J)
#     print(f"⚙️ Hessian 条件数 cond={cond:.2e}")

#     y_true = df[NEW_COL].values
#     residuals_vec = y_true - y_pred
#     sigma2 = np.sum(residuals_vec ** 2) / (n - k)

#     try:
#         cov = sigma2 * np.linalg.inv(J.T @ J + 1e-6 * np.eye(J.shape[1]))
#         se = np.sqrt(np.diag(cov))
#     except np.linalg.LinAlgError:
#         se = np.full(k, np.nan)

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
#     res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond

#     names = {
#         "linear_add": ["p0", "alpha(price)", "beta(event)", "q", "m"],
#         "log_event": ["p0", "alpha(price)", "beta(logE)", "q", "m"],
#         "linear_interact": ["p0", "alpha(price)", "beta(event)", "gamma(inter)", "q", "m"],
#         "log_interact": ["p0", "alpha(price)", "beta(logE)", "gamma(inter)", "q", "m"]
#     }[model_type]

#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(names, params, se, tvals, pvals):
#         print(f"{name:15s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)
#     models = ["linear_add", "log_event", "linear_interact", "log_interact"]
#     results = []
#     valid_models = []

#     for name in models:
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, name)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         dN_predicted, p_t = compute_prediction(df, res.x, name)
#         rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
#         sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)

#         print(f"✅ 拟合成功：{name}, RMSE={rmse:.3f}")
#         cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted
#         results.append({"model": name, **{f"param_{i}": val for i, val in enumerate(res.x)}, "SSE": sse, "RMSE": rmse})
#         valid_models.append(name)

#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     # 绘制图像
#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.legend(); plt.grid(True, linestyle='--'); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")


# if __name__ == "__main__":
#     main()

# 新增三个log price拟合

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"
PRICE_COL = "btc_ma_14d"
EVENT_COL = "btc_p_event_sum_30"

START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "btc_bass_price_eventfit_new.png"
OUTPUT_PNG_CUM = "btc_bass_price_eventfit_cum.png"
OUTPUT_CSV = "btc_bass_price_eventfit_results.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, EVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)

    # ✅ 全局标准化 price 与 event
    for col in [PRICE_COL, EVENT_COL]:
        mean_val, std_val = df[col].mean(), df[col].std()
        if std_val > 0:
            df[col] = (df[col] - mean_val) / std_val
        else:
            print(f"⚠️ 列 {col} 标准差为0，跳过标准化。")

    # log 变量及交互项
    df["log_price"] = np.log1p(np.maximum(df[PRICE_COL], 0))
    df["log_event"] = np.log1p(np.maximum(df[EVENT_COL], 0))
    df["interaction"] = df[PRICE_COL] * df[EVENT_COL]
    df["log_interaction"] = df["log_price"] * df["log_event"]
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

# --------- 模型定义 ----------
def dN_pred(N, p_t, q, m):
    remaining_market = np.maximum(m - N, 0)
    return (p_t + q * (N / m)) * remaining_market

def compute_p_t(df, params, model_type):
    P = df[PRICE_COL].values
    E = df[EVENT_COL].values
    LP = df["log_price"].values
    LE = df["log_event"].values
    I = df["interaction"].values
    LI = df["log_interaction"].values

    if model_type == "linear_add":
        p0, alpha, beta, q, m = params
        p_t = np.maximum(p0 + alpha * P + beta * E, 0)

    elif model_type == "log_event":
        p0, alpha, beta, q, m = params
        p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)), 0)

    elif model_type == "linear_interact":
        p0, alpha, beta, gamma, q, m = params
        p_t = np.maximum(p0 + alpha * P + beta * E + gamma * I, 0)

    elif model_type == "log_interact":
        p0, alpha, beta, gamma, q, m = params
        p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)) + gamma * I, 0)

    # === 新增三种含 log(price) 模型 ===
    elif model_type == "logprice_add":
        p0, alpha, beta, q, m = params
        p_t = np.maximum(p0 + alpha * LP + beta * E, 0)

    elif model_type == "logprice_logevent":
        p0, alpha, beta, q, m = params
        p_t = np.maximum(p0 + alpha * LP + beta * LE, 0)

    elif model_type == "logprice_loginteract":
        p0, alpha, beta, gamma, q, m = params
        p_t = np.maximum(p0 + alpha * LP + beta * LE + gamma * LI, 0)

    else:
        raise ValueError(f"未知模型类型：{model_type}")

    return p_t

def compute_prediction(df, params, model_type):
    p_t = compute_p_t(df, params, model_type)
    N = df[CUM_COL].values
    return dN_pred(N, p_t, params[-2], params[-1]), p_t  # q, m

# --------- 残差函数 ----------
def residuals(params, df, model_type):
    dN_predicted, _ = compute_prediction(df, params, model_type)
    dN_true = df[NEW_COL].values
    if (params[-1] <= df[CUM_COL].max()) or (params[-2] < 0) or (params[0] < 0):
        return np.ones(len(df)) * 1e6
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return dN_true - dN_predicted

# --------- 参数拟合 + 显著性检验 ----------
def fit_bass(df, model_type):
    m_guess = 1.2 * df[CUM_COL].max()
    if "interact" in model_type:
        init = [1e-4, 0.01, 0.01, 0.01, 0.01, m_guess]
        bounds = ([0, -10, -10, -10, 0, 0.9*m_guess], [1, 10, 10, 10, 1, 20*m_guess])
    else:
        init = [1e-4, 0.01, 0.01, 0.01, m_guess]
        bounds = ([0, -10, -10, 0, 0.9*m_guess], [1, 10, 10, 1, 20*m_guess])

    res = least_squares(residuals, init, bounds=bounds, args=(df, model_type), method="trf")
    if not res.success:
        return res, None
    params = res.x

    eps = 1e-6
    n = len(df)
    k = len(params)
    y_pred, _ = compute_prediction(df, params, model_type)

    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_pred_eps, _ = compute_prediction(df, params_eps, model_type)
        J.append((y_pred_eps - y_pred) / eps)
    J = np.array(J).T
    cond = np.linalg.cond(J.T @ J)
    print(f"⚙️ Hessian 条件数 cond={cond:.2e}")

    y_true = df[NEW_COL].values
    residuals_vec = y_true - y_pred
    sigma2 = np.sum(residuals_vec ** 2) / (n - k)

    try:
        cov = sigma2 * np.linalg.inv(J.T @ J + 1e-6 * np.eye(J.shape[1]))
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)

    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
    res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond

    names_dict = {
        "linear_add": ["p0", "alpha(price)", "beta(event)", "q", "m"],
        "log_event": ["p0", "alpha(price)", "beta(logE)", "q", "m"],
        "linear_interact": ["p0", "alpha(price)", "beta(event)", "gamma(inter)", "q", "m"],
        "log_interact": ["p0", "alpha(price)", "beta(logE)", "gamma(inter)", "q", "m"],
        "logprice_add": ["p0", "alpha(logP)", "beta(event)", "q", "m"],
        "logprice_logevent": ["p0", "alpha(logP)", "beta(logE)", "q", "m"],
        "logprice_loginteract": ["p0", "alpha(logP)", "beta(logE)", "gamma(logP*logE)", "q", "m"]
    }
    names = names_dict[model_type]

    print("\n--- 参数显著性检验 ---")
    for name, val, se_i, t_i, p_i in zip(names, params, se, tvals, pvals):
        print(f"{name:20s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")
    return res

# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    models = [
        "linear_add", "log_event", "linear_interact", "log_interact",
        "logprice_add", "logprice_logevent", "logprice_loginteract"
    ]

    results, valid_models = [], []

    for name in models:
        print(f"\n=== 拟合模型：{name} ===")
        res = fit_bass(df, name)
        if (not res.success) or np.any(np.isnan(res.x)):
            print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
            continue
        dN_predicted, p_t = compute_prediction(df, res.x, name)
        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
        sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)

        print(f"✅ 拟合成功：{name}, RMSE={rmse:.3f}")
        cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_predicted
        results.append({"model": name, **{f"param_{i}": val for i, val in enumerate(res.x)}, "SSE": sse, "RMSE": rmse})
        valid_models.append(name)

    if results:
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ 拟合结果保存至 {OUTPUT_CSV}")
    else:
        print("❌ 无有效模型结果。")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
    plt.legend(); plt.grid(True, linestyle='--'); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")

if __name__ == "__main__":
    main()



# 局部标准化

# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"
# CUM_COL = "eth_cum_users"
# PRICE_COL = "eth_price"
# EVENT_COL = "eth_p_event"

# START_DATE = "2016-03-10"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "eth_bass_price_eventfit_new.png"
# OUTPUT_PNG_CUM = "eth_bass_price_eventfit_cum.png"
# OUTPUT_CSV = "eth_bass_price_eventfit_results.csv"
# # ===================================


# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, EVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)
#     df["interaction"] = df[PRICE_COL] * df[EVENT_COL]
#     return df


# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()


# # --------- 模型定义 ----------
# def dN_pred(N, p_t, q, m):
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining_market


# def compute_p_t(df, params, model_type, price_col, event_col):
#     """
#     四种可选形式:
#       1. linear_add      : p0 + α * price + β * event
#       2. log_event       : p0 + α * price + β * log(event + 1)
#       3. linear_interact : p0 + α * price + β * event + γ * (price * event)
#       4. log_interact    : p0 + α * price + β * log(event + 1) + γ * (price * event)
#     """
#     P = df[price_col].values
#     E = df[event_col].values
#     I = (df[price_col] * df[event_col]).values

#     if model_type == "linear_add":
#         p0, alpha, beta, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * E, 0)

#     elif model_type == "log_event":
#         p0, alpha, beta, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)), 0)

#     elif model_type == "linear_interact":
#         p0, alpha, beta, gamma, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * E + gamma * I, 0)

#     elif model_type == "log_interact":
#         p0, alpha, beta, gamma, q, m = params
#         p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)) + gamma * I, 0)

#     else:
#         raise ValueError("未知模型类型")

#     return p_t


# def compute_prediction(df, params, model_type, price_col, event_col):
#     p_t = compute_p_t(df, params, model_type, price_col, event_col)
#     N = df[CUM_COL].values
#     return dN_pred(N, p_t, params[-2], params[-1]), p_t


# # --------- 残差函数 ----------
# def residuals(params, df, model_type, price_col, event_col):
#     dN_predicted, _ = compute_prediction(df, params, model_type, price_col, event_col)
#     dN_true = df[NEW_COL].values

#     if (params[-1] <= df[CUM_COL].max()) or (params[-2] < 0) or (params[0] < 0):
#         return np.ones(len(df)) * 1e6

#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6

#     return dN_true - dN_predicted


# # --------- 参数拟合 + 显著性检验（局部标准化） ----------
# def fit_bass(df, model_type):
#     # --- 局部标准化 ---
#     df_norm = df.copy()
#     price_mean, price_std = df_norm[PRICE_COL].mean(), df_norm[PRICE_COL].std()
#     event_mean, event_std = df_norm[EVENT_COL].mean(), df_norm[EVENT_COL].std()
#     df_norm["price_std"] = (df_norm[PRICE_COL] - price_mean) / price_std
#     df_norm["event_std"] = (df_norm[EVENT_COL] - event_mean) / event_std

#     m_guess = 1.2 * df[CUM_COL].max()

#     if "interact" in model_type:
#         init = [1e-4, 0.01, 0.01, 0.01, 0.01, m_guess]
#         bounds = ([0, -10, -10, -10, 0, 0.9*m_guess], [1, 10, 10, 10, 1, 20*m_guess])
#     else:
#         init = [1e-4, 0.01, 0.01, 0.01, m_guess]
#         bounds = ([0, -10, -10, 0, 0.9*m_guess], [1, 10, 10, 1, 20*m_guess])

#     res = least_squares(residuals, init, bounds=bounds,
#                         args=(df_norm, model_type, "price_std", "event_std"), method="trf")

#     if not res.success:
#         return res, None

#     params = res.x.copy()

#     # --- 参数还原（反标准化） ---
#     if "interact" in model_type:
#         p0, alpha, beta, gamma, q, m = params
#         # 对应缩放关系
#         alpha_orig = alpha / price_std
#         beta_orig = beta / event_std
#         gamma_orig = gamma / (price_std * event_std)
#         p0_orig = p0 - alpha_orig * price_mean - beta_orig * event_mean - gamma_orig * price_mean * event_mean
#         params_orig = [p0_orig, alpha_orig, beta_orig, gamma_orig, q, m]
#     else:
#         p0, alpha, beta, q, m = params
#         alpha_orig = alpha / price_std
#         beta_orig = beta / event_std
#         p0_orig = p0 - alpha_orig * price_mean - beta_orig * event_mean
#         params_orig = [p0_orig, alpha_orig, beta_orig, q, m]

#     res.params_orig = np.array(params_orig)

#     # --- 显著性检验 ---
#     eps = 1e-6
#     n, k = len(df), len(params)
#     y_pred, _ = compute_prediction(df_norm, params, model_type, "price_std", "event_std")

#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df_norm, params_eps, model_type, "price_std", "event_std")
#         grad_i = (y_pred_eps - y_pred) / eps
#         J.append(grad_i)
#     J = np.array(J).T

#     cond = np.linalg.cond(J.T @ J)
#     print(f"⚙️ Hessian 条件数 cond={cond:.2e}")

#     y_true = df[NEW_COL].values
#     residuals_vec = y_true - y_pred
#     sigma2 = np.sum(residuals_vec ** 2) / (n - k)
#     cov = sigma2 * np.linalg.inv(J.T @ J + 1e-6 * np.eye(J.shape[1]))
#     se = np.sqrt(np.diag(cov))

#     tvals = params / se
#     pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
#     res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond

#     return res


# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)
#     models = ["linear_add", "log_event", "linear_interact", "log_interact"]
#     results, valid_models = [], []

#     for name in models:
#         print(f"\n=== 拟合模型：{name} ===")
#         res = fit_bass(df, name)
#         if (not res.success) or np.any(np.isnan(res.x)):
#             print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
#             continue

#         dN_predicted, p_t = compute_prediction(df, res.params_orig, name, PRICE_COL, EVENT_COL)
#         rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
#         sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)

#         print(f"✅ 拟合成功：{name}, RMSE={rmse:.3f}")
#         cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
#         df[f"pred_new_{name}"] = dN_predicted
#         df[f"pred_cum_{name}"] = cum_predicted

#         results.append({"model": name, **{f"param_{i}": val for i, val in enumerate(res.params_orig)},
#                         "SSE": sse, "RMSE": rmse})
#         valid_models.append(name)

#     if results:
#         pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#         print(f"\n✅ 拟合结果保存至 {OUTPUT_CSV}")
#     else:
#         print("❌ 无有效模型结果。")
#         return

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
#     plt.legend(); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_NEW, dpi=300)
#     print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

#     plt.figure(figsize=(12, 6))
#     plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
#     for name in valid_models:
#         plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
#     plt.legend(); plt.grid(True, linestyle='--'); plt.tight_layout()
#     plt.savefig(OUTPUT_PNG_CUM, dpi=300)
#     print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")


# if __name__ == "__main__":
#     main()
