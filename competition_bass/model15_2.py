# 在model12_1基础上用真实的迁出数据,用于累积市场N修改，不改变m
# Δ𝑁(𝑡)=[𝑝(𝑡)+𝑞(𝑡)  (𝑋_𝑡𝑟𝑢𝑒 (𝑡−1))/𝑚]⋅[𝑚−𝑋_𝑡𝑟𝑢𝑒 (𝑡−1)]
# 𝑋_𝑡𝑟𝑢𝑒 (𝑡−1)=𝑋_𝑜𝑏𝑠 (𝑡−1)−∑(𝑠=1)^(𝑡−1)▒𝑀^𝑜𝑢𝑡  (𝑠)

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
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv"  # 🔥 新增
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"
# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"
START_DATE = "2020-10-01"
END_DATE = "2021-10-01"
OUTPUT_CSV = "btc_bass_pqfit_results_competition_with_cum_outflow20202021.csv"  # 🔥 修改文件名

# ===================================
# ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
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

# ============= 价格滞后变量 =============
PRICE_LAG_COLS = [
    "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
]

# ----------------- 工具函数 -----------------
def normalize(x):
    x = np.array(x, dtype=float)
    mean = np.mean(x)
    std = np.std(x)
    if std <= 0:
        return x - mean
    return (x - mean) / (std + 1e-12)

# --------- 🔥 新增：加载并对齐迁出数据 ---------
def load_and_align_outflow_data(migration_path, main_df):
    """
    加载迁出数据并对齐到主数据框的日期
    
    Args:
        migration_path: 迁移数据CSV路径
        main_df: 主数据框（包含date列）
    
    Returns:
        total_out_aligned: 对齐后的总迁出数组
    """
    try:
        df_mig = pd.read_csv(migration_path)
        # 解析日期
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}")
        return None
    
    print(f"\n{'='*80}")
    print(f"📊 加载迁出数据")
    print(f"{'='*80}")
    print(f"迁移数据文件: {migration_path}")
    print(f"迁移数据列名: {df_mig.columns.tolist()}")
    print(f"迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
    print(f"迁移数据行数: {len(df_mig)}")
    
    # 检查是否有total_out列
    if 'total_out' not in df_mig.columns:
        print("⚠️ 迁移数据缺少 'total_out' 列")
        return None
    
    # 对齐到main_df的日期（左连接，缺失值填0）
    main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    
    # 创建完整日期范围的DataFrame
    df_full = pd.DataFrame({'date': main_dates})
    
    # 合并
    df_merged = df_full.merge(df_mig[['date', 'total_out']], on='date', how='left')
    
    # 缺失日期填充为0
    total_out_aligned = df_merged['total_out'].fillna(0).values
    
    # 统计
    total_out_sum = total_out_aligned.sum()
    non_zero_days = (total_out_aligned > 0).sum()
    
    print(f"\n📈 迁出数据统计（对齐后）:")
    print(f"  总迁出人数: {total_out_sum:.0f}")
    print(f"  非零天数:   {non_zero_days}")
    print(f"  平均每天:   {total_out_sum/len(total_out_aligned):.2f}")
    if non_zero_days > 0:
        print(f"  非零日均值: {total_out_aligned[total_out_aligned > 0].mean():.2f}")
        print(f"  最大单日:   {total_out_aligned.max():.0f}")
    print(f"{'='*80}\n")
    
    return total_out_aligned

# --------- q(t) 计算 ----------
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

# --------- p(t) 计算 ----------
def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    """计算p(t)"""
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

# --------- Bass 增量（使用真实存量 N_lag_true） ----------
def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m):
    """
    Bass模型增量预测
    
    现在 N_lag 是 X_true(t-1)，即扣除迁出后的真实存量
    """
    remaining = np.maximum(m - N_lag, 0)
    return (p_t_arr + q_t_arr * (N_lag / m)) * remaining

# --------- compute_prediction ----------
def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form):
    """计算预测值"""
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        q0, beta_q, m = params[p_param_count:p_param_count+3]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q, m = params[p_param_count:p_param_count+3]
    
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
    # 🔥 使用真实存量的滞后值
    N_lag = df["N_lag_true"].values
    
    dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m)
    
    return dN, p_t, q_t

# --------- residuals ----------
def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form):
    """计算残差"""
    if p_model in ["additive", "nonlinear_event"]:
        q0 = params[3]
        m = params[5]
    else:
        q0 = params[4]
        m = params[6]
    
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6
    
    dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
    
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    
    return df[NEW_COL].values - dN_predicted

# --------- fit ----------
def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form):
    """拟合Bass模型"""
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        
        if p_model in ["additive", "nonlinear_event"]:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, m_guess]
            bounds = ([0, -10, -10, 0, -10, 0.9*m_guess],
                      [1, 10, 10, 1, 10, 20*m_guess])
        else:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
            bounds = ([0, -10, -10, -10, 0, -10, 0.9*m_guess],
                      [1, 10, 10, 10, 1, 10, 20*m_guess])
        
        res = least_squares(residuals_pair, init, bounds=bounds,
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form), 
                            method="trf")
        
        if not res.success:
            return None
        
        params = res.x
        
        # 计算标准误、t值、p值
        eps = 1e-6
        n = len(df)
        k = len(params)
        
        y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
        
        J = []
        for i in range(k):
            p_eps = params.copy()
            p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form)
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
    # 读取主数据
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}")
        sys.exit(1)
    
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
    # 🔥 加载迁出数据（在循环外部，只加载一次）
    df_raw = df_raw[(df_raw[DATE_COL] >= pd.to_datetime(START_DATE)) & 
                    (df_raw[DATE_COL] <= pd.to_datetime(END_DATE))].copy()

    total_out_data = load_and_align_outflow_data(MIGRATION_PATH, df_raw)

    if total_out_data is None:
        print("⚠️ 无法加载迁出数据，程序退出")
        sys.exit(1)

    # 🔥 计算累积迁出（包含第t期）
    cumulative_out = np.cumsum(total_out_data)  # Σ_{s=1}^{t} M^out(s)

    # 🔥 添加到df_raw
    df_raw['total_out'] = total_out_data
    df_raw['cumulative_out'] = cumulative_out
    df_raw['X_true'] = df_raw[CUM_COL] - cumulative_out  # 正确公式
    df_raw['N_lag_true'] = df_raw['X_true'].shift(1).fillna(df_raw['X_true'].iloc[0])

    # 诊断信息
    print(f"\n📊 真实存量统计:")
    print(f"  观察累积用户（X_obs）: 最小={df_raw[CUM_COL].min():.0f}, 最大={df_raw[CUM_COL].max():.0f}")
    print(f"  真实累积用户（X_true）: 最小={df_raw['X_true'].min():.0f}, 最大={df_raw['X_true'].max():.0f}")
    print(f"  累积迁出:              最小={cumulative_out.min():.0f}, 最大={cumulative_out.max():.0f}")
    print(f"  占比（迁出/观察）:      {cumulative_out.max() / df_raw[CUM_COL].max() * 100:.2f}%\n")    
    
    results = []
    combos_done = 0
    combos_skipped = 0
    
    total_price_cols = [c for c in PRICE_LAG_COLS]
    total_p_events = [c for c in P_EVENT_LIST]
    total_q_events = [c for c in Q_EVENT_LIST]
    
    # 主循环
    for p_event_col in total_p_events:
        for q_event_col in total_q_events:
            # 检查列
            required_cols = [DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols
            missing = [c for c in required_cols if c not in df_raw.columns]
            if missing:
                print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue
            
            # 选择数据（已在前面筛选过日期窗口）
            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col, 
                         'X_true', 'N_lag_true'] + total_price_cols].copy()
            df = df.fillna(method="ffill").fillna(0)
            
            if df.empty:
                print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue
            
            # 价格变换
            for price_col in total_price_cols:
                raw_price = df[price_col].values.astype(float)
                
                try:
                    price_transforms = {
                        "linear": normalize(raw_price),
                        "log": normalize(np.log(np.maximum(raw_price, 1e-8))),
                        "exp": normalize(np.exp(np.clip(raw_price, -50, 50)))
                    }
                except Exception:
                    print(f"⚠️ price transform error for {price_col}, skipping.")
                    continue
                
                for pt_name, price_arr in price_transforms.items():
                    for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
                        for q_form in ["linear", "log", "exp"]:
                            model_tag = f"P={p_event_col} | Q={q_event_col} | price={price_col}({pt_name}) | p_model={p_model} | q_form={q_form}"
                            print(f"\n→ 拟合: {model_tag}")
                            
                            res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form)
                            
                            if res is None:
                                print(" ✖ 拟合失败或不收敛，跳过。")
                                combos_skipped += 1
                                continue
                            
                            combos_done += 1
                            params = res.x
                            
                            # 计算RMSE/SSE
                            dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form)
                            rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                            sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
                            # 参数名称
                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q", "m"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", "m"]
                            
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
    
    # 保存结果
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
    print(f"✅ 结果已保存：{OUTPUT_CSV}")

if __name__ == "__main__":
    main()


# grok 和上面claude运行的结果一样
# import warnings
# warnings.filterwarnings("ignore")
# import pandas as pd
# import numpy as np
# from scipy.optimize import least_squares
# from scipy.stats import t
# import math
# import sys

# # ============= 参数配置 =============
# MAIN_CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
# MIGRATION_CSV_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv"  # 迁出数据

# DATE_COL = "date"
# NEW_COL = "btc_new_developers"
# CUM_COL = "btc_cum_users"

# START_DATE = "2017-01-01"
# END_DATE = "2019-01-01"

# OUTPUT_CSV = "btc_bass_pqfit_results_with_true_cum_grok.csv"

# # ============= 显式 P/Q/Price 列 =============
# P_EVENT_LIST = [
#     "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
#     "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
#     # "btc_p_bip_event_lag1","btc_p_bip_event_sum_7","btc_p_bip_event_mean_7","btc_p_bip_event_vol_7"
# ]
# Q_EVENT_LIST = [
#     "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
#     "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
#     # "btc_q_bip_event_lag1","btc_q_bip_event_sum_7","btc_q_bip_event_mean_7"
# ]
# PRICE_LAG_COLS = [
#     "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
# ]

# # ----------------- 工具函数 -----------------
# def normalize(x):
#     x = np.array(x, dtype=float)
#     mean = np.mean(x)
#     std = np.std(x)
#     if std <= 0:
#         return x - mean
#     return (x - mean) / (std + 1e-12)

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
#     return np.maximum(p_t, 0)

# # --------- Bass 增量（使用 X_true(t-1)） ----------
# def dN_pred_from_Xtrue(X_true_lag, p_t_arr, q_t_arr, m):
#     remaining = np.maximum(m - X_true_lag, 0)
#     return (p_t_arr + q_t_arr * (X_true_lag / m)) * remaining

# # --------- compute_prediction ----------
# def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form):
#     if p_model in ["additive", "nonlinear_event"]:
#         p_param_count = 3
#         p_params = params[:p_param_count]
#         q0, beta_q, m = params[p_param_count:p_param_count+3]
#     else:
#         p_param_count = 4
#         p_params = params[:p_param_count]
#         q0, beta_q, m = params[p_param_count:p_param_count+3]
    
#     p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
#     q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    
#     # 使用 X_true_lag
#     X_true_lag = df["X_true_lag"].values
    
#     dN = dN_pred_from_Xtrue(X_true_lag, p_t, q_t, m)
#     return dN, p_t, q_t

# # --------- residuals ----------
# def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form):
#     if p_model in ["additive", "nonlinear_event"]:
#         q0 = params[3]
#         m = params[5]
#     else:
#         q0 = params[4]
#         m = params[6]
    
#     if m <= df[CUM_COL].max() or q0 < 0:
#         return np.ones(len(df)) * 1e6
    
#     dN_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
    
#     if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0):
#         return np.ones(len(df)) * 1e6
    
#     return df[NEW_COL].values - dN_pred

# # --------- fit + 统计量 ----------
# def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form):
#     try:
#         m_guess = 1.2 * df[CUM_COL].max()
#         if p_model in ["additive", "nonlinear_event"]:
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, 0, -10, 0.9*m_guess],
#                       [1, 10, 10, 1, 10, 20*m_guess])
#         else:
#             init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
#             bounds = ([0, -10, -10, -10, 0, -10, 0.9*m_guess],
#                       [1, 10, 10, 10, 1, 10, 20*m_guess])
        
#         res = least_squares(residuals_pair, init, bounds=bounds,
#                             args=(df, price_array, p_event_col, q_event_col, p_model, q_form),
#                             method="trf")
        
#         if not res.success:
#             return None
        
#         params = res.x
#         dN_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form)
        
#         rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
        
#         # 数值Jacobian计算SE/t/p
#         eps = 1e-6
#         n = len(df)
#         k = len(params)
#         J = []
#         for i in range(k):
#             p_eps = params.copy()
#             p_eps[i] += eps
#             dN_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form)
#             J.append((dN_eps - dN_pred) / eps)
#         J = np.array(J).T
        
#         resid_vec = df[NEW_COL].values - dN_pred
#         sigma2 = np.sum(resid_vec**2) / (n - k)
#         try:
#             cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
#             se = np.sqrt(np.diag(cov))
#         except:
#             se = np.full(k, np.nan)
        
#         tvals = params / se
#         pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))
        
#         return {
#             'params': params,
#             'rmse': rmse,
#             'se': se,
#             'tvals': tvals,
#             'pvals': pvals
#         }
#     except Exception as e:
#         print("Fit error:", e)
#         return None

# # ----------------- 主程序 -----------------
# def main():
#     # 读取主表
#     df_raw = pd.read_csv(MAIN_CSV_PATH, parse_dates=[DATE_COL])
#     df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
#     # 读取迁出数据
#     df_out = pd.read_csv(MIGRATION_CSV_PATH, parse_dates=['date'])
#     df_out = df_out.rename(columns={'date': DATE_COL})
#     df_out = df_out[[DATE_COL, 'total_out']]
    
#     # 合并 + 填0
#     df = pd.merge(df_raw, df_out, on=DATE_COL, how='left')
#     df['total_out'] = df['total_out'].fillna(0).astype(int)
    
#     # 时间窗口
#     df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
#     if df.empty:
#         print("数据窗口为空")
#         sys.exit(1)
    
#     # 计算累计迁出
#     df['cum_out'] = df['total_out'].cumsum()
    
#     # X_true(t-1) = X_obs(t-1) - Cum-Perm-Out(t-1)
#     df['X_obs_lag'] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0])
#     df['cum_out_lag'] = df['cum_out'].shift(1).fillna(0)
#     df['X_true_lag'] = df['X_obs_lag'] - df['cum_out_lag']
#     df['X_true_lag'] = df['X_true_lag'].clip(lower=0)  # 防止负值
    
#     results = []
#     combos_done = 0
    
#     for p_event_col in P_EVENT_LIST:
#         for q_event_col in Q_EVENT_LIST:
#             required = [p_event_col, q_event_col] + PRICE_LAG_COLS
#             if not all(col in df.columns for col in required):
#                 continue
            
#             for price_col in PRICE_LAG_COLS:
#                 raw_price = df[price_col].values.astype(float)
#                 price_transforms = {
#                     "linear": normalize(raw_price),
#                     "log": normalize(np.log1p(np.maximum(raw_price, 0))),
#                     "exp": normalize(np.exp(np.clip(raw_price, -10, 10)))
#                 }
#                 for pt_name, price_arr in price_transforms.items():
#                     for p_model in ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]:
#                         for q_form in ["linear", "log", "exp"]:
#                             print(f"Fitting: P={p_event_col} Q={q_event_col} price={price_col}({pt_name}) p_model={p_model} q_form={q_form}")
#                             res_dict = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form)
#                             if res_dict is None:
#                                 continue
                            
#                             combos_done += 1
#                             row = {
#                                 "P_event": p_event_col,
#                                 "Q_event": q_event_col,
#                                 "price_col": price_col,
#                                 "price_tf": pt_name,
#                                 "p_model": p_model,
#                                 "q_form": q_form,
#                                 "RMSE": res_dict['rmse'],
#                             }
#                             param_names = ["p0", "alpha", "beta", "q0", "beta_q", "m"] if p_model in ["additive", "nonlinear_event"] else ["p0", "alpha", "beta", "gamma", "q0", "beta_q", "m"]
#                             for name, val, se_val, t_val, p_val in zip(param_names, res_dict['params'], res_dict['se'], res_dict['tvals'], res_dict['pvals']):
#                                 row[name] = val
#                                 row[f"se_{name}"] = se_val
#                                 row[f"t_{name}"] = t_val
#                                 row[f"p_{name}"] = p_val
#                             results.append(row)
    
#     pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
#     print(f"\n✅ 完成！成功拟合 {combos_done} 个模型，结果保存至 {OUTPUT_CSV}")

# if __name__ == "__main__":
#     main()