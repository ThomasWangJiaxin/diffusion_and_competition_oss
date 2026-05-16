import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import math
import sys

# ============= 参数配置 =============
CSV_PATH       = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv"
DATE_COL   = "date"
NEW_COL    = "eth_new_developers"
CUM_COL    = "eth_cum_users"
START_DATE = "2020-10-01"
END_DATE   = "2023-01-01"
OUTPUT_CSV = "/home/lab0/survival_diffusion_github/sensitivity/market_size/eth_bass_m_sensitivity_20202023.csv"

COMPETITORS = [
    "BTC", "Solana", "Cosmos", "BNBChain", "Erigon", "Optimism",
    "TRON", "Aptos", "Sui", "Besu", "Nethermind", "Avalanche",
    "Polygon", "Arweave", "Near", "FLOW", "Harmony", "Reth",
    "EthereumPOW", "THETA"
]

P_EVENT_LIST = [
    "eth_p_event_lag1", "eth_p_event_sum_7", "eth_p_event_sum_14",
    "eth_p_event_sum_21", "eth_p_event_sum_30"
]
Q_EVENT_LIST = [
    "eth_q_event_lag1", "eth_q_event_sum_7", "eth_q_event_sum_14",
    "eth_q_event_sum_21", "eth_q_event_sum_30"
]
PRICE_LAG_COLS = [
    "eth_price_lag1", "eth_ma_7d", "eth_ma_14d", "eth_ma_21d", "eth_ma_30d"
]

M_MULTIPLIERS = [1.1, 1.2, 1.5, 2.0, 3.0, 5.0]
P_MODEL_LIST  = ["additive", "nonlinear_event"]

# ----------------- 评估指标 -----------------
def compute_metrics(y_true, y_pred, k):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    n      = len(y_true)
    resid  = y_true - y_pred
    sse    = np.sum(resid ** 2)
    mse    = sse / n
    rmse   = math.sqrt(mse)
    mad    = np.mean(np.abs(resid))
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2     = 1 - sse / ss_tot if ss_tot > 0 else np.nan
    adj_r2 = (1 - (1 - r2) * (n - 1) / (n - k - 1)
              if (n - k - 1 > 0 and ss_tot > 0) else np.nan)
    mask = y_true != 0
    mape = (np.mean(np.abs(resid[mask] / y_true[mask])) * 100
            if mask.sum() > 0 else np.nan)
    denom = np.sum(np.abs(y_true))
    wape  = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan
    return {"MAD": mad, "SSE": sse, "MSE": mse, "RMSE": rmse,
            "R2": r2, "Adj_R2": adj_r2, "MAPE": mape, "WAPE": wape}

# ----------------- 工具函数 -----------------
def normalize(x):
    x    = np.array(x, dtype=float)
    mean = np.mean(x)
    std  = np.std(x)
    if std <= 0:
        return x - mean
    return (x - mean) / (std + 1e-12)

def compute_q_t_from_array(event_arr, q_params, q_form):
    q0, beta = q_params
    ev = normalize(event_arr)
    if q_form == "linear":
        return np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":
        return np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        return q0 * np.exp(beta * ev)
    raise ValueError(f"未知 q_form: {q_form}")

def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    ev = normalize(df[p_event_col].values)
    if p_model == "additive":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * ev
    elif p_model == "nonlinear_event":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
    else:
        raise ValueError(f"未知 p_model: {p_model}")
    return np.maximum(p_t, 0)

def get_param_indices(p_model):
    n_comp        = len(COMPETITORS)
    p_param_count = 3
    q_start       = p_param_count
    gamma_start   = q_start + 2
    delta_start   = gamma_start + n_comp
    m_idx         = delta_start + n_comp
    total         = m_idx + 1
    return p_param_count, q_start, gamma_start, delta_start, m_idx, total

def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m,
                      inflow_dict, outflow_dict,
                      gamma_in_params, delta_out_params):
    remaining = np.maximum(m - N_lag, 0)
    base_rate = p_t_arr + q_t_arr * (N_lag / m)

    inflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            M_in     = inflow_dict[coin]
            M_in_lag = np.concatenate([[0], M_in[:-1]])
            inflow_network_rate += gamma_in_params[i] * normalize(M_in_lag)

    outflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            M_out     = outflow_dict[coin]
            M_out_lag = np.concatenate([[0], M_out[:-1]])
            outflow_network_rate += delta_out_params[i] * normalize(M_out_lag)

    total_rate         = base_rate + inflow_network_rate - outflow_network_rate
    constrained_growth = total_rate * remaining

    direct_migration = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct_migration += inflow_dict[coin]

    return constrained_growth + direct_migration

def compute_prediction_pair(df, params, price_array,
                             p_event_col, q_event_col,
                             p_model, q_form,
                             inflow_dict, outflow_dict):
    p_param_count, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
    p_params         = params[:p_param_count]
    q0, beta_q       = params[q_start], params[q_start + 1]
    gamma_in_params  = params[gamma_start: gamma_start + len(COMPETITORS)]
    delta_out_params = params[delta_start: delta_start + len(COMPETITORS)]
    m                = params[m_idx]

    p_t   = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t   = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    N_lag = df["N_lag"].values
    dN    = dN_pred_from_Nlag(N_lag, p_t, q_t, m,
                               inflow_dict, outflow_dict,
                               gamma_in_params, delta_out_params)
    return dN, p_t, q_t

def residuals_pair(params, df, price_array,
                   p_event_col, q_event_col,
                   p_model, q_form,
                   inflow_dict, outflow_dict):
    _, q_start, _, _, m_idx, _ = get_param_indices(p_model)
    q0 = params[q_start]
    m  = params[m_idx]
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _, _ = compute_prediction_pair(
        df, params, price_array, p_event_col, q_event_col,
        p_model, q_form, inflow_dict, outflow_dict)
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - dN_predicted

def fit_bass_pair(df, price_array,
                  p_event_col, q_event_col,
                  p_model, q_form,
                  inflow_dict, outflow_dict,
                  m_mult):
    try:
        N_max   = df[CUM_COL].max()
        m_guess = m_mult * N_max
        lo_m    = 1.08  * N_max
        hi_m    = 24 * N_max
        n_comp  = len(COMPETITORS)

        _, q_start, gamma_start, delta_start, m_idx, total = get_param_indices(p_model)

        p_init = [0.001, 0.01, 0.01]; p_lo = [0, -10, -10]; p_hi = [1, 10, 10]
        q_init = [0.01, 0.01];        q_lo = [0, -10];       q_hi = [1, 10]
        gamma_init = [0.0001] * n_comp; gamma_lo = [-0.01] * n_comp; gamma_hi = [0.01] * n_comp
        delta_init = [0.0001] * n_comp; delta_lo = [-0.01] * n_comp; delta_hi = [0.01] * n_comp

        init = p_init + q_init + gamma_init + delta_init + [m_guess]
        lo   = p_lo   + q_lo   + gamma_lo   + delta_lo   + [lo_m]
        hi   = p_hi   + q_hi   + gamma_hi   + delta_hi   + [hi_m]

        res = least_squares(
            residuals_pair, init, bounds=(lo, hi),
            args=(df, price_array, p_event_col, q_event_col,
                  p_model, q_form, inflow_dict, outflow_dict),
            method="trf")

        if not res.success:
            return None

        params = res.x
        n      = len(df)
        k      = len(params)
        eps    = 1e-6

        y_pred, _, _ = compute_prediction_pair(
            df, params, price_array, p_event_col, q_event_col,
            p_model, q_form, inflow_dict, outflow_dict)

        J = []
        for i in range(k):
            p_eps       = params.copy(); p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(
                df, p_eps, price_array, p_event_col, q_event_col,
                p_model, q_form, inflow_dict, outflow_dict)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T

        try:
            cond = np.linalg.cond(J.T @ J)
        except np.linalg.LinAlgError:
            cond = np.nan

        resid_vec = df[NEW_COL].values - y_pred
        sigma2    = np.sum(resid_vec ** 2) / max(n - k, 1)
        try:
            cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
            se  = np.sqrt(np.diag(cov))
        except np.linalg.LinAlgError:
            se = np.full(k, np.nan)

        tvals = params / (se + 1e-12)
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        return res

    except Exception as e:
        print(f"  拟合异常: {e}")
        return None

# --------- 加载迁移数据 ----------
def load_migration_data(migration_path, main_df):
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}"); return None, None

    if 'date' not in df_mig.columns:
        print("⚠️ 迁移数据缺少 'date' 列"); return None, None

    date_range = pd.date_range(
        start=main_df[DATE_COL].min(), end=main_df[DATE_COL].max(), freq='D')
    df_full   = pd.DataFrame({DATE_COL: date_range})
    df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')

    inflow_col_mapping = {
        "Aptos":       "in_from_Aptos",
        "Arweave":     "in_from_Arweave",
        "Avalanche":   "in_from_Avalanche",
        "Besu":        "in_from_Besu",
        "BNBChain":    "in_from_BNBChain",
        "BTC":         "in_from_BTC",
        "Cosmos":      "in_from_Cosmos",
        "Erigon":      "in_from_Erigon",
        "EthereumPOW": "in_from_Ethereumpow",
        "FLOW":        "in_from_FLOW",
        "Harmony":     "in_from_Harmony",
        "Near":        "in_from_Near",
        "Nethermind":  "in_from_Nethermind",
        "Optimism":    "in_from_Optimism",
        "Polygon":     "in_from_Polygon",
        "Reth":        "in_from_Reth",
        "Sui":         "in_from_Sui",
        "Solana":      "in_from_Solana",
        "THETA":       "in_from_THETA",
        "TRON":        "in_from_TRON",
    }
    outflow_col_mapping = {
        "Aptos":       "out_to_Aptos",
        "Arweave":     "out_to_Arweave",
        "Avalanche":   "out_to_Avalanche",
        "Besu":        "out_to_Besu",
        "BNBChain":    "out_to_BNBChain",
        "BTC":         "out_to_BTC",
        "Cosmos":      "out_to_Cosmos",
        "Erigon":      "out_to_Erigon",
        "EthereumPOW": "out_to_Ethereumpow",
        "FLOW":        "out_to_FLOW",
        "Harmony":     "out_to_Harmony",
        "Near":        "out_to_Near",
        "Nethermind":  "out_to_Nethermind",
        "Optimism":    "out_to_Optimism",
        "Polygon":     "out_to_Polygon",
        "Reth":        "out_to_Reth",
        "Sui":         "out_to_Sui",
        "Solana":      "out_to_Solana",
        "THETA":       "out_to_THETA",
        "TRON":        "out_to_TRON",
    }

    df_merged_indexed = df_merged.set_index(DATE_COL)
    main_dates        = pd.DatetimeIndex(main_df[DATE_COL].values)
    inflow_dict_aligned  = {}
    outflow_dict_aligned = {}

    for coin in COMPETITORS:
        col_in = inflow_col_mapping.get(coin)
        inflow_dict_aligned[coin] = (
            df_merged_indexed.reindex(main_dates)[col_in].fillna(0).values
            if col_in and col_in in df_merged.columns
            else np.zeros(len(main_df)))

        col_out = outflow_col_mapping.get(coin)
        outflow_dict_aligned[coin] = (
            df_merged_indexed.reindex(main_dates)[col_out].fillna(0).values
            if col_out and col_out in df_merged.columns
            else np.zeros(len(main_df)))

    print("\n📈 迁移数据统计（窗口期内）:")
    for coin in COMPETITORS:
        M_in  = inflow_dict_aligned[coin]
        M_out = outflow_dict_aligned[coin]
        if np.sum(M_in) > 0 or np.sum(M_out) > 0:
            print(f"  {coin:20s}: 迁入总数={np.sum(M_in):6.0f} 迁出总数={np.sum(M_out):6.0f}")

    return inflow_dict_aligned, outflow_dict_aligned

# ----------------- 主程序 -----------------
def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}"); sys.exit(1)

    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)
    results        = []
    combos_done    = 0
    combos_skipped = 0

    for p_event_col in P_EVENT_LIST:
        for q_event_col in Q_EVENT_LIST:
            required_cols = ([DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col]
                             + list(PRICE_LAG_COLS))
            missing = [c for c in required_cols if c not in df_raw.columns]
            if missing:
                print(f"⚠️ 跳过 (缺列): P={p_event_col}, Q={q_event_col}")
                combos_skipped += 1; continue

            df = df_raw[[DATE_COL, NEW_COL, CUM_COL, p_event_col, q_event_col]
                        + list(PRICE_LAG_COLS)].copy()
            df = df.fillna(method="ffill").fillna(0)
            df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) &
                    (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
            if df.empty:
                combos_skipped += 1; continue

            df["N_lag"] = df[CUM_COL].shift(1).fillna(df[CUM_COL].iloc[0]).values

            inflow_dict, outflow_dict = load_migration_data(MIGRATION_PATH, df)
            if inflow_dict is None:
                combos_skipped += 1; continue

            for price_col in PRICE_LAG_COLS:
                raw_price = df[price_col].values.astype(float)
                try:
                    price_transforms = {
                        "linear": normalize(raw_price),
                        "log":    normalize(np.log(np.maximum(raw_price, 1e-8))),
                        "exp":    normalize(np.exp(np.clip(raw_price, -50, 50)))
                    }
                except Exception:
                    continue

                for pt_name, price_arr in price_transforms.items():
                    for p_model in P_MODEL_LIST:
                        for q_form in ["linear", "log", "exp"]:
                            for m_mult in M_MULTIPLIERS:

                                model_tag = (
                                    f"P={p_event_col} | Q={q_event_col} | "
                                    f"price={price_col}({pt_name}) | "
                                    f"p_model={p_model} | q_form={q_form} | "
                                    f"m_mult={m_mult}")
                                print(f"\n→ 拟合: {model_tag}")

                                res = fit_bass_pair(
                                    df, price_arr,
                                    p_event_col, q_event_col,
                                    p_model, q_form,
                                    inflow_dict, outflow_dict,
                                    m_mult=m_mult)

                                if res is None:
                                    print(" ✖ 拟合失败，跳过。")
                                    combos_skipped += 1; continue

                                combos_done += 1
                                params = res.x
                                k      = len(params)

                                dN_pred, _, _ = compute_prediction_pair(
                                    df, params, price_arr,
                                    p_event_col, q_event_col,
                                    p_model, q_form,
                                    inflow_dict, outflow_dict)

                                metrics = compute_metrics(df[NEW_COL].values, dN_pred, k)

                                param_names = ["p0", "alpha", "beta", "q0", "beta_q"]
                                for coin in COMPETITORS:
                                    param_names.append(f"gamma_in_{coin}")
                                for coin in COMPETITORS:
                                    param_names.append(f"delta_out_{coin}")
                                param_names.append("m")

                                row = {
                                    "P_event":   p_event_col,
                                    "Q_event":   q_event_col,
                                    "price_col": price_col,
                                    "price_tf":  pt_name,
                                    "p_model":   p_model,
                                    "q_form":    q_form,
                                    "m_mult":    m_mult,
                                    "m_init":    m_mult * df[CUM_COL].max(),
                                    **metrics,
                                    "cond": float(getattr(res, "cond", np.nan))
                                }

                                for i, name in enumerate(param_names):
                                    row[name]          = float(params[i]) if i < len(params) else np.nan
                                    row["se_"  + name] = float(res.se[i])    if i < len(res.se)    else np.nan
                                    row["t_"   + name] = float(res.tvals[i]) if i < len(res.tvals) else np.nan
                                    row["p_"   + name] = float(res.pvals[i]) if i < len(res.pvals) else np.nan

                                results.append(row)

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 完成。成功 {combos_done} 次，跳过 {combos_skipped} 次。")
    print(f"✅ 结果已保存：{OUTPUT_CSV}")

if __name__ == "__main__":
    main()