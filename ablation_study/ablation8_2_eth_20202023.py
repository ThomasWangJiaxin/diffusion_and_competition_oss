"""
M8.2 Ablation: Bass + Cryptocurrency Price + Profession-logic Events
             + Herding-logic Events + In-flow Effects
=====================================================================
p(t) = p0 + alpha * price(t) + beta * p_event(t)
q(t) = q0 + beta_q * q_event(t)
In-flow  Effects: YES  — direct M_j^in(t)  +  gamma_in * M_j^in_norm(t-1)
Out-flow Effects: NO

ΔN(t) = [p0 + alpha * price(t) + beta * p_event(t) + q(t) * N(t-1)/m
         + Σ γ_j^in * M_j^in_norm(t-1)] * (m - N(t-1))
        + Σ M_j^in(t)

price_transforms: linear | log | exp
p_form options:   linear | log
q_form options:   linear | log | exp

Parameters: [p0, alpha, beta, q0, beta_q, gamma_in × J, m]   total = 5 + J + 1
Loops over: PRICE_LAG_COLS × price_transforms{linear,log,exp}
            × P_EVENT_LIST × p_forms{linear,log}
            × Q_EVENT_LIST × q_forms{linear,log,exp}
            = 2 × 3 × 2 × 2 × 2 × 3 = 144 combinations
"""
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
DATE_COL       = "date"
NEW_COL        = "eth_new_developers"
CUM_COL        = "eth_cum_users"
START_DATE     = "2020-10-01"
END_DATE       = "2023-01-01"
OUTPUT_CSV     = "/home/lab0/survival_diffusion_github/ablation_study/ablation_M8_2_eth_price_pevent_qevent_inflow_20202023.csv"

COMPETITORS = ["BTC", "Solana", "Cosmos", "BNBChain", "Erigon", "Optimism", "TRON", "Aptos", "Sui", "Besu", "Nethermind", "Avalanche", "Polygon", "Arweave", "Near", "FLOW", "Harmony", "Reth", "Ethereumpow", "THETA"]

PRICE_LAG_COLS = [
    # "eth_price_lag1","eth_ma_7d","eth_ma_14d","eth_ma_21d","eth_ma_30d"
    "eth_ma_21d"
]
P_EVENT_LIST = [
    # "eth_p_event_lag1","eth_p_event_sum_7","eth_p_event_sum_14","eth_p_event_sum_21","eth_p_event_sum_30"
    "eth_p_event_sum_21"
]
Q_EVENT_LIST = [
    # "eth_q_event_lag1","eth_q_event_sum_7","eth_q_event_sum_14","eth_q_event_sum_21","eth_q_event_sum_30"
    "eth_q_event_sum_7"
]
# =====================================

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

    mask   = y_true != 0
    mape   = np.mean(np.abs(resid[mask] / y_true[mask])) * 100 if mask.sum() > 0 else np.nan

    denom  = np.sum(np.abs(y_true))
    wape   = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan

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

def compute_p_t(price_array, p_event_arr, p0, alpha, beta, p_form):
    ev = normalize(p_event_arr)
    if p_form == "linear":
        p_t = p0 + alpha * price_array + beta * ev
    elif p_form == "log":
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
    else:
        raise ValueError(f"未知 p_form: {p_form}")
    return np.maximum(p_t, 0)

def compute_q_t(event_arr, q0, beta_q, q_form):
    ev = normalize(event_arr)
    if q_form == "linear":
        return np.maximum(q0 + beta_q * ev, 0)
    elif q_form == "log":
        return np.maximum(q0 + beta_q * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        return q0 * np.exp(beta_q * ev)
    else:
        raise ValueError(f"未知 q_form: {q_form}")

# ----------------- 参数索引 -----------------
def get_param_indices_M72():
    """
    参数布局: [p0, alpha, beta, q0, beta_q, gamma_in × J, m]
    索引:       0    1     2    3    4       5 … 4+J         5+J
    """
    n_comp      = len(COMPETITORS)
    gamma_start = 5               # p0=0, alpha=1, beta=2, q0=3, beta_q=4
    m_idx       = gamma_start + n_comp
    total       = m_idx + 1
    return gamma_start, m_idx, total

# ----------------- 核心预测函数 -----------------
def compute_prediction_M72(df, params, price_array,
                           p_event_col, p_form, q_event_col, q_form,
                           inflow_dict):
    """
    ΔN(t) = [p0 + alpha*price(t) + beta*p_event(t) + q(t)*N(t-1)/m
             + Σ γ_j^in * M_j^in_norm(t-1)] * (m - N(t-1))
            + Σ M_j^in(t)
    """
    n_comp                = len(COMPETITORS)
    gamma_start, m_idx, _ = get_param_indices_M72()

    p0       = params[0]
    alpha    = params[1]
    beta     = params[2]
    q0       = params[3]
    beta_q   = params[4]
    gamma_in = params[gamma_start: gamma_start + n_comp]
    m        = params[m_idx]

    N_lag     = df["N_lag"].values
    remaining = np.maximum(m - N_lag, 0)

    p_t       = compute_p_t(price_array, df[p_event_col].values, p0, alpha, beta, p_form)
    q_t       = compute_q_t(df[q_event_col].values, q0, beta_q, q_form)
    base_rate = p_t + q_t * (N_lag / m)

    # 迁入网络效应（正向，t-1 标准化）
    inflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            M_in      = inflow_dict[coin]
            M_in_lag  = np.concatenate([[0], M_in[:-1]])
            M_in_norm = normalize(M_in_lag)
            inflow_network_rate += gamma_in[i] * M_in_norm

    constrained_growth = np.maximum(base_rate + inflow_network_rate, 0) * remaining

    # 直接迁入（t 期原始值）
    direct_migration = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct_migration += inflow_dict[coin]

    return constrained_growth + direct_migration


def residuals_M72(params, df, price_array,
                  p_event_col, p_form, q_event_col, q_form, inflow_dict):
    p0 = params[0]
    q0 = params[3]
    _, m_idx, _ = get_param_indices_M72()
    m  = params[m_idx]

    if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6

    dN_pred = compute_prediction_M72(
        df, params, price_array, p_event_col, p_form, q_event_col, q_form, inflow_dict)
    if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0):
        return np.ones(len(df)) * 1e6

    return df[NEW_COL].values - dN_pred


def fit_M72(df, price_array, p_event_col, p_form, q_event_col, q_form, inflow_dict):
    try:
        m_guess                   = 1.2 * df[CUM_COL].max()
        n_comp                    = len(COMPETITORS)
        gamma_start, m_idx, total = get_param_indices_M72()

        # 初始值与边界: [p0, alpha, beta, q0, beta_q, gamma_in × J, m]
        init = ([0.001, 0.01,  0.01,  0.01, 0.01]
                + [0.0001] * n_comp
                + [m_guess])
        lo   = ([0,    -10,   -10,    0,   -10]
                + [-0.01] * n_comp
                + [0.9 * m_guess])
        hi   = ([1,     10,    10,    1,    10]
                + [0.01]  * n_comp
                + [20   * m_guess])

        res = least_squares(residuals_M72, init, bounds=(lo, hi),
                            args=(df, price_array, p_event_col, p_form,
                                  q_event_col, q_form, inflow_dict),
                            method="trf")
        if not res.success:
            return None

        params = res.x
        n      = len(df)
        k      = len(params)
        eps    = 1e-6

        y_pred = compute_prediction_M72(
            df, params, price_array, p_event_col, p_form, q_event_col, q_form, inflow_dict)

        # 数值 Jacobian
        J = []
        for i in range(k):
            p_eps      = params.copy()
            p_eps[i]  += eps
            y_eps      = compute_prediction_M72(
                df, p_eps, price_array, p_event_col, p_form,
                q_event_col, q_form, inflow_dict)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T

        try:
            cond = np.linalg.cond(J.T @ J)
        except np.linalg.LinAlgError:
            cond = np.nan

        resid_vec = df[NEW_COL].values - y_pred
        sigma2    = np.sum(resid_vec ** 2) / (n - k)

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

# --------- 加载迁移数据（仅迁入） ----------
def load_inflow_data(migration_path, main_df):
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}");  return None

    if 'date' not in df_mig.columns:
        print("⚠️ 迁移数据缺少 'date' 列");  return None

    date_range = pd.date_range(start=main_df[DATE_COL].min(),
                               end=main_df[DATE_COL].max(), freq='D')
    df_full   = pd.DataFrame({DATE_COL: date_range})
    df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')

    inflow_col_mapping = {
        "Aptos": "in_from_Aptos",
        # "Alephzero": "in_from_Alephzero",
        # "Arbitrum": "in_from_Arbitrum",
        "Arweave": "in_from_Arweave",
        "Avalanche": "in_from_Avalanche",
        "Besu": "in_from_Besu",
        "BNBChain": "in_from_BNBChain",
        "BTC": "in_from_BTC",
        "Cosmos": "in_from_Cosmos",
        # "ETC": "in_from_ETC",
        "Erigon": "in_from_Erigon",
        "Ethereumpow": "in_from_Ethereumpow",
        "FLOW": "in_from_FLOW",
        "Harmony": "in_from_Harmony",
        # "Helium": "in_from_Helium",
        "Near": "in_from_Near",
        "Nethermind": "in_from_Nethermind",
        "Optimism": "in_from_Optimism",
        # "Polkadot": "in_from_Polkadot",
        "Polygon": "in_from_Polygon",
        "Reth": "in_from_Reth",
        # "Ronin": "in_from_Ronin",
        # "SKALE": "in_from_SKALE",
        "Sui": "in_from_Sui",
        # "SecretNetwork": "in_from_SecretNetwork",
        "Solana": "in_from_Solana",
        # "Starknet": "in_from_Starknet",
        "THETA": "in_from_THETA",
        "TRON": "in_from_TRON",
        # "Zksync": "in_from_Zksync",
    }

    df_merged_indexed = df_merged.set_index(DATE_COL)
    main_dates        = pd.DatetimeIndex(main_df[DATE_COL].values)
    inflow_dict       = {}

    for coin in COMPETITORS:
        actual_col = inflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            inflow_dict[coin] = (df_merged_indexed
                                 .reindex(main_dates)[actual_col]
                                 .fillna(0).values)
            print(f"✅ 成功加载 {coin} 的迁入数据列: {actual_col}")
        else:
            inflow_dict[coin] = np.zeros(len(main_df))
            print(f"⚠️ 未找到 {coin} 对应的迁入列: {actual_col}")

    print("\n📈 迁入数据统计（窗口期内）:")
    for coin in COMPETITORS:
        M_in = inflow_dict[coin]
        nz   = np.sum(M_in > 0)
        if nz > 0:
            print(f"  {coin:20s}: 总数={np.sum(M_in):6.0f}, 非零天数={nz:4d}")
        else:
            print(f"  {coin:20s}: 无数据")

    return inflow_dict

# ----------------- 主程序 -----------------
def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}");  sys.exit(1)

    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    required_cols = ([DATE_COL, NEW_COL, CUM_COL]
                     + list(PRICE_LAG_COLS)
                     + list(P_EVENT_LIST)
                     + list(Q_EVENT_LIST))
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        print(f"⚠️ 缺少必要列: {missing}");  sys.exit(1)

    df = df_raw[[DATE_COL, NEW_COL, CUM_COL]
                + list(PRICE_LAG_COLS)
                + list(P_EVENT_LIST)
                + list(Q_EVENT_LIST)].copy()
    df = df.fillna(method="ffill").fillna(0)
    df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) &
            (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
    # 新增：窗口内累积归零
    df[CUM_COL] = df[NEW_COL].cumsum()

    if df.empty:
        print("⚠️ 日期窗口内无数据，退出。");  sys.exit(1)

    df["N_lag"] = df[CUM_COL].shift(1).fillna(0).values

    print(f"\n📊 数据窗口: {START_DATE} ~ {END_DATE},  共 {len(df)} 行")

    # 加载迁入数据（只需加载一次）
    inflow_dict = load_inflow_data(MIGRATION_PATH, df)
    if inflow_dict is None:
        print("⚠️ 无法加载迁入数据，退出。");  sys.exit(1)

    # 动态生成参数名
    param_names = ["p0", "alpha", "beta", "q0", "beta_q"]
    for coin in COMPETITORS:
        param_names.append(f"gamma_in_{coin}")
    param_names.append("m")

    results        = []
    combos_done    = 0
    combos_skipped = 0

    for price_col in PRICE_LAG_COLS:
        raw_price = df[price_col].values.astype(float)

        try:
            price_transforms = {
                # "linear": normalize(raw_price),
                "log":    normalize(np.log(np.maximum(raw_price, 1e-8))),
                # "exp":    normalize(np.exp(np.clip(raw_price, -50, 50)))
            }
        except Exception:
            print(f"⚠️ price transform error for {price_col}, skipping.")
            continue

        for pt_name, price_arr in price_transforms.items():
            for p_event_col in P_EVENT_LIST:
                for p_form in ["linear"]:
                    for q_event_col in Q_EVENT_LIST:
                        for q_form in ["linear"]:
                            model_tag = (f"price={price_col}({pt_name}) | "
                                         f"P={p_event_col}({p_form}) | "
                                         f"Q={q_event_col}({q_form})")
                            print(f"\n→ 拟合 M8.2: {model_tag}")

                            res = fit_M72(df, price_arr,
                                          p_event_col, p_form,
                                          q_event_col, q_form,
                                          inflow_dict)

                            if res is None:
                                print("  ✖ 拟合失败或不收敛，跳过。")
                                combos_skipped += 1
                                continue

                            combos_done += 1
                            params  = res.x
                            k       = len(params)
                            y_pred  = compute_prediction_M72(
                                df, params, price_arr,
                                p_event_col, p_form, q_event_col, q_form,
                                inflow_dict)
                            metrics = compute_metrics(df[NEW_COL].values, y_pred, k)

                            # 打印结果
                            for name, val, se, tv, pv in zip(
                                    param_names, params, res.se, res.tvals, res.pvals):
                                print(f"  {name:25s} = {val:12.6f}  SE={se:.6f}  "
                                      f"t={tv:.3f}  p={pv:.4f}")
                            print(f"  MAD={metrics['MAD']:.4f}  RMSE={metrics['RMSE']:.4f}  "
                                  f"R²={metrics['R2']:.4f}  Adj_R²={metrics['Adj_R2']:.4f}")
                            print(f"  MAPE={metrics['MAPE']:.2f}%  WAPE={metrics['WAPE']:.2f}%")
                            print(f"  cond(J'J) = {res.cond:.4e}")

                            row = {
                                "model":       "M8.2",
                                "start":       START_DATE,
                                "end":         END_DATE,
                                "price_col":   price_col,
                                "price_tf":    pt_name,
                                "p_event_col": p_event_col,
                                "p_form":      p_form,
                                "q_event_col": q_event_col,
                                "q_form":      q_form,
                                **metrics,
                                "cond":        float(res.cond),
                            }
                            for i, name in enumerate(param_names):
                                row[name]           = float(params[i])
                                row["se_"  + name]  = float(res.se[i])
                                row["t_"   + name]  = float(res.tvals[i])
                                row["p_"   + name]  = float(res.pvals[i])

                            results.append(row)

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 完成。组合成功 {combos_done} 次，跳过 {combos_skipped} 次。")
    print(f"✅ 结果已保存：{OUTPUT_CSV}")

if __name__ == "__main__":
    main()