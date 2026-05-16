# # 在12的基础上进行竞争模型

# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============================= 路径配置（请修改成你的真实路径）=============================
# # 主链：BTC（你原来那个文件，里面放的是 BTC 数据）
# BTC_MAIN_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"

# # 竞争对手各自独立文件（请确保每份文件都有 date 列）
# COMPETITOR_FILES = {
#     "eth":  "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv",      # 必须有 date, eth_new_developers, eth_cum_users
#     "ltc":  "/home/lab0/survival_diffusion_github/Bitcoin_compete/litecoin_first_actor_count.csv",      # date, litecoin_new_developers, litecoin_cum_users
#     "doge": "/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_first_actor_count.csv",     # date, dogecoin_new_developers, dogecoin_cum_users
#     "bch":  "/home/lab0/survival_diffusion_github/Bitcoin/bitcoinabc_first_actor_count.csv",      # date, bitcoinabc_new_developers, bitcoinabc_cum_users
#     "bsv":  "/home/lab0/survival_diffusion_github/Bitcoin/bitcoinsv_first_actor_count.csv"       # date, bitcoinsv_new_developers, bitcoinsv_cum_users
# }

# # 对手文件中列名映射（防止文件名不一致）
# COLUMN_MAPPING = {
#     "eth":  ("eth_new_developers",   "eth_cum_users"),
#     "ltc":  ("litecoin_new_developers", "litecoin_cum_users"),
#     "doge": ("dogecoin_new_developers",  "dogecoin_cum_users"),
#     "bch":  ("bitcoinabc_new_developers","bitcoinabc_cum_users"),
#     "bsv":  ("bitcoinsv_new_developers", "bitcoinsv_cum_users")
# }

# # <<< FINAL VERSION >>> 剥夺强度（你重叠数据算出的最准值）
# LAMBDA_COMPETITION = 0.1   # BTC 被这5个对手共同剥夺的比例

# DATE_COL = "date"
# NEW_COL = "btc_new_developers"      # 主文件里 BTC 的新增列
# CUM_COL = "btc_cum_users"           # 主文件里 BTC 的累计列
# START_DATE = "2017-01-01"
# END_DATE   = "2019-01-01"
# OUTPUT_CSV = "btc_bass_with_real_competition_2017_2019.csv"

# # ============================= 你的 BTC 事件与价格列（请按实际列名改）=============================
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7"
#     # "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#     # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
# ]

# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7"
#     # "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
#     # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
# ]
# PRICE_LAG_COLS = ["btc_price_lag1", "btc_ma_7d", "btc_ma_14d", "btc_ma_21d", "btc_ma_30d"]

# # ============================= 工具函数（完全不变）=============================
# def normalize(x):
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     return (x - mean) / (std + 1e-12) if std > 1e-12 else x - mean

# def compute_q_t_from_array(event_arr, q_params, q_form):
#     q0, beta = q_params
#     ev = normalize(event_arr)
#     if q_form == "linear":
#         return np.maximum(q0 + beta * ev, 1e-8)
#     elif q_form == "log":
#         return np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 1e-8)
#     elif q_form == "exp":
#         return np.maximum(q0 * np.exp(beta * ev), 1e-8)

# def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
#     ev = normalize(df[p_event_col].values)
#     if p_model == "additive":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * ev
#     elif p_model == "nonlinear_event":
#         p0, alpha, beta = params[:3]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
#     elif p_model == "interaction_linear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)
#     elif p_model == "interaction_nonlinear":
#         p0, alpha, beta, gamma = params[:4]
#         p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)
#     return np.maximum(p_t, 1e-8)

# # <<< FINAL VERSION >>> 核心：带真实竞争剥夺的 Bass 增量
# def dN_pred_with_competition(N_lag, p_t_arr, q_t_arr, m, competitor_cum_lag_sum):
#     remaining_base = np.maximum(m - N_lag, 0)
#     penalty = LAMBDA_COMPETITION * competitor_cum_lag_sum
#     remaining = np.maximum(remaining_base - penalty, 0)
#     return (p_t_arr + q_t_arr * (N_lag / m)) * remaining

# # ============================= 预测与残差（小改）=============================
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, competitor_lag):
#     if p_model in ["additive", "nonlinear_event"]:
#         p_params = params[:3]
#         q0, beta_q, m = params[3:6]
#     else:
#         p_params = params[:4]
#         q0, beta_q, m = params[4:7]

#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
#     N_lag = df["N_lag"].values

#     dN = dN_pred_with_competition(N_lag, p_t, q_t, m, competitor_lag)
#     return dN, p_t, q_t

# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, competitor_lag):
#     dN_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, competitor_lag)
#     return df[NEW_COL].values - dN_pred

# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, competitor_lag):
#     try:
#         m_guess = max(1.3 * df[CUM_COL].max(), df[CUM_COL].max() + 5e4)
#         if p_model in ["additive", "nonlinear_event"]:
#             init = [0.001, 0.02, 0.01, 0.05, 0.02, m_guess]
#             bounds = ([0, -5, -5, 0, -5, 0.9*m_guess], [0.5, 5, 5, 2, 5, 30*m_guess])
#         else:
#             init = [0.001, 0.02, 0.01, 0.01, 0.05, 0.02, m_guess]
#             bounds = ([0, -5, -5, -5, 0, -5, 0.9*m_guess], [0.5, 5, 5, 5, 2, 5, 30*m_guess])

#         res = least_squares(residuals_pair, init, bounds=bounds, max_nfev=4000,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, competitor_lag),
#                             method="trf", xtol=1e-10, ftol=1e-10)

#         if not res.success or res.cost > 1e9:
#             return None

#         params = res.x
#         dN_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, competitor_lag)
#         rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#         res.rmse = rmse
#         return res
#     except Exception as e:
#         print("拟合出错:", e)
#         return None

# # ============================= 主程序：加载5个独立对手文件 + 合并 =============================
# def main():
#     print("正在读取 BTC 主文件...")
#     df_btc = pd.read_csv(BTC_MAIN_PATH, parse_dates=[DATE_COL])
    
#     # 自动修复列名
#     if "eth_new_developers" in df_btc.columns:
#         df_btc = df_btc.rename(columns={
#             "eth_new_developers": "btc_new_developers",
#             "eth_cum_users": "btc_cum_users"
#         })
#         print("已自动修复列名为 btc_ 开头")

#     df_btc = df_btc.sort_values(DATE_COL).reset_index(drop=True)

#     # 先切时间窗口（关键！先切再算对手）
#     mask = (df_btc[DATE_COL] >= pd.to_datetime(START_DATE)) & (df_btc[DATE_COL] <= pd.to_datetime(END_DATE))
#     df = df_btc.loc[mask].copy().reset_index(drop=True)   # ← 重置索引！
    
#     # 再用 df 的 date 去对齐对手（这样长度一定一样）
#     print("正在读取5个竞争对手文件并对齐到 [2017-2019] 时间窗口...")
#     competitor_cum_sum = pd.Series(0.0, index=df.index)   # ← 用 df 的长度！

#     for name, path in COMPETITOR_FILES.items():
#         try:
#             df_comp = pd.read_csv(path, parse_dates=["date"])
#             _, cum_col = COLUMN_MAPPING[name]
#             df_comp = df_comp[["date", cum_col]].rename(columns={cum_col: "cum_comp"})
            
#             # 用 df 的 date 作为主时间轴
#             df_merged = pd.merge(df[[DATE_COL]], df_comp, left_on=DATE_COL, right_on="date", how="left")
#             df_merged["cum_comp"] = df_merged["cum_comp"].ffill().fillna(0)
#             competitor_cum_sum += df_merged["cum_comp"]
#             print(f"成功加载 {name}（最大 {df_merged['cum_comp'].max():.0f}）")
#         except Exception as e:
#             print(f"加载 {name} 失败：{e}")

#     competitor_cum_lag_sum = competitor_cum_sum.shift(1).fillna(0).values  # 长度 = len(df)

#     # N_lag
#     df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0])

#     results = []
#     combos_done = 0

#     for p_event_col in P_EVENT_LIST:
#         for q_event_col in Q_EVENT_LIST:
#             for price_col in PRICE_LAG_COLS:
#                 if price_col not in df.columns:
#                     continue
#                 raw_price = df[price_col].values.astype(float)
#                 price_transforms = {
#                     "linear": normalize(raw_price),
#                     "log": normalize(np.log1p(raw_price)),
#                     "exp": normalize(np.exp(np.clip(raw_price/1e4, -10, 10)))
#                 }
#                 for pt_name, price_arr in price_transforms.items():
#                     for p_model in ["additive", "interaction_linear"]:
#                         for q_form in ["linear", "log"]:
#                             tag = f"{p_event_col}|{q_event_col}|{price_col}({pt_name})|{p_model}|{q_form}"
#                             print(f"拟合中（λ={LAMBDA_COMPETITION}）：{tag}")

#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col,
#                                                 p_model, q_form, competitor_cum_lag_sum)

#                             if res:
#                                 combos_done += 1
#                                 row = {
#                                     "P_event": p_event_col, "Q_event": q_event_col,
#                                     "price_col": price_col, "price_tf": pt_name,
#                                     "p_model": p_model, "q_form": q_form,
#                                     "RMSE": res.rmse, "λ": LAMBDA_COMPETITION,
#                                     "note": "BTC_vs_ETH_LTC_DOGE_BCH_BSV_real_files"
#                                 }
#                                 param_names = ["p0","alpha","beta","gamma","q0","beta_q","m"] if "interaction" in p_model else ["p0","alpha","beta","q0","beta_q","m"]
#                                 for i, n in enumerate(param_names[:len(res.x)]):
#                                     row[n] = float(res.x[i])
#                                 results.append(row)

#     pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#     print(f"\n完成！成功拟合 {combos_done} 个模型，结果保存至：{OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import math
import sys

# ============================= 路径配置 =============================
# 主链：BTC
BTC_MAIN_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"

# 竞争对手各自独立文件
COMPETITOR_FILES = {
    # "eth":  "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv",
    # "ltc":  "/home/lab0/survival_diffusion_github/Bitcoin_compete/litecoin_first_actor_count.csv",
    # "doge": "/home/lab0/survival_diffusion_github/Bitcoin_compete/dogecoin_first_actor_count.csv",
    "bch":  "/home/lab0/survival_diffusion_github/Bitcoin/bitcoinabc_first_actor_count.csv",
    "bsv":  "/home/lab0/survival_diffusion_github/Bitcoin/bitcoinsv_first_actor_count.csv"
}

# 对手文件中列名映射
COLUMN_MAPPING = {
    # "eth":  ("eth_new_developers",   "eth_cum_users"),
    # "ltc":  ("litecoin_new_developers", "litecoin_cum_users"),
    # "doge": ("dogecoin_new_developers",  "dogecoin_cum_users"),
    "bch":  ("bitcoinabc_new_developers","bitcoinabc_cum_users"),
    "bsv":  ("bitcoinsv_new_developers", "bitcoinsv_cum_users")
}

# ============= 参数配置 =============
DATE_COL = "date"
NEW_COL = "btc_new_developers"  # 主链的新增开发者列
CUM_COL = "btc_cum_users"        # 主链的累计用户列

START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_CSV = "btc_bass_competition_results.csv"

# ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
P_EVENT_LIST = [
    "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7"
    "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#   # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
]

Q_EVENT_LIST = [
     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7"
     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
#     # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
]

PRICE_LAG_COLS = ["btc_price_lag1", "btc_ma_7d", "btc_ma_14d", "btc_ma_21d"]

# P_EVENT_LIST = [
#     "eth_p_event_lag1","eth_p_event_sum_7","eth_p_event_mean_7","eth_p_event_vol_7",
#     "eth_p_eip_p_event_lag1","eth_p_eip_p_event_sum_7","eth_p_eip_p_event_mean_7","eth_p_eip_p_event_vol_7",
#     "eth_p_eip_event_lag1","eth_p_eip_event_sum_7","eth_p_eip_event_mean_7","eth_p_eip_event_vol_7"
# ]

# Q_EVENT_LIST = [
#     "eth_q_event_lag1","eth_q_event_sum_7","eth_q_event_mean_7",
#     "eth_q_eip_q_event_lag1","eth_q_eip_q_event_sum_7","eth_q_eip_q_event_mean_7",
#     "eth_q_eip_event_lag1","eth_q_eip_event_sum_7","eth_q_eip_event_mean_7"
# ]

# # ============= 价格滞后变量 =============
# PRICE_LAG_COLS = [
#     "eth_price_lag1","eth_ma_7d","eth_ma_14d","eth_ma_21d","eth_ma_30d"
# ]

# ============= 工具函数 =============
def normalize(x):
    x = np.array(x, dtype=float)
    mean = np.mean(x)
    std = np.std(x)
    if std <= 0:
        return x - mean
    return (x - mean) / (std + 1e-12)

def compute_q_t_from_array(event_arr, q_params, q_form):
    q0, beta = q_params
    ev = normalize(event_arr)
    if q_form == "linear":
        q_t = np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":
        q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        q_t = q0 * np.exp(beta * ev)
    else:
        raise ValueError("未知 q_form")
    return q_t

def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    """
    params: for p_model "additive"/"nonlinear_event": [p0, alpha, beta, q0, beta_q, lambda, m]
            for interaction variants: [p0, alpha, beta, gamma, q0, beta_q, lambda, m]
    """
    ev = normalize(df[p_event_col].values)

    if p_model == "additive":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * ev

    elif p_model == "nonlinear_event":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))

    elif p_model == "interaction_linear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)

    elif p_model == "interaction_nonlinear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)

    else:
        raise ValueError("未知 p_model")
    return np.maximum(p_t, 0)

# ============= 竞争Bass模型增量（加入竞争项）=============
def dN_pred_competition(N_lag, competitor_sum_lag, p_t_arr, q_t_arr, lambda_comp, m):
    """
    竞争Bass模型：
    ΔN_i(t) = [p(t) + q(t) × N_i(t-1)/m] × (m - N_i(t-1) - λ × ΣN_竞争对手(t-1))
    
    参数:
        N_lag: N_i(t-1) 主链的滞后累计用户
        competitor_sum_lag: ΣN_竞争对手(t-1) 所有竞争对手的累计用户之和(滞后)
        p_t_arr: p(t) 数组
        q_t_arr: q(t) 数组
        lambda_comp: λ 竞争系数
        m: 市场潜力
    """
    # 剩余市场 = m - N_i(t-1) - λ × ΣN_竞争对手(t-1)
    remaining = np.maximum(m - N_lag - lambda_comp * competitor_sum_lag, 0)
    
    # Bass扩散项: p(t) + q(t) × N_i(t-1)/m
    diffusion_rate = p_t_arr + q_t_arr * (N_lag / m)
    
    return diffusion_rate * remaining

def compute_prediction_competition(df, params, price_array, p_event_col, q_event_col, p_model, q_form):
    """
    计算竞争Bass模型的预测值
    
    params layout:
      if p_model in ['additive','nonlinear_event']:
         params = [p0, alpha, beta, q0, beta_q, lambda, m]
      else:
         params = [p0, alpha, beta, gamma, q0, beta_q, lambda, m]
    """
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        q0, beta_q, lambda_comp, m = params[p_param_count:p_param_count+4]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q, lambda_comp, m = params[p_param_count:p_param_count+4]

    # 计算 p(t)
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    
    # 计算 q(t)
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
    # 获取滞后值
    N_lag = df["N_lag"].values
    competitor_sum_lag = df["competitor_sum_lag"].values
    
    # 竞争Bass增量
    dN = dN_pred_competition(N_lag, competitor_sum_lag, p_t, q_t, lambda_comp, m)
    
    return dN, p_t, q_t

def residuals_competition(params, df, price_array, p_event_col, q_event_col, p_model, q_form):
    """残差函数用于least_squares优化"""
    # 参数合理性检查
    if p_model in ["additive", "nonlinear_event"]:
        q0 = params[3]
        lambda_comp = params[5]
        m = params[6]
    else:
        q0 = params[4]
        lambda_comp = params[6]
        m = params[7]

    if m <= df[CUM_COL].max() or q0 < 0 or lambda_comp < 0:
        return np.ones(len(df)) * 1e6

    dN_predicted, _, _ = compute_prediction_competition(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
    
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
        
    return df[NEW_COL].values - dN_predicted

def fit_bass_competition(df, price_array, p_event_col, q_event_col, p_model, q_form):
    """
    拟合竞争Bass模型
    """
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        
        if p_model in ["additive", "nonlinear_event"]:
            # params = [p0, alpha, beta, q0, beta_q, lambda, m]
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
            bounds = ([0, -10, -10, 0, -10, 0, 0.9*m_guess],
                      [1, 10, 10, 1, 10, 1, 20*m_guess])
        else:
            # params = [p0, alpha, beta, gamma, q0, beta_q, lambda, m]
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
            bounds = ([0, -10, -10, -10, 0, -10, 0, 0.9*m_guess],
                      [1, 10, 10, 10, 1, 10, 1, 20*m_guess])

        res = least_squares(residuals_competition, init, bounds=bounds,
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form), 
                            method="trf")
        
        if not res.success:
            return None

        params = res.x
        
        # 计算数值Jacobian用于标准误、t值、p值
        eps = 1e-6
        n = len(df)
        k = len(params)
        y_pred, _, _ = compute_prediction_competition(df, params, price_array, p_event_col, q_event_col, p_model, q_form)

        J = []
        for i in range(k):
            p_eps = params.copy()
            p_eps[i] += eps
            y_eps, _, _ = compute_prediction_competition(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T

        try:
            cond = np.linalg.cond(J.T @ J)
        except np.linalg.LinAlgError:
            cond = np.nan

        resid_vec = df[NEW_COL].values - y_pred
        sigma2 = np.sum(resid_vec**2) / (n - k)
        
        try:
            cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
            se = np.sqrt(np.diag(cov))
        except np.linalg.LinAlgError:
            se = np.full(k, np.nan)

        tvals = params / se
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))

        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        return res
        
    except Exception as e:
        return None

# ============= 数据加载与对齐 =============
def load_and_align_data():
    """
    加载主链和竞争对手数据，通过date对齐
    """
    print("\n========== 开始加载和对齐数据 ==========")
    
    # 1. 加载主链数据 (BTC/ETH)
    try:
        df_main = pd.read_csv(BTC_MAIN_PATH, parse_dates=[DATE_COL])
        df_main = df_main.sort_values(DATE_COL).reset_index(drop=True)
        print(f"✓ 主链数据加载成功: {len(df_main)} 行")
    except Exception as e:
        print(f"✗ 无法读取主链CSV: {e}")
        sys.exit(1)
    
    # 2. 加载所有竞争对手数据
    competitor_dfs = {}
    for name, filepath in COMPETITOR_FILES.items():
        try:
            df_comp = pd.read_csv(filepath, parse_dates=[DATE_COL])
            df_comp = df_comp.sort_values(DATE_COL).reset_index(drop=True)
            
            # 重命名列以便识别
            new_col, cum_col = COLUMN_MAPPING[name]
            
            # 只保留date和累计用户列
            df_comp = df_comp[[DATE_COL, cum_col]].rename(columns={cum_col: f"{name}_cum"})
            competitor_dfs[name] = df_comp
            print(f"✓ {name.upper()} 数据加载成功: {len(df_comp)} 行")
            
        except Exception as e:
            print(f"✗ 无法读取 {name} 数据: {e}")
            competitor_dfs[name] = None
    
    # 3. 通过date逐步合并所有数据
    df_merged = df_main.copy()
    
    for name, df_comp in competitor_dfs.items():
        if df_comp is not None:
            df_merged = pd.merge(df_merged, df_comp, on=DATE_COL, how="left")
            print(f"✓ 合并 {name.upper()} 数据")
    
    # 4. 填充缺失值（forward fill后再用0填充）
    competitor_cols = [f"{name}_cum" for name in competitor_dfs.keys() if competitor_dfs[name] is not None]
    df_merged[competitor_cols] = df_merged[competitor_cols].fillna(method="ffill").fillna(0)
    
    # 5. 计算竞争对手累计用户之和
    df_merged["competitor_sum"] = df_merged[competitor_cols].sum(axis=1)
    
    # 6. 添加滞后项 (t-1)
    df_merged["N_lag"] = df_merged[CUM_COL].shift(1).fillna(df_merged[CUM_COL].iloc[0])
    df_merged["competitor_sum_lag"] = df_merged["competitor_sum"].shift(1).fillna(0)
    
    print(f"\n✓ 数据对齐完成: {len(df_merged)} 行")
    print(f"✓ 竞争对手列: {competitor_cols}")
    print(f"✓ 已添加 N_lag 和 competitor_sum_lag 列")
    
    return df_merged

# ============= 主程序 =============
def main():
    # 加载并对齐数据
    df_full = load_and_align_data()
    
    # 筛选日期窗口
    df_full = df_full[(df_full[DATE_COL] >= pd.to_datetime(START_DATE)) & 
                      (df_full[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
    if df_full.empty:
        print("⚠️ 日期筛选后数据为空！")
        sys.exit(1)
    
    print(f"\n✓ 时间窗口: {START_DATE} 至 {END_DATE}, {len(df_full)} 行数据")
    
    results = []
    combos_done = 0
    combos_skipped = 0

    # 遍历所有P×Q组合
    for p_event_col in P_EVENT_LIST:
        for q_event_col in Q_EVENT_LIST:
            
            # 检查必需列是否存在
            required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
                           "N_lag", "competitor_sum_lag"] + PRICE_LAG_COLS
            missing = [c for c in required_cols if c not in df_full.columns]
            
            if missing:
                print(f"⚠️ 跳过组合 (缺列): P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue

            # 准备数据
            df = df_full[required_cols].copy()
            df = df.fillna(method="ffill").fillna(0)
            
            # 遍历价格列和变换
            for price_col in PRICE_LAG_COLS:
                raw_price = df[price_col].values.astype(float)

                try:
                    price_transforms = {
                        "linear": normalize(raw_price),
                        "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
                        "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
                    }
                except Exception:
                    print(f"⚠️ price transform error for {price_col}")
                    continue

                for pt_name, price_arr in price_transforms.items():
                    # 遍历p_model和q_form
                    for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
                        for q_form in ["linear", "log", "exp"]:
                            
                            model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
                            print(f"\n→ 拟合: {model_tag}")

                            res = fit_bass_competition(df, price_arr, p_event_col, q_event_col, p_model, q_form)
                            
                            if res is None:
                                print("  ✖ 拟合失败或不收敛")
                                combos_skipped += 1
                                continue

                            combos_done += 1
                            params = res.x
                            
                            # 计算预测值和误差
                            dN_pred, p_t, q_t = compute_prediction_competition(df, params, price_arr, p_event_col, q_event_col, p_model, q_form)
                            rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                            sse = np.sum((df[NEW_COL].values - dN_pred)**2)

                            # 参数名称
                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q", "lambda", "m"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", "lambda", "m"]

                            row = {
                                "P_event": p_event_col,
                                "Q_event": q_event_col,
                                "price_col": price_col,
                                "price_tf": pt_name,
                                "p_model": p_model,
                                "q_form": q_form,
                                "RMSE": rmse,
                                "SSE": sse,
                                "cond": float(getattr(res, "cond", np.nan))
                            }

                            # 保存参数及其统计量
                            for i, name in enumerate(param_names):
                                row[name] = float(params[i]) if i < len(params) else np.nan
                                row["se_"+name] = float(res.se[i]) if hasattr(res, "se") and i < len(res.se) else np.nan
                                row["t_"+name] = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
                                row["p_"+name] = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan

                            results.append(row)
                            print(f"  ✓ RMSE={rmse:.4f}, lambda={params[-2]:.4f}, m={params[-1]:.2f}")

    # 保存结果
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n{'='*60}")
    print(f"✅ 完成！组合成功 {combos_done} 次，跳过 {combos_skipped} 次")
    print(f"✅ 结果已保存至: {OUTPUT_CSV}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()