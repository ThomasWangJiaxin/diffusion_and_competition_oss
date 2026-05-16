# p(t)改price+p_event
# bass model拟合应该用N(t-1)
# 价格已经用了滞后的：
# btc_price_lag1	ln_btc_price_lag1 btc_return_1d 
# btc_return_7d	btc_vol_7d	btc_ma_7d	btc_trend_7d	
# btc_return_14	btc_vol_14d	btc_ma_14d	btc_trend_14d	
# btc_return_21	btc_vol_21d	btc_ma_21d	btc_trend_21d	
# btc_return_30	btc_vol_30d	btc_ma_30d	btc_trend_30d

# event也使用了滞后的
# btc_event_lag1	btc_event_sum_7	btc_event_mean_7	btc_event_vol_7	btc_event_sum_14	btc_event_mean_14	btc_event_vol_14	btc_event_sum_21	btc_event_mean_21	btc_event_vol_21	btc_event_sum_30	btc_event_mean_30	btc_event_vol_30	
# btc_p_event_lag1	btc_p_event_sum_7	btc_p_event_mean_7	btc_p_event_vol_7	btc_p_event_sum_14	btc_p_event_mean_14	btc_p_event_vol_14	btc_p_event_sum_21	btc_p_event_mean_21	btc_p_event_vol_21	btc_p_event_sum_30	btc_p_event_mean_30	btc_p_event_vol_30	
# btc_q_event_lag1	btc_q_event_sum_7	btc_q_event_mean_7	btc_q_event_vol_7	btc_q_event_sum_14	btc_q_event_mean_14	btc_q_event_vol_14	btc_q_event_sum_21	btc_q_event_mean_21	btc_q_event_vol_21	btc_q_event_sum_30	btc_q_event_mean_30	btc_q_event_vol_30	
# bip_event_lag1	bip_event_sum_7	bip_event_mean_7	bip_event_vol_7	bip_event_sum_14	bip_event_mean_14	bip_event_vol_14	bip_event_sum_21	bip_event_mean_21	bip_event_vol_21	bip_event_sum_30	bip_event_mean_30	bip_event_vol_30	
# bip_p_event_lag1	bip_p_event_sum_7	bip_p_event_mean_7	bip_p_event_vol_7	bip_p_event_sum_14	bip_p_event_mean_14	bip_p_event_vol_14	bip_p_event_sum_21	bip_p_event_mean_21	bip_p_event_vol_21	bip_p_event_sum_30	bip_p_event_mean_30	bip_p_event_vol_30	
# bip_q_event_lag1	bip_q_event_sum_7	bip_q_event_mean_7	bip_q_event_vol_7	bip_q_event_sum_14	bip_q_event_mean_14	bip_q_event_vol_14	bip_q_event_sum_21	bip_q_event_mean_21	bip_q_event_vol_21	bip_q_event_sum_30	bip_q_event_mean_30	bip_q_event_vol_30	
# btc_bip_event_lag1	btc_bip_event_sum_7	btc_bip_event_mean_7	btc_bip_event_vol_7	btc_bip_event_sum_14	btc_bip_event_mean_14	btc_bip_event_vol_14	btc_bip_event_sum_21	btc_bip_event_mean_21	btc_bip_event_vol_21	btc_bip_event_sum_30	btc_bip_event_mean_30	btc_bip_event_vol_30	
# btc_p_bip_p_event_lag1	btc_p_bip_p_event_sum_7	btc_p_bip_p_event_mean_7	btc_p_bip_p_event_vol_7	btc_p_bip_p_event_sum_14	btc_p_bip_p_event_mean_14	btc_p_bip_p_event_vol_14	btc_p_bip_p_event_sum_21	btc_p_bip_p_event_mean_21	btc_p_bip_p_event_vol_21	btc_p_bip_p_event_sum_30	btc_p_bip_p_event_mean_30	btc_p_bip_p_event_vol_30	
# btc_q_bip_q_event_lag1	btc_q_bip_q_event_sum_7	btc_q_bip_q_event_mean_7	btc_q_bip_q_event_vol_7	btc_q_bip_q_event_sum_14	btc_q_bip_q_event_mean_14	btc_q_bip_q_event_vol_14	btc_q_bip_q_event_sum_21	btc_q_bip_q_event_mean_21	btc_q_bip_q_event_vol_21	btc_q_bip_q_event_sum_30	btc_q_bip_q_event_mean_30	btc_q_bip_q_event_vol_30	
# btc_p_bip_event_lag1	btc_p_bip_event_sum_7	btc_p_bip_event_mean_7	btc_p_bip_event_vol_7	btc_p_bip_event_sum_14	btc_p_bip_event_mean_14	btc_p_bip_event_vol_14	btc_p_bip_event_sum_21	btc_p_bip_event_mean_21	btc_p_bip_event_vol_21	btc_p_bip_event_sum_30	btc_p_bip_event_mean_30	btc_p_bip_event_vol_30	
# btc_bip_p_event_lag1	btc_bip_p_event_sum_7	btc_bip_p_event_mean_7	btc_bip_p_event_vol_7	btc_bip_p_event_sum_14	btc_bip_p_event_mean_14	btc_bip_p_event_vol_14	btc_bip_p_event_sum_21	btc_bip_p_event_mean_21	btc_bip_p_event_vol_21	btc_bip_p_event_sum_30	btc_bip_p_event_mean_30	btc_bip_p_event_vol_30	
# btc_q_bip_event_lag1	btc_q_bip_event_sum_7	btc_q_bip_event_mean_7	btc_q_bip_event_vol_7	btc_q_bip_event_sum_14	btc_q_bip_event_mean_14	btc_q_bip_event_vol_14	btc_q_bip_event_sum_21	btc_q_bip_event_mean_21	btc_q_bip_event_vol_21	btc_q_bip_event_sum_30	btc_q_bip_event_mean_30	btc_q_bip_event_vol_30	
# btc_bip_q_event_lag1	btc_bip_q_event_sum_7	btc_bip_q_event_mean_7	btc_bip_q_event_vol_7	btc_bip_q_event_sum_14	btc_bip_q_event_mean_14	btc_bip_q_event_vol_14	btc_bip_q_event_sum_21	btc_bip_q_event_mean_21	btc_bip_q_event_vol_21	btc_bip_q_event_sum_30	btc_bip_q_event_mean_30	btc_bip_q_event_vol_30，

# =======
# 根据下面最优的模型 人工单个输入变量版本和图
# import warnings
# warnings.filterwarnings("ignore")

# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import matplotlib.pyplot as plt

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"

# # 使用滞后列
# PRICE_LAG_COL = "btc_ma_14d"
# EVENT_LAG_COL = "btc_p_event_cum_lag1"

# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_PNG_NEW = "btc_bass_price_eventfit_new.png"
# OUTPUT_PNG_CUM = "btc_bass_price_eventfit_cum.png"
# OUTPUT_CSV = "btc_bass_price_eventfit_results.csv"
# # ===================================

# # --------- 数据准备 ----------
# def load_data():
#     df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     cols_needed = [DATE_COL, NEW_COL, CUM_COL, PRICE_LAG_COL, EVENT_LAG_COL]
#     df = df[cols_needed].sort_values(DATE_COL).reset_index(drop=True)
#     df = df.fillna(method="ffill").fillna(0)

#     # 标准化滞后价格和事件
#     for col in [PRICE_LAG_COL, EVENT_LAG_COL]:
#         mean_val, std_val = df[col].mean(), df[col].std()
#         if std_val > 0:
#             df[col] = (df[col] - mean_val) / std_val
#         else:
#             print(f"⚠️ 列 {col} 标准差为0，跳过标准化。")

#     # log 变量及交互项
#     df["log_price"] = np.log1p(np.maximum(df[PRICE_LAG_COL], 0))
#     df["log_event"] = np.log1p(np.maximum(df[EVENT_LAG_COL], 0))
#     df["interaction"] = df[PRICE_LAG_COL] * df[EVENT_LAG_COL]
#     df["log_interaction"] = df["log_price"] * df["log_event"]

#     return df

# def select_date(df, start, end):
#     mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
#     return df.loc[mask].copy()

# # --------- 模型定义 ----------
# def dN_pred(N, p_t, q, m):
#     remaining_market = np.maximum(m - N, 0)
#     return (p_t + q * (N / m)) * remaining_market

# def compute_p_t(df, params, model_type):
#     P = df[PRICE_LAG_COL].values
#     E = df[EVENT_LAG_COL].values
#     LP = df["log_price"].values
#     LE = df["log_event"].values
#     I = df["interaction"].values
#     LI = df["log_interaction"].values

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

#     elif model_type == "logprice_add":
#         p0, alpha, beta, q, m = params
#         p_t = np.maximum(p0 + alpha * LP + beta * E, 0)

#     elif model_type == "logprice_logevent":
#         p0, alpha, beta, q, m = params
#         p_t = np.maximum(p0 + alpha * LP + beta * LE, 0)

#     elif model_type == "logprice_loginteract":
#         p0, alpha, beta, gamma, q, m = params
#         p_t = np.maximum(p0 + alpha * LP + beta * LE + gamma * LI, 0)

#     else:
#         raise ValueError(f"未知模型类型：{model_type}")

#     return p_t

# def compute_prediction(df, params, model_type):
#     p_t = compute_p_t(df, params, model_type)
#     N = df[CUM_COL].values
#     # 使用 N(t-1)
#     N_lag = np.roll(N, 1)
#     N_lag[0] = 0
#     return dN_pred(N_lag, p_t, params[-2], params[-1]), p_t  # q, m

# # --------- 残差函数 ----------
# def residuals(params, df, model_type):
#     dN_predicted, _ = compute_prediction(df, params, model_type)
#     dN_true = df[NEW_COL].values
#     if (params[-1] <= df[CUM_COL].max()) or (params[-2] < 0) or (params[0] < 0):
#         return np.ones(len(df)) * 1e6
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
#     return dN_true - dN_predicted

# # --------- 参数拟合 + 显著性检验 ----------
# def fit_bass(df, model_type):
#     m_guess = 1.2 * df[CUM_COL].max()
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

#     eps = 1e-6
#     n = len(df)
#     k = len(params)
#     y_pred, _ = compute_prediction(df, params, model_type)

#     J = []
#     for i in range(k):
#         params_eps = params.copy()
#         params_eps[i] += eps
#         y_pred_eps, _ = compute_prediction(df, params_eps, model_type)
#         J.append((y_pred_eps - y_pred) / eps)
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

#     names_dict = {
#         "linear_add": ["p0", "alpha(price)", "beta(event)", "q", "m"],
#         "log_event": ["p0", "alpha(price)", "beta(logE)", "q", "m"],
#         "linear_interact": ["p0", "alpha(price)", "beta(event)", "gamma(inter)", "q", "m"],
#         "log_interact": ["p0", "alpha(price)", "beta(logE)", "gamma(inter)", "q", "m"],
#         "logprice_add": ["p0", "alpha(logP)", "beta(event)", "q", "m"],
#         "logprice_logevent": ["p0", "alpha(logP)", "beta(logE)", "q", "m"],
#         "logprice_loginteract": ["p0", "alpha(logP)", "beta(logE)", "gamma(logP*logE)", "q", "m"]
#     }
#     names = names_dict[model_type]

#     print("\n--- 参数显著性检验 ---")
#     for name, val, se_i, t_i, p_i in zip(names, params, se, tvals, pvals):
#         print(f"{name:20s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")
#     return res

# # --------- 主程序 ----------
# def main():
#     df = load_data()
#     df = select_date(df, START_DATE, END_DATE)

#     models = [
#         "linear_add", "log_event", "linear_interact", "log_interact",
#         "logprice_add", "logprice_logevent", "logprice_loginteract"
#     ]

#     results, valid_models = [], []

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


# =======
# 较上面代码加入了变量组合生成结果

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt
import itertools

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"

# BTC
# PRICE_LAG_COLS = [
#     "btc_price_lag1","ln_btc_price_lag1","btc_return_1d",
#     "btc_return_7d","btc_vol_7d","btc_ma_7d","btc_trend_7d",
#     "btc_return_14d","btc_vol_14d","btc_ma_14d","btc_trend_14d",
#     "btc_return_21d","btc_vol_21d","btc_ma_21d","btc_trend_21d",
#     "btc_return_30d","btc_vol_30d","btc_ma_30d","btc_trend_30d"
# ]

PRICE_LAG_COLS = [
    "btc_price_lag1","ln_btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
]

# EVENT_LAG_COLS = [
#     "btc_event_lag1","btc_event_sum_7","btc_event_mean_7","btc_event_vol_7",
#     "btc_event_sum_14","btc_event_mean_14","btc_event_vol_14",
#     "btc_event_sum_21","btc_event_mean_21","btc_event_vol_21",
#     "btc_event_sum_30","btc_event_mean_30","btc_event_vol_30",
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_event_sum_14","btc_p_event_mean_14","btc_p_event_vol_14",
#     "btc_p_event_sum_21","btc_p_event_mean_21","btc_p_event_vol_21",
#     "btc_p_event_sum_30","btc_p_event_mean_30","btc_p_event_vol_30",
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7","btc_q_event_vol_7",
#     "btc_q_event_sum_14","btc_q_event_mean_14","btc_q_event_vol_14",
#     "btc_q_event_sum_21","btc_q_event_mean_21","btc_q_event_vol_21",
#     "btc_q_event_sum_30","btc_q_event_mean_30","btc_q_event_vol_30",
#     "bip_event_lag1","bip_event_sum_7","bip_event_mean_7","bip_event_vol_7",
#         "bip_event_sum_14","bip_event_mean_14","bip_event_vol_14",
#         "bip_event_sum_21","bip_event_mean_21","bip_event_vol_21",
#         "bip_event_sum_30","bip_event_mean_30","bip_event_vol_30",
#         "bip_p_event_lag1","bip_p_event_sum_7","bip_p_event_mean_7","bip_p_event_vol_7",
#         "bip_p_event_sum_14","bip_p_event_mean_14","bip_p_event_vol_14",
#         "bip_p_event_sum_21","bip_p_event_mean_21","bip_p_event_vol_21",
#         "bip_p_event_sum_30","bip_p_event_mean_30","bip_p_event_vol_30",
#         "bip_q_event_lag1","bip_q_event_sum_7","bip_q_event_mean_7","bip_q_event_vol_7",
#         "bip_q_event_sum_14","bip_q_event_mean_14","bip_q_event_vol_14",
#         "bip_q_event_sum_21","bip_q_event_mean_21","bip_q_event_vol_21",
#         "bip_q_event_sum_30","bip_q_event_mean_30","bip_q_event_vol_30",
#         "btc_bip_event_lag1","btc_bip_event_sum_7","btc_bip_event_mean_7","btc_bip_event_vol_7",
#         "btc_bip_event_sum_14","btc_bip_event_mean_14","btc_bip_event_vol_14",
#         "btc_bip_event_sum_21","btc_bip_event_mean_21","btc_bip_event_vol_21",
#         "btc_bip_event_sum_30","btc_bip_event_mean_30","btc_bip_event_vol_30",
#         "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#         "btc_p_bip_p_event_sum_14","btc_p_bip_p_event_mean_14","btc_p_bip_p_event_vol_14",
#         "btc_p_bip_p_event_sum_21","btc_p_bip_p_event_mean_21","btc_p_bip_p_event_vol_21",
#         "btc_p_bip_p_event_sum_30","btc_p_bip_p_event_mean_30","btc_p_bip_p_event_vol_30",
#         "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7","btc_q_bip_q_event_vol_7",
#         "btc_q_bip_q_event_sum_14","btc_q_bip_q_event_mean_14","btc_q_bip_q_event_vol_14",
#         "btc_q_bip_q_event_sum_21","btc_q_bip_q_event_mean_21","btc_q_bip_q_event_vol_21",
#         "btc_q_bip_q_event_sum_30","btc_q_bip_q_event_mean_30","btc_q_bip_q_event_vol_30",
#         "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7",
#         "btc_p_bip_event_sum_14","btc_p_bip_event_mean_14","btc_p_bip_event_vol_14",
#         "btc_p_bip_event_sum_21","btc_p_bip_event_mean_21","btc_p_bip_event_vol_21",
#         "btc_p_bip_event_sum_30","btc_p_bip_event_mean_30","btc_p_bip_event_vol_30",
#         "btc_bip_p_event_lag1","btc_bip_p_event_sum_7","btc_bip_p_event_mean_7","btc_bip_p_event_vol_7",
#         "btc_bip_p_event_sum_14","btc_bip_p_event_mean_14","btc_bip_p_event_vol_14",
#         "btc_bip_p_event_sum_21","btc_bip_p_event_mean_21","btc_bip_p_event_vol_21",
#         "btc_bip_p_event_sum_30","btc_bip_p_event_mean_30","btc_bip_p_event_vol_30",
#         "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7","btc_q_bip_event_vol_7",
#         "btc_q_bip_event_sum_14","btc_q_bip_event_mean_14","btc_q_bip_event_vol_14",
#         "btc_q_bip_event_sum_21","btc_q_bip_event_mean_21","btc_q_bip_event_vol_21",
#         "btc_q_bip_event_sum_30","btc_q_bip_event_mean_30","btc_q_bip_event_vol_30",
#         "btc_bip_q_event_lag1","btc_bip_q_event_sum_7","btc_bip_q_event_mean_7","btc_bip_q_event_vol_7",
#         "btc_bip_q_event_sum_14","btc_bip_q_event_mean_14","btc_bip_q_event_vol_14",
#         "btc_bip_q_event_sum_21","btc_bip_q_event_mean_21","btc_bip_q_event_vol_21",
#         "btc_bip_q_event_sum_30","btc_bip_q_event_mean_30","btc_bip_q_event_vol_30"
# ]

EVENT_LAG_COLS = [
    "btc_event_lag1","btc_event_sum_7","btc_event_mean_7","btc_event_vol_7",
    "btc_event_sum_14","btc_event_mean_14","btc_event_cum_lag1","btc_p_event_cum_lag1","btc_q_event_cum_lag1",
    "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
    "btc_p_event_sum_14","btc_p_event_mean_14","btc_p_event_vol_14", 
    "bip_event_sum_14","bip_event_mean_14","bip_event_vol_14",
    "bip_event_sum_21","bip_event_mean_21","bip_event_vol_21",
    "bip_event_sum_30","bip_event_mean_30","bip_event_vol_30",
    "bip_p_event_lag1","bip_p_event_sum_7","bip_p_event_mean_7","bip_p_event_vol_7",
    "bip_p_event_sum_14","bip_p_event_mean_14","bip_p_event_vol_14",
    "bip_p_event_sum_21","bip_p_event_mean_21","bip_p_event_vol_21",
    "bip_p_event_sum_30","bip_p_event_mean_30","bip_p_event_vol_30",
    "btc_bip_event_lag1","btc_bip_event_sum_7","btc_bip_event_mean_7","btc_bip_event_vol_7",
    "btc_bip_event_sum_14","btc_bip_event_mean_14","btc_bip_event_vol_14",
    "btc_bip_event_sum_21","btc_bip_event_mean_21","btc_bip_event_vol_21",
    "btc_bip_event_sum_30","btc_bip_event_mean_30","btc_bip_event_vol_30",
    "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
    "btc_p_bip_p_event_sum_14","btc_p_bip_p_event_mean_14","btc_p_bip_p_event_vol_14",
    "btc_p_bip_p_event_sum_21","btc_p_bip_p_event_mean_21","btc_p_bip_p_event_vol_21"
]

# ETH
# PRICE_LAG_COLS = [
#     "eth_price_lag1","ln_eth_price_lag1","eth_return_1d",
#     "eth_return_7d","eth_vol_7d","eth_ma_7d","eth_trend_7d",
#     "eth_return_14d","eth_vol_14d","eth_ma_14d","eth_trend_14d",
#     "eth_return_21d","eth_vol_21d","eth_ma_21d","eth_trend_21d",
#     "eth_return_30d","eth_vol_30d","eth_ma_30d","eth_trend_30d"
# ]

# EVENT_LAG_COLS = [
#     # === 1. ETH Event Features ===
#     "eth_event_lag1", "eth_event_sum_7", "eth_event_mean_7", "eth_event_vol_7",
#     "eth_event_sum_14", "eth_event_mean_14", "eth_event_vol_14",
#     "eth_event_sum_21", "eth_event_mean_21", "eth_event_vol_21",
#     "eth_event_sum_30", "eth_event_mean_30", "eth_event_vol_30",

#     # === 2. ETH Price Event Features (eth_p) ===
#     "eth_p_event_lag1", "eth_p_event_sum_7", "eth_p_event_mean_7", "eth_p_event_vol_7",
#     "eth_p_event_sum_14", "eth_p_event_mean_14", "eth_p_event_vol_14",
#     "eth_p_event_sum_21", "eth_p_event_mean_21", "eth_p_event_vol_21",
#     "eth_p_event_sum_30", "eth_p_event_mean_30", "eth_p_event_vol_30",

#     # === 3. ETH Quantity/Volume Event Features (eth_q) ===
#     "eth_q_event_lag1", "eth_q_event_sum_7", "eth_q_event_mean_7", "eth_q_event_vol_7",
#     "eth_q_event_sum_14", "eth_q_event_mean_14", "eth_q_event_vol_14",
#     "eth_q_event_sum_21", "eth_q_event_mean_21", "eth_q_event_vol_21",
#     "eth_q_event_sum_30", "eth_q_event_mean_30", "eth_q_event_vol_30",

#     # === 4. EIP Event Features (General) ===
#     "eip_event_lag1", "eip_event_sum_7", "eip_event_mean_7", "eip_event_vol_7",
#     "eip_event_sum_14", "eip_event_mean_14", "eip_event_vol_14",
#     "eip_event_sum_21", "eip_event_mean_21", "eip_event_vol_21",
#     "eip_event_sum_30", "eip_event_mean_30", "eip_event_vol_30",

#     # === 5. EIP Price Event Features (eip_p) ===
#     "eip_p_event_lag1", "eip_p_event_sum_7", "eip_p_event_mean_7", "eip_p_event_vol_7",
#     "eip_p_event_sum_14", "eip_p_event_mean_14", "eip_p_event_vol_14",
#     "eip_p_event_sum_21", "eip_p_event_mean_21", "eip_p_event_vol_21",
#     "eip_p_event_sum_30", "eip_p_event_mean_30", "eip_p_event_vol_30",

#     # === 6. EIP Quantity/Volume Event Features (eip_q) ===
#     "eip_q_event_lag1", "eip_q_event_sum_7", "eip_q_event_mean_7", "eip_q_event_vol_7",
#     "eip_q_event_sum_14", "eip_q_event_mean_14", "eip_q_event_vol_14",
#     "eip_q_event_sum_21", "eip_q_event_mean_21", "eip_q_event_vol_21",
#     "eip_q_event_sum_30", "eip_q_event_mean_30", "eip_q_event_vol_30",

#     # === 7. ETH-EIP Combined Event Features ===
#     "eth_eip_event_lag1", "eth_eip_event_sum_7", "eth_eip_event_mean_7", "eth_eip_event_vol_7",
#     "eth_eip_event_sum_14", "eth_eip_event_mean_14", "eth_eip_event_vol_14",
#     "eth_eip_event_sum_21", "eth_eip_event_mean_21", "eth_eip_event_vol_21",
#     "eth_eip_event_sum_30", "eth_eip_event_mean_30", "eth_eip_event_vol_30",

#     # === 8. ETC-P-EIP-P Event Features (etc_p_eip_p) ===
#     "etc_p_eip_p_event_lag1", "etc_p_eip_p_event_sum_7", "etc_p_eip_p_event_mean_7", "etc_p_eip_p_event_vol_7",
#     "etc_p_eip_p_event_sum_14", "etc_p_eip_p_event_mean_14", "etc_p_eip_p_event_vol_14",
#     "etc_p_eip_p_event_sum_21", "etc_p_eip_p_event_mean_21", "etc_p_eip_p_event_vol_21",
#     "etc_p_eip_p_event_sum_30", "etc_p_eip_p_event_mean_30", "etc_p_eip_p_event_vol_30",

#     # === 9. ETC-Q-EIP-Q Event Features (etc_q_eip_q) ===
#     "etc_q_eip_q_event_lag1", "etc_q_eip_q_event_sum_7", "etc_q_eip_q_event_mean_7", "etc_q_eip_q_event_vol_7",
#     "etc_q_eip_q_event_sum_14", "etc_q_eip_q_event_mean_14", "etc_q_eip_q_event_vol_14",
#     "etc_q_eip_q_event_sum_21", "etc_q_eip_q_event_mean_21", "etc_q_eip_q_event_vol_21",
#     "etc_q_eip_q_event_sum_30", "etc_q_eip_q_event_mean_30", "etc_q_eip_q_event_vol_30",

#     # === 10. ETC-P-EIP Event Features (etc_p_eip) ===
#     "etc_p_eip_event_lag1", "etc_p_eip_event_sum_7", "etc_p_eip_event_mean_7", "etc_p_eip_event_vol_7",
#     "etc_p_eip_event_sum_14", "etc_p_eip_event_mean_14", "etc_p_eip_event_vol_14",
#     "etc_p_eip_event_sum_21", "etc_p_eip_event_mean_21", "etc_p_eip_event_vol_21",
#     "etc_p_eip_event_sum_30", "etc_p_eip_event_mean_30", "etc_p_eip_event_vol_30",

#     # === 11. ETC-EIP-P Event Features (etc_eip_p) ===
#     "etc_eip_p_event_lag1", "etc_eip_p_event_sum_7", "etc_eip_p_event_mean_7", "etc_eip_p_event_vol_7",
#     "etc_eip_p_event_sum_14", "etc_eip_p_event_mean_14", "etc_eip_p_event_vol_14",
#     "etc_eip_p_event_sum_21", "etc_eip_p_event_mean_21", "etc_eip_p_event_vol_21",
#     "etc_eip_p_event_sum_30", "etc_eip_p_event_mean_30", "etc_eip_p_event_vol_30",

#     # === 12. ETC-Q-EIP Event Features (etc_q_eip) ===
#     "etc_q_eip_event_lag1", "etc_q_eip_event_sum_7", "etc_q_eip_event_mean_7", "etc_q_eip_event_vol_7",
#     "etc_q_eip_event_sum_14", "etc_q_eip_event_mean_14", "etc_q_eip_event_vol_14",
#     "etc_q_eip_event_sum_21", "etc_q_eip_event_mean_21", "etc_q_eip_event_vol_21",
#     "etc_q_eip_event_sum_30", "etc_q_eip_event_mean_30", "etc_q_eip_event_vol_30",

#     # === 13. ETC-EIP-Q Event Features (etc_eip_q) ===
#     "etc_eip_q_event_lag1", "etc_eip_q_event_sum_7", "etc_eip_q_event_mean_7", "etc_eip_q_event_vol_7",
#     "etc_eip_q_event_sum_14", "etc_eip_q_event_mean_14", "etc_eip_q_event_vol_14",
#     "etc_eip_q_event_sum_21", "etc_eip_q_event_mean_21", "etc_eip_q_event_vol_21",
#     "etc_eip_q_event_sum_30", "etc_eip_q_event_mean_30", "etc_eip_q_event_vol_30",
# ]

START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_CSV = "btc_bass_price_eventfit_results_all_p.csv"
OUTPUT_PNG_NEW = "btc_bass_price_eventfit_new.png"
OUTPUT_PNG_CUM = "btc_bass_price_eventfit_cum.png"
# ===================================

# --------- 数据加载 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

# --------- Bass 模型核心 ----------
def dN_pred(N, p_t, q, m):
    remaining = np.maximum(m - N, 0)
    return (p_t + q * (N / m)) * remaining

def compute_p_t(df, params, model_type):
    P = df["price"].values
    E = df["event"].values
    LP = df["log_price"].values
    LE = df["log_event"].values
    I = df["interaction"].values
    LI = df["log_interaction"].values

    if model_type == "linear_add":
        p0, alpha, beta, q, m = params
        return np.maximum(p0 + alpha * P + beta * E, 0)
    elif model_type == "log_event":
        p0, alpha, beta, q, m = params
        return np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E,0)),0)
    elif model_type == "linear_interact":
        p0, alpha, beta, gamma, q, m = params
        return np.maximum(p0 + alpha*P + beta*E + gamma*I,0)
    elif model_type == "log_interact":
        p0, alpha, beta, gamma, q, m = params
        return np.maximum(p0 + alpha*P + beta*np.log1p(np.maximum(E,0)) + gamma*I,0)
    elif model_type == "logprice_add":
        p0, alpha, beta, q, m = params
        return np.maximum(p0 + alpha*LP + beta*E,0)
    elif model_type == "logprice_logevent":
        p0, alpha, beta, q, m = params
        return np.maximum(p0 + alpha*LP + beta*LE,0)
    elif model_type == "logprice_loginteract":
        p0, alpha, beta, gamma, q, m = params
        return np.maximum(p0 + alpha*LP + beta*LE + gamma*LI,0)
    else:
        raise ValueError(f"未知模型类型: {model_type}")

def compute_prediction(df, params, model_type):
    p_t = compute_p_t(df, params, model_type)
    N = df[CUM_COL].values
    N_lag = np.roll(N,1); N_lag[0]=0
    return dN_pred(N_lag, p_t, params[-2], params[-1]), p_t

def residuals(params, df, model_type):
    dN_predicted, _ = compute_prediction(df, params, model_type)
    dN_true = df[NEW_COL].values
    if (params[-1]<=df[CUM_COL].max()) or (params[-2]<0) or (params[0]<0):
        return np.ones(len(df))*1e6
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted,0):
        return np.ones(len(df))*1e6
    return dN_true - dN_predicted

# --------- 拟合与显著性 ----------
def fit_bass(df, model_type="linear_add"):
    try:
        m_guess = 1.2*df[CUM_COL].max()
        if "interact" in model_type:
            init = [1e-4,0.01,0.01,0.01,0.01,m_guess]
            bounds=([0,-10,-10,-10,0,0.9*m_guess],[1,10,10,10,1,20*m_guess])
        else:
            init=[1e-4,0.01,0.01,0.01,m_guess]
            bounds=([0,-10,-10,0,0.9*m_guess],[1,10,10,1,20*m_guess])

        res = least_squares(residuals, init, bounds=bounds, args=(df, model_type), method="trf")
        if not res.success:
            return None

        params = res.x
        n = len(df); k = len(params)
        eps = 1e-6
        y_pred,_ = compute_prediction(df, params, model_type)

        J = []
        for i in range(k):
            p_eps = params.copy(); p_eps[i]+=eps
            y_eps,_ = compute_prediction(df,p_eps,model_type)
            J.append((y_eps - y_pred)/eps)
        J = np.array(J).T
        cond = np.linalg.cond(J.T@J)

        residuals_vec = df[NEW_COL].values - y_pred
        sigma2 = np.sum(residuals_vec**2)/(n-k)
        try:
            cov = sigma2*np.linalg.inv(J.T@J + 1e-6*np.eye(J.shape[1]))
            se = np.sqrt(np.diag(cov))
        except:
            se = np.full(k, np.nan)

        tvals = params / se
        pvals = 2*(1 - t.cdf(np.abs(tvals), df=n-k))
        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        return res
    except Exception as e:
        print(f"⚠️ 模型 {model_type} 拟合异常: {e}")
        return None


# --------- 主程序 ----------
def main():
    df_all = load_data()
    df_all = select_date(df_all, START_DATE, END_DATE)

    models = ["linear_add","log_event","linear_interact","log_interact",
              "logprice_add","logprice_logevent","logprice_loginteract"]

    results_list = []

    # 遍历所有 PRICE_LAG × EVENT_LAG 组合
    for price_col, event_col in itertools.product(PRICE_LAG_COLS, EVENT_LAG_COLS):
        print(f"\n=== 拟合组合: price={price_col}, event={event_col} ===")

        df = df_all[[DATE_COL, NEW_COL, CUM_COL, price_col, event_col]].copy()
        df = df.rename(columns={price_col:"price", event_col:"event"})

        # 标准化 + log + interaction
        for col in ["price","event"]:
            mean_val,std_val = df[col].mean(), df[col].std()
            if std_val>0:
                df[col] = (df[col]-mean_val)/std_val
        df["log_price"] = np.log1p(np.maximum(df["price"],0))
        df["log_event"] = np.log1p(np.maximum(df["event"],0))
        df["interaction"] = df["price"]*df["event"]
        df["log_interaction"] = df["log_price"]*df["log_event"]

        for model_type in models:
            print(f"-- 拟合模型: {model_type}")
            res = fit_bass(df, model_type)
            if res is None or not getattr(res, 'success', True):
                print(f"⚠️ 模型 {model_type} 拟合失败，跳过")
                continue

            dN_predicted,_ = compute_prediction(df,res.x,model_type)
            cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
            rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted)**2))
            sse = np.sum((df[NEW_COL].values - dN_predicted)**2)

            # 保存结果
            result = {"price_col":price_col,"event_col":event_col,"model":model_type,
                    "SSE":sse,"RMSE":rmse}
            for i,val in enumerate(res.x):
                result[f"param_{i}"] = val
            for i,se_val,t_val,p_val in zip(range(len(res.se)),res.se,res.tvals,res.pvals):
                result[f"se_{i}"]=se_val
                result[f"t_{i}"]=t_val
                result[f"p_{i}"]=p_val
            results_list.append(result)


    # 保存 CSV
    pd.DataFrame(results_list).to_csv(OUTPUT_CSV,index=False)
    print(f"\n✅ 所有组合拟合结果保存至 {OUTPUT_CSV}")

if __name__=="__main__":
    main()
