# 独立项+网络效应扩散速度 但网络效应中Mj(t)用净流量，且标准化,独立项用Mj(t)且不标准化 btc
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
START_DATE = "2017-01-01"
END_DATE = "2019-01-01"
OUTPUT_CSV = "btc_bass_pqfit_results_competition_netflow_standardized20172019.csv"  # 🔥 修改文件名（净流量版本）

# 竞争币种列表
COMPETITORS = ["BCH", "BSV", "ETH", "LTC", "Dogecoin"]

# ===================================
# ============= P_EVENT_LIST 与 Q_EVENT_LIST =============
P_EVENT_LIST = [
    "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_mean_7","btc_p_event_vol_7",
    "btc_p_bip_p_event_lag1","btc_p_bip_p_event_sum_7","btc_p_bip_p_event_mean_7","btc_p_bip_p_event_vol_7",
]
Q_EVENT_LIST = [
    "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_mean_7",
    "btc_q_bip_q_event_lag1","btc_q_bip_q_event_sum_7","btc_q_bip_q_event_mean_7",
]

# ============= 价格滞后变量 =============
PRICE_LAG_COLS = [
    "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
]

# ----------------- 工具函数 -----------------
def normalize(x):
    """标准化函数：均值0，标准差1"""
    x = np.array(x, dtype=float)
    mean = np.mean(x)
    std = np.std(x)
    if std <= 0:
        return x - mean
    return (x - mean) / (std + 1e-12)

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

# --------- 🔥 Bass 增量（净流量版本） ----------
def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m, inflow_dict, outflow_dict, gamma_params):
    """
    净流量版本：
    
    ΔN(t) = [p(t) + q(t)·X(t-1)/m + Σγ_j·NetFlow_j^norm(t)] · (m-X(t-1)) + Σ M_j^in(t)
    
    关键修改：
    - 网络效应项使用标准化的 净流量 NetFlow_j = M_j^in - M_j^out
    - 直接迁入项使用原始的 M_j^in(t)
    
    Args:
        N_lag: N(t-1) 数组
        p_t_arr: p(t) 数组
        q_t_arr: q(t) 数组
        m: 市场容量
        inflow_dict: {coin: inflow_array} 字典（迁入原始值）
        outflow_dict: {coin: outflow_array} 字典（迁出原始值）
        gamma_params: [γ_BCH, γ_BSV, γ_ETH, γ_LTC, γ_Dogecoin]（净流量系数）
    """
    remaining = np.maximum(m - N_lag, 0)
    
    # Bass内生扩散率
    base_rate = p_t_arr + q_t_arr * (N_lag / m)
    
    # 🔥 关键修改：净流量网络效应（使用标准化的净流量）
    netflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict and coin in outflow_dict:
            # 计算净流量
            M_in = inflow_dict[coin]
            M_out = outflow_dict[coin]
            NetFlow = M_in - M_out  # 🔥 净流量 = 迁入 - 迁出
            
            # 标准化净流量
            NetFlow_norm = normalize(NetFlow)
            
            netflow_network_rate += gamma_params[i] * NetFlow_norm
    
    # 总扩散率（受市场容量约束）
    total_rate = base_rate + netflow_network_rate
    constrained_growth = total_rate * remaining
    
    # 🔥 直接迁入（使用原始值，不标准化）
    direct_migration = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct_migration += inflow_dict[coin]  # 只用迁入
    
    # 总增长
    return constrained_growth + direct_migration

# --------- compute_prediction ----------
def compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
    """计算预测值"""
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        q0, beta_q = params[3:5]
        gamma_params = params[5:10]
        m = params[10]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q = params[4:6]
        gamma_params = params[6:11]
        m = params[11]
    
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    N_lag = df["N_lag"].values
    
    # 🔥 传入迁入和迁出字典
    dN = dN_pred_from_Nlag(N_lag, p_t, q_t, m, inflow_dict, outflow_dict, gamma_params)
    
    return dN, p_t, q_t

# --------- residuals ----------
def residuals_pair(params, df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
    """计算残差"""
    if p_model in ["additive", "nonlinear_event"]:
        q0 = params[3]
        m = params[10]
    else:
        q0 = params[4]
        m = params[11]
    
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6
    
    dN_predicted, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
    
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    
    return df[NEW_COL].values - dN_predicted

# --------- fit ----------
def fit_bass_pair(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict):
    """拟合Bass模型"""
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        
        if p_model in ["additive", "nonlinear_event"]:
            init = [0.001, 0.01, 0.01, 0.01, 0.01, 
                    0.0001, 0.0001, 0.0001, 0.0001, 0.0001,
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
                            args=(df, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict), 
                            method="trf")
        
        if not res.success:
            return None
        
        params = res.x
        
        # 计算标准误、t值、p值
        eps = 1e-6
        n = len(df)
        k = len(params)
        
        y_pred, _, _ = compute_prediction_pair(df, params, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
        
        J = []
        for i in range(k):
            p_eps = params.copy()
            p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(df, p_eps, price_array, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
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

# --------- 🔥 加载迁移数据（迁入和迁出） ----------
def load_migration_data(migration_path, main_df):
    """
    读取迁移数据并对齐到主数据框的日期
    返回: (inflow_dict, outflow_dict) 元组
    """
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}")
        return None, None
    
    print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
    print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")
    print(f"📊 迁移数据行数: {len(df_mig)}")
    
    if 'date' not in df_mig.columns:
        print("⚠️ 迁移数据缺少 'date' 列")
        return None, None
    
    # 创建完整日期范围
    date_range = pd.date_range(start=main_df[DATE_COL].min(), 
                               end=main_df[DATE_COL].max(), 
                               freq='D')
    df_full = pd.DataFrame({DATE_COL: date_range})
    
    # 合并
    df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')
    
    # 🔥 列名映射（迁入和迁出）
    inflow_col_mapping = {
        "BCH": "in_from_BCH",
        "BSV": "in_from_BSV",
        "ETH": "in_from_ETH",
        "LTC": "in_from_LTC",
        "Dogecoin": "in_from_DOGE"
    }
    
    outflow_col_mapping = {
        "BCH": "out_to_BCH",
        "BSV": "out_to_BSV",
        "ETH": "out_to_ETH",
        "LTC": "out_to_LTC",
        "Dogecoin": "out_to_DOGE"
    }
    
    # 构建迁入字典
    inflow_dict = {}
    for coin in COMPETITORS:
        actual_col = inflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            inflow_dict[coin] = df_merged[actual_col].fillna(0).values
            print(f"✅ 成功加载 {coin} 的迁入数据列: {actual_col}")
        else:
            print(f"⚠️ 未找到 {coin} 对应的迁入列: {actual_col}")
            inflow_dict[coin] = np.zeros(len(df_merged))
    
    # 🔥 构建迁出字典
    outflow_dict = {}
    for coin in COMPETITORS:
        actual_col = outflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            outflow_dict[coin] = df_merged[actual_col].fillna(0).values
            print(f"✅ 成功加载 {coin} 的迁出数据列: {actual_col}")
        else:
            print(f"⚠️ 未找到 {coin} 对应的迁出列: {actual_col}")
            outflow_dict[coin] = np.zeros(len(df_merged))
    
    # 对齐到main_df
    df_merged_indexed = df_merged.set_index(DATE_COL)
    main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    
    inflow_dict_aligned = {}
    outflow_dict_aligned = {}
    
    for coin in COMPETITORS:
        # 迁入
        actual_col = inflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
            inflow_dict_aligned[coin] = aligned
        else:
            inflow_dict_aligned[coin] = np.zeros(len(main_df))
        
        # 迁出
        actual_col = outflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            aligned = df_merged_indexed.reindex(main_dates)[actual_col].fillna(0).values
            outflow_dict_aligned[coin] = aligned
        else:
            outflow_dict_aligned[coin] = np.zeros(len(main_df))
    
    # 打印统计
    print("\n📈 迁移数据统计（窗口期内）:")
    print("🔥 方法：网络效应项使用标准化净流量，直接迁入项使用原始迁入")
    for coin in COMPETITORS:
        M_in = inflow_dict_aligned[coin]
        M_out = outflow_dict_aligned[coin]
        NetFlow = M_in - M_out
        
        total_in = np.sum(M_in)
        total_out = np.sum(M_out)
        net_total = np.sum(NetFlow)
        
        non_zero_days_in = np.sum(M_in > 0)
        non_zero_days_out = np.sum(M_out > 0)
        
        if non_zero_days_in > 0 or non_zero_days_out > 0:
            print(f"  {coin:10s}:")
            print(f"    迁入: 总数={total_in:6.0f}, 非零天数={non_zero_days_in:4d}")
            print(f"    迁出: 总数={total_out:6.0f}, 非零天数={non_zero_days_out:4d}")
            print(f"    净流量: {net_total:6.0f} ({'流入' if net_total > 0 else '流出'})")
        else:
            print(f"  {coin:10s}: 无数据")
    
    return inflow_dict_aligned, outflow_dict_aligned

# ----------------- 主程序 -----------------
def main():
    # 读取主数据
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}")
        sys.exit(1)
    
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    
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
                print(f"⚠️ 跳过组合 (缺列)：P={p_event_col}, Q={q_event_col}, 缺失列示例: {missing[:5]}")
                combos_skipped += 1
                continue
            
            # 选择日期窗口
            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col] + total_price_cols].copy()
            df = df.fillna(method="ffill").fillna(0)
            df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) & (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            
            if df.empty:
                print(f"⚠️ 空窗口，跳过 P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1
                continue
            
            # N_lag
            df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values
            
            # 🔥 加载迁移数据（迁入和迁出）
            inflow_dict, outflow_dict = load_migration_data(MIGRATION_PATH, df)
            if inflow_dict is None or outflow_dict is None:
                print(f"⚠️ 无法加载迁移数据，跳过 P={p_event_col}, Q={q_event_col}")
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
                            
                            res = fit_bass_pair(df, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
                            
                            if res is None:
                                print(" ✖ 拟合失败或不收敛，跳过。")
                                combos_skipped += 1
                                continue
                            
                            combos_done += 1
                            params = res.x
                            
                            # 计算RMSE/SSE
                            dN_pred, p_t, q_t = compute_prediction_pair(df, params, price_arr, p_event_col, q_event_col, p_model, q_form, inflow_dict, outflow_dict)
                            rmse = math.sqrt(np.mean((df[NEW_COL].values - dN_pred)**2))
                            sse = np.sum((df[NEW_COL].values - dN_pred)**2)
                            
                            # 🔥 修改参数名称（净流量版本）
                            if p_model in ["additive", "nonlinear_event"]:
                                param_names = ["p0", "alpha", "beta", "q0", "beta_q", 
                                             "gamma_netflow_BCH", "gamma_netflow_BSV", "gamma_netflow_ETH", 
                                             "gamma_netflow_LTC", "gamma_netflow_Dogecoin", "m"]
                            else:
                                param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", 
                                             "gamma_netflow_BCH", "gamma_netflow_BSV", "gamma_netflow_ETH", 
                                             "gamma_netflow_LTC", "gamma_netflow_Dogecoin", "m"]
                            
                            # 保存结果
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