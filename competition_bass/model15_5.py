# 迁入（直接减少+正面网络效应）+迁出（考虑累积市场减少）BTC
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import math
import sys

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
START_DATE = "2020-10-01"
END_DATE = "2021-10-01"
OUTPUT_CSV = "btc_bass_pqfit_results_inflow_outflow_stock20202021.csv"  # 🔥 方案1：剩余市场

# 竞争币种
COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "DOGE"]

# 迁移列名
INFLOW_COLS = {
    "BCH": "in_from_BCH",
    "BSV": "in_from_BSV", 
    "ETH": "in_from_ETH",
    "LTC": "in_from_LTC",
    "DOGE": "in_from_DOGE"
}
OUTFLOW_COLS = {
    "BCH": "out_to_BCH",
    "BSV": "out_to_BSV",
    "ETH": "out_to_ETH",
    "LTC": "out_to_LTC",
    "DOGE": "out_to_DOGE"
}

# P/Q事件列表
P_EVENT_LIST = [
    "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
    "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
    # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
]
Q_EVENT_LIST = [
    "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
    "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
    # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
]
PRICE_LAG_COLS = [
    "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
]

# ----------------- 工具函数 -----------------
def normalize(x):
    """标准化"""
    x = np.array(x, dtype=float)
    mean = np.mean(x)
    std = np.std(x)
    if std <= 0:
        return x - mean
    return (x - mean) / (std + 1e-12)

# --------- 加载迁移数据 ---------
def load_and_align_migration_data(migration_path, main_df):
    """加载迁入和迁出数据"""
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}")
        return None, None
    
    print(f"\n{'='*80}")
    print(f"📊 加载迁移数据（方案1：迁入+迁出剩余市场）")
    print(f"{'='*80}")
    
    main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    df_full = pd.DataFrame({'date': main_dates})
    df_merged = df_full.merge(df_mig, on='date', how='left')
    
    # 迁入
    inflow_dict = {}
    for coin in COMPETITORS:
        col = INFLOW_COLS.get(coin)
        if col and col in df_merged.columns:
            inflow_dict[coin] = df_merged[col].fillna(0).values
        else:
            inflow_dict[coin] = np.zeros(len(df_merged))
    
    # 迁出
    outflow_dict = {}
    for coin in COMPETITORS:
        col = OUTFLOW_COLS.get(coin)
        if col and col in df_merged.columns:
            outflow_dict[coin] = df_merged[col].fillna(0).values
        else:
            outflow_dict[coin] = np.zeros(len(df_merged))
    
    print(f"✅ 迁入数据加载完成")
    print(f"✅ 迁出数据加载完成")
    print(f"{'='*80}\n")
    
    return inflow_dict, outflow_dict

# --------- q(t)/p(t) 计算 ----------
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

# --------- 🔥 Bass增量（方案1：迁入+迁出剩余市场） ----------
def dN_pred_from_Nlag(N_lag_true, p_t_arr, q_t_arr, m, inflow_dict, gamma_params):
    """
    方案1：迁入 + 迁出（剩余市场）
    
    ΔN = [p + q·X_true/m + Σγ·M^in,norm] · (m - X_true) + Σ M^in
    
    其中：X_true = X_obs - Σ累积迁出
    """
    remaining = np.maximum(m - N_lag_true, 0)
    
    # Bass基础扩散率
    base_rate = p_t_arr + q_t_arr * (N_lag_true / m)
    
    # 迁入正网络效应（🔥 使用 t 的 M_in,norm）
    # positive_network = np.zeros_like(N_lag_true)
    # for i, coin in enumerate(COMPETITORS):
    #     if coin in inflow_dict:
    #         M_in = inflow_dict[coin]
    #         M_in_norm = normalize(M_in)
    #         positive_network += gamma_params[i] * M_in_norm
    
    # 迁入正网络效应（🔥 使用 t-1 的 M_in,norm）
    positive_network = np.zeros_like(N_lag_true)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            M_in = inflow_dict[coin]
            # 🔥 核心变化：先 lag 一期
            M_in_lag = np.concatenate([[0], M_in[:-1]])
            # 再做标准化
            M_in_norm_lag = normalize(M_in_lag)
            positive_network += gamma_params[i] * M_in_norm_lag
    
    # 总扩散率
    total_rate = base_rate + positive_network
    
    # Bass增长
    bass_growth = total_rate * remaining
    
    # 直接迁入
    direct_inflow = np.zeros_like(N_lag_true)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct_inflow += inflow_dict[coin]
    
    return bass_growth + direct_inflow

# --------- compute_prediction ----------
def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict):
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        q0, beta_q = params[3:5]
        gamma_params = params[5:10]  # 5个γ
        m = params[10]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q = params[4:6]
        gamma_params = params[6:11]  # 5个γ
        m = params[11]
    
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
    # 🔥 使用真实存量（扣除迁出）
    N_lag_true = df["N_lag_true"].values
    
    dN = dN_pred_from_Nlag(N_lag_true, p_t, q_t, m, inflow_dict, gamma_params)
    
    return dN, p_t, q_t

# --------- residuals ----------
def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict):
    if p_model in ["additive", "nonlinear_event"]:
        q0 = params[3]
        m = params[10]
    else:
        q0 = params[4]
        m = params[11]
    
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6
    
    dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict)
    
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    
    return df[NEW_COL].values - dN_predicted

# --------- fit ----------
def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict):
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        
        if p_model in ["additive", "nonlinear_event"]:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 
                    0.0001, 0.0001, 0.0001, 0.0001, 0.0001,  # gamma
                    m_guess]
            bounds = ([0, -10, -10, 0, -10, 
                      -0.01, -0.01, -0.01, -0.01, -0.01,
                      0.9*m_guess],
                      [1, 10, 10, 1, 10, 
                       0.01, 0.01, 0.01, 0.01, 0.01,
                       20*m_guess])
        else:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, 
                    0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 
                    m_guess]
            bounds = ([0, -10, -10, -10, 0, -10, 
                      -0.01, -0.01, -0.01, -0.01, -0.01,
                      0.9*m_guess],
                      [1, 10, 10, 10, 1, 10, 
                       0.01, 0.01, 0.01, 0.01, 0.01,
                       20*m_guess])
        
        res = least_squares(residuals_pair, init, bounds=bounds,
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict), 
                            method="trf")
        
        if not res.success:
            return None
        
        params = res.x
        
        # 计算标准误等
        eps = 1e-6
        n = len(df)
        k = len(params)
        
        y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict)
        
        J = []
        for i in range(k):
            p_eps = params.copy()
            p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict)
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
        
        tvals = params / (se + 1e-12)
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))
        
        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        
        return res
    
    except Exception as e:
        print(f"  拟合异常: {e}")
        return None

# ----------------- 主程序 -----------------
def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}")
        sys.exit(1)
    
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    df_raw = df_raw[(df_raw[DATE_COL] >= pd.to_datetime(START_DATE)) & 
                    (df_raw[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
    # 加载迁移数据
    inflow_dict_global, outflow_dict_global = load_and_align_migration_data(MIGRATION_PATH, df_raw)
    
    if inflow_dict_global is None or outflow_dict_global is None:
        print("⚠️ 无法加载迁移数据，程序退出")
        sys.exit(1)
    
    # 🔥 计算累积迁出
    total_out = np.zeros(len(df_raw))
    for coin in COMPETITORS:
        total_out += outflow_dict_global[coin]
    
    cumulative_out = np.cumsum(total_out)
    cumulative_out_lag = np.concatenate([[0], cumulative_out[:-1]])
    
    # 🔥 计算真实存量 X_true = X_obs - Σ累积迁出
    df_raw['X_true'] = df_raw[CUM_COL] - cumulative_out_lag
    df_raw['N_lag_true'] = df_raw['X_true'].shift(1).fillna(df_raw['X_true'].iloc[0])
    
    print(f"📊 真实存量统计:")
    print(f"  观察累积（X_obs）: {df_raw[CUM_COL].iloc[-1]:,.0f}")
    print(f"  真实累积（X_true）: {df_raw['X_true'].iloc[-1]:,.0f}")
    print(f"  累积迁出:          {cumulative_out_lag.max():,.0f}\n")
    
    results = []
    combos_done = 0
    combos_skipped = 0
    
    # 主循环
    for p_event_col in P_EVENT_LIST:
        for q_event_col in Q_EVENT_LIST:
            required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + PRICE_LAG_COLS
            missing = [c for c in required_cols if c not in df_raw.columns]
            if missing:
                combos_skipped += 1
                continue
            
            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
                         'N_lag_true'] + PRICE_LAG_COLS].copy()
            df = df.fillna(method="ffill").fillna(0)
            
            if df.empty:
                combos_skipped += 1
                continue
            
            # 对齐迁入数据
            inflow_dict = {}
            for coin in COMPETITORS:
                inflow_dict[coin] = inflow_dict_global[coin][:len(df)]
            
            for price_col in PRICE_LAG_COLS:
                raw_price = df[price_col].values.astype(float)
                
                try:
                    price_transforms = {
                        "linear": normalize(raw_price),
                        "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
                        "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
                    }
                except Exception:
                    continue
                
                for pt_name, price_arr in price_transforms.items():
                    for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
                        for q_form in ["linear", "log", "exp"]:
                            print(f"\n→ 拟合: P={p_event_col} | Q={q_event_col} | {price_col}({pt_name}) | {p_model} | {q_form}")
                            
                            res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict)
                            
                            if res is None:
                                combos_skipped += 1
                                continue
                            
                            combos_done += 1
                            params = res.x
                            
                            dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict)
                            rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                            sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
                                             "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_DOGE", "m"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma_price", "q0", "beta_q", 
                                             "gamma_BCH", "gamma_BSV", "gamma_ETH", "gamma_LTC", "gamma_DOGE", "m"]
                            
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
                            
                            for i, name in enumerate(param_names):
                                row[name] = float(params[i]) if i < len(params) else np.nan
                                row["se_"+name] = float(res.se[i]) if hasattr(res, "se") and i < len(res.se) else np.nan
                                row["t_"+name] = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
                                row["p_"+name] = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan
                            
                            results.append(row)
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n{'='*80}")
    print(f"✅ 方案1完成：迁入+迁出（剩余市场）")
    print(f"成功: {combos_done}, 跳过: {combos_skipped}")
    print(f"结果: {OUTPUT_CSV}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

# ========================================
# ETH
# 迁入（直接减少+正面网络效应）+迁出（考虑累积市场减少）
# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============= 参数配置 =============
# CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"  # 🔥 ETH数据
# MIGRATION_PATH = "/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv"  # 🔥 ETH迁移
# DATE_COL = "date"
# NEW_COL = "eth_new_developers"  # 🔥 ETH
# CUM_COL = "eth_cum_users"  # 🔥 ETH
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
# OUTPUT_CSV = "eth_bass_pqfit_results_inflow_outflow_stock.csv"  # 🔥 ETH输出

# # 🔥 竞争币种（ETH的12个竞争对手）
# COMPETITORS = ["BTC", "SOLANA", "BNB", "OPTIMISM", "APTOS", "SUI", "NEAR", "ZKSYNC", "ARBITRUM", "HARMONY", "ETC", "ETHPOW"]

# # 🔥 迁移列名（ETH版本）
# INFLOW_COLS = {
#     "BTC": "in_from_BTC",
#     "SOLANA": "in_from_SOLANA",
#     "BNB": "in_from_BNB",
#     "OPTIMISM": "in_from_OPTIMISM",
#     "APTOS": "in_from_APTOS",
#     "SUI": "in_from_SUI",
#     "NEAR": "in_from_NEAR",
#     "ZKSYNC": "in_from_ZKSYNC",
#     "ARBITRUM": "in_from_ARBITRUM",
#     "HARMONY": "in_from_HARMONY",
#     "ETC": "in_from_ETC",
#     "ETHPOW": "in_from_ETHPOW"
# }
# OUTFLOW_COLS = {
#     "BTC": "out_to_BTC",
#     "SOLANA": "out_to_SOLANA",
#     "BNB": "out_to_BNB",
#     "OPTIMISM": "out_to_OPTIMISM",
#     "APTOS": "out_to_APTOS",
#     "SUI": "out_to_SUI",
#     "NEAR": "out_to_NEAR",
#     "ZKSYNC": "out_to_ZKSYNC",
#     "ARBITRUM": "out_to_ARBITRUM",
#     "HARMONY": "out_to_HARMONY",
#     "ETC": "out_to_ETC",
#     "ETHPOW": "out_to_ETHPOW"
# }

# # 🔥 P/Q事件列表（ETH版本）
# P_EVENT_LIST = [
#     "eth_p_event_lag1","eth_p_event_sum_7","eth_p_event_mean_7","eth_p_event_vol_7",
#     "eth_p_eip_p_event_lag1","eth_p_eip_p_event_sum_7","eth_p_eip_p_event_mean_7","eth_p_eip_p_event_vol_7",
#     # "eth_p_eip_event_lag1","eth_p_eip_event_sum_7","eth_p_eip_event_mean_7","eth_p_eip_event_vol_7"
# ]
# Q_EVENT_LIST = [
#     "eth_q_event_lag1","eth_q_event_sum_7","eth_q_event_mean_7",
#     "eth_q_eip_q_event_lag1","eth_q_eip_q_event_sum_7","eth_q_eip_q_event_mean_7",
#     # "eth_q_eip_event_lag1","eth_q_eip_event_sum_7","eth_q_eip_event_mean_7"
# ]

# # 🔥 价格滞后变量（ETH版本）
# PRICE_LAG_COLS = [
#     "eth_price_lag1","eth_ma_7d","eth_ma_14d","eth_ma_21d","eth_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     """标准化"""
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

# # --------- 加载迁移数据 ---------
# def load_and_align_migration_data(migration_path, main_df):
#     """加载迁入和迁出数据"""
#     try:
#         df_mig = pd.read_csv(migration_path)
#         df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
#     except Exception as e:
#         print(f"⚠️ 无法读取迁移数据: {e}")
#         return None, None
    
#     print(f"\n{'='*80}")
#     print(f"📊 加载迁移数据（方案1：迁入+迁出剩余市场）")
#     print(f"{'='*80}")
    
#     main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
#     df_full = pd.DataFrame({'date': main_dates})
#     df_merged = df_full.merge(df_mig, on='date', how='left')
    
#     # 迁入
#     inflow_dict = {}
#     for coin in COMPETITORS:
#         col = INFLOW_COLS.get(coin)
#         if col and col in df_merged.columns:
#             inflow_dict[coin] = df_merged[col].fillna(0).values
#             print(f"✅ 加载迁入: {coin} ({col})")
#         else:
#             inflow_dict[coin] = np.zeros(len(df_merged))
#             print(f"⚠️ 未找到迁入列: {coin} ({col})")
    
#     # 迁出
#     outflow_dict = {}
#     for coin in COMPETITORS:
#         col = OUTFLOW_COLS.get(coin)
#         if col and col in df_merged.columns:
#             outflow_dict[coin] = df_merged[col].fillna(0).values
#             print(f"✅ 加载迁出: {coin} ({col})")
#         else:
#             outflow_dict[coin] = np.zeros(len(df_merged))
#             print(f"⚠️ 未找到迁出列: {coin} ({col})")
    
#     print(f"\n✅ 迁入数据加载完成")
#     print(f"✅ 迁出数据加载完成")
#     print(f"{'='*80}\n")
    
#     return inflow_dict, outflow_dict

# # --------- q(t)/p(t) 计算 ----------
# def compute_q_t_from_array(event_arr, q_params, q_form):
#     q0, beta = q_params
#     ev = normalize(event_arr)
#     if q_form == "linear":
#         q_t = np.maximum(q0 + beta * ev, 0)
#     elif q_form == "log":
#         q_t = np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
#     elif q_form == "exp":
#         q_t = q0 * np.exp(beta * ev)
#     else:
#         raise ValueError("未知 q_form")
#     return q_t

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
#     else:
#         raise ValueError("未知 p_model")
#     return np.maximum(p_t, 0)

# # --------- 🔥 Bass增量（方案1：迁入+迁出剩余市场） ----------
# def dN_pred_from_Nlag(N_lag_true, p_t_arr, q_t_arr, m, inflow_dict, gamma_params):
#     """
#     方案1：迁入 + 迁出（剩余市场）
    
#     ΔN = [p + q·X_true/m + Σγ·M^in,norm(t-1)] · (m - X_true) + Σ M^in(t)
    
#     其中：X_true = X_obs - Σ累积迁出
#     """
#     remaining = np.maximum(m - N_lag_true, 0)
    
#     # Bass基础扩散率
#     base_rate = p_t_arr + q_t_arr * (N_lag_true / m)
    
#     # 🔥 迁入正网络效应（使用 t-1 的 M_in,norm）
#     positive_network = np.zeros_like(N_lag_true)
#     for i, coin in enumerate(COMPETITORS):
#         if coin in inflow_dict:
#             M_in = inflow_dict[coin]
#             # 🔥 核心变化：先 lag 一期
#             M_in_lag = np.concatenate([[0], M_in[:-1]])
#             # 再做标准化
#             M_in_norm_lag = normalize(M_in_lag)
#             positive_network += gamma_params[i] * M_in_norm_lag
    
#     # 总扩散率
#     total_rate = base_rate + positive_network
    
#     # Bass增长
#     bass_growth = total_rate * remaining
    
#     # 🔥 直接迁入（使用 t 的原始值）
#     direct_inflow = np.zeros_like(N_lag_true)
#     for coin in COMPETITORS:
#         if coin in inflow_dict:
#             direct_inflow += inflow_dict[coin]
    
#     return bass_growth + direct_inflow

# # --------- compute_prediction ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict):
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q = params[3:5]
#         gamma_params = params[5:17]  # 🔥 12个γ
#         m = params[17]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q = params[4:6]
#         gamma_params = params[6:18]  # 🔥 12个γ
#         m = params[18]
    
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
#     # 🔥 使用真实存量（扣除迁出）
#     N_lag_true = df["N_lag_true"].values
    
#     dN = dN_pred_from_Nlag(N_lag_true, p_t, q_t, m, inflow_dict, gamma_params)
    
#     return dN, p_t, q_t

# # --------- residuals ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict):
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[17]
#     else:
#         q0 = params[4]
#         m = params[18]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict)
    
#     if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_predicted

# # --------- fit ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict):
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
        
#         if p_model in ["additive", "nonlinear_event"]:
#             # 🔥 12个γ参数
#             init = [0.001, 0.01, 0.01, 0.01, 0.01] + [0.0001] * 12 + [m_guess]
#             bounds = ([0, -10, -10, 0, -10] + [-0.01] * 12 + [0.9*m_guess],
#                       [1, 10, 10, 1, 10] + [0.01] * 12 + [20*m_guess])
#         else:
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01] + [0.0001] * 12 + [m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10] + [-0.01] * 12 + [0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10] + [0.01] * 12 + [20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict), 
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
        
#         # 计算标准误等
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
        
#         y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict)
        
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict)
#             J.append((y_eps - y_pred) / eps)
#         J = np.array(J).T
        
#         try:
#             cond = np.linalg.cond(J.T @ J)
#         except np.linalg.LinAlgError:
#             cond = np.nan
        
#         resid_vec = df[NEW_COL].values - y_pred
#         sigma2 = np.sum(resid_vec**2) / (n - k)
        
#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se = np.sqrt(np.diag(cov))
#         except np.linalg.LinAlgError:
#             se = np.full(k, np.nan)
        
#         tvals = params / (se + 1e-12)
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))
        
#         res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        
#         return res
    
#     except Exception as e:
#         print(f"  拟合异常: {e}")
#         return None

# # ----------------- 主程序 -----------------
# def main():
#     try:
#         df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
#     except Exception as e:
#         print(f"无法读取 CSV: {e}")
#         sys.exit(1)
    
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
#     df_raw = df_raw[(df_raw[DATE_COL] >= pd.to_datetime(START_DATE)) & 
#                     (df_raw[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
#     # 加载迁移数据
#     inflow_dict_global, outflow_dict_global = load_and_align_migration_data(MIGRATION_PATH, df_raw)
    
#     if inflow_dict_global is None or outflow_dict_global is None:
#         print("⚠️ 无法加载迁移数据，程序退出")
#         sys.exit(1)
    
#     # 🔥 计算累积迁出
#     total_out = np.zeros(len(df_raw))
#     for coin in COMPETITORS:
#         total_out += outflow_dict_global[coin]
    
#     cumulative_out = np.cumsum(total_out)
#     cumulative_out_lag = np.concatenate([[0], cumulative_out[:-1]])
    
#     # 🔥 计算真实存量 X_true = X_obs - Σ累积迁出
#     df_raw['X_true'] = df_raw[CUM_COL] - cumulative_out_lag
#     df_raw['N_lag_true'] = df_raw['X_true'].shift(1).fillna(df_raw['X_true'].iloc[0])
    
#     print(f"📊 真实存量统计:")
#     print(f"  观察累积（X_obs）: {df_raw[CUM_COL].iloc[-1]:,.0f}")
#     print(f"  真实累积（X_true）: {df_raw['X_true'].iloc[-1]:,.0f}")
#     print(f"  累积迁出:          {cumulative_out_lag.max():,.0f}\n")
    
#     results = []
#     combos_done = 0
#     combos_skipped = 0
    
#     # 主循环
#     for p_event_col in P_EVENT_LIST:
#         for q_event_col in Q_EVENT_LIST:
#             required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + PRICE_LAG_COLS
#             missing = [c for c in required_cols if c not in df_raw.columns]
#             if missing:
#                 combos_skipped += 1
#                 continue
            
#             df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
#                          'N_lag_true'] + PRICE_LAG_COLS].copy()
#             df = df.fillna(method="ffill").fillna(0)
            
#             if df.empty:
#                 combos_skipped += 1
#                 continue
            
#             # 对齐迁入数据
#             inflow_dict = {}
#             for coin in COMPETITORS:
#                 inflow_dict[coin] = inflow_dict_global[coin][:len(df)]
            
#             for price_col in PRICE_LAG_COLS:
#                 raw_price = df[price_col].values.astype(float)
                
#                 try:
#                     price_transforms = {
#                         "linear": normalize(raw_price),
#                         "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
#                         "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
#                     }
#                 except Exception:
#                     continue
                
#                 for pt_name, price_arr in price_transforms.items():
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             print(f"\n→ 拟合: P={p_event_col} | Q={q_event_col} | {price_col}({pt_name}) | {p_model} | {q_form}")
                            
#                             res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict)
                            
#                             if res is None:
#                                 combos_skipped += 1
#                                 continue
                            
#                             combos_done += 1
#                             params = res.x
                            
#                             dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict)
#                             rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
#                             sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
#                             # 🔥 参数名称（12个γ）
#                             if p_model in ["additive", "nonlinear_event"]:
#                                 param_names = ["p0", "alpha", "beta", "q0", "beta_q"] + \
#                                     [f"gamma_{coin}" for coin in COMPETITORS] + ["m"]
#                             else:
#                                 param_names = ["p0", "alpha", "beta", "gamma_price", "q0", "beta_q"] + \
#                                     [f"gamma_{coin}" for coin in COMPETITORS] + ["m"]
                            
#                             row = {
#                                 "P_event": p_event_col,
#                                 "Q_event": q_event_col,
#                                 "price_col": price_col,
#                                 "price_tf": pt_name,
#                                 "p_model": p_model,
#                                 "q_form": q_form,
#                                 "RMSE": rmse,
#                                 "SSE": sse,
#                                 "cond": float(getattr(res, "cond", np.nan))
#                             }
                            
#                             for i, name in enumerate(param_names):
#                                 row[name] = float(params[i]) if i < len(params) else np.nan
#                                 row["se_"+name] = float(res.se[i]) if hasattr(res, "se") and i < len(res.se) else np.nan
#                                 row["t_"+name] = float(res.tvals[i]) if hasattr(res, "tvals") and i < len(res.tvals) else np.nan
#                                 row["p_"+name] = float(res.pvals[i]) if hasattr(res, "pvals") and i < len(res.pvals) else np.nan
                            
#                             results.append(row)
    
#     df_results = pd.DataFrame(results)
#     df_results.to_csv(OUTPUT_CSV, index=False)
    
#     print(f"\n{'='*80}")
#     print(f"✅ 方案1完成：迁入+迁出（剩余市场）- ETH版本")
#     print(f"成功: {combos_done}, 跳过: {combos_skipped}")
#     print(f"结果: {OUTPUT_CSV}")
#     print(f"{'='*80}\n")

# if __name__ == "__main__":
#     main()