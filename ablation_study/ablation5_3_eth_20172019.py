"""
M5.3 Ablation: Bass + Profession-logic Events + Out-flow Effects
================================================================
p(t) = p0 + beta * p_event(t)    (profession-logic events, no price)
q(t) = q0                         (no herding-logic events)
In-flow  Effects: NO
Out-flow Effects: YES  — delta_out * M_j^out_norm(t-1)  [negative network effect]

ΔN(t) = [p0 + beta * p_event(t) + q0 * N(t-1)/m
         - Σ δ_j^out * M_j^out_norm(t-1)] * (m - N(t-1))

p_form options:
  "linear"  : p(t) = p0 + beta * ev
  "log"     : p(t) = p0 + beta * log(1 + ev+)

Parameters: [p0, beta, q0, delta_out × J, m]   total = 3 + J + 1
Loops over: P_EVENT_LIST × p_forms{linear, log}
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
START_DATE     = "2017-01-01"
END_DATE       = "2019-01-01"
OUTPUT_CSV     = "/home/lab0/survival_diffusion_github/ablation_study/ablation_M5_3_eth_pevent_outflow_20172019.csv"

COMPETITORS = ["BTC", "Solana", "Cosmos", "TRON"]

P_EVENT_LIST = [
    # "eth_p_event_lag1","eth_p_event_sum_7","eth_p_event_sum_14","eth_p_event_sum_21","eth_p_event_sum_30"
    "eth_p_event_sum_30"
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

def compute_p_t(event_arr, p0, beta, p_form):
    ev = normalize(event_arr)
    if p_form == "linear":
        p_t = p0 + beta * ev
    elif p_form == "log":
        p_t = p0 + beta * np.log1p(np.maximum(ev, 0))
    else:
        raise ValueError(f"未知 p_form: {p_form}")
    return np.maximum(p_t, 0)

# ----------------- 参数索引 -----------------
def get_param_indices_M43():
    """
    参数布局: [p0, beta, q0, delta_out × J, m]
    索引:       0    1    2   3 … 2+J         3+J
    """
    n_comp      = len(COMPETITORS)
    delta_start = 3               # p0=0, beta=1, q0=2
    m_idx       = delta_start + n_comp
    total       = m_idx + 1
    return delta_start, m_idx, total

# ----------------- 核心预测函数 -----------------
def compute_prediction_M43(df, params, p_event_col, p_form, outflow_dict):
    """
    ΔN(t) = [p0 + beta*p_event(t) + q0*N(t-1)/m
             - Σ δ_j^out * M_j^out_norm(t-1)] * (m - N(t-1))
    """
    n_comp                 = len(COMPETITORS)
    delta_start, m_idx, _  = get_param_indices_M43()

    p0        = params[0]
    beta      = params[1]
    q0        = params[2]
    delta_out = params[delta_start: delta_start + n_comp]
    m         = params[m_idx]

    N_lag     = df["N_lag"].values
    remaining = np.maximum(m - N_lag, 0)

    p_t       = compute_p_t(df[p_event_col].values, p0, beta, p_form)
    base_rate = p_t + q0 * (N_lag / m)

    # 迁出网络效应（负向，t-1 标准化）
    outflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            M_out      = outflow_dict[coin]
            M_out_lag  = np.concatenate([[0], M_out[:-1]])
            M_out_norm = normalize(M_out_lag)
            outflow_network_rate += delta_out[i] * M_out_norm

    total_rate = base_rate - outflow_network_rate

    return np.maximum(total_rate, 0) * remaining


def residuals_M43(params, df, p_event_col, p_form, outflow_dict):
    p0 = params[0]
    q0 = params[2]
    _, m_idx, _ = get_param_indices_M43()
    m  = params[m_idx]

    if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6

    dN_pred = compute_prediction_M43(df, params, p_event_col, p_form, outflow_dict)
    if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0):
        return np.ones(len(df)) * 1e6

    return df[NEW_COL].values - dN_pred


def fit_M43(df, p_event_col, p_form, outflow_dict):
    try:
        m_guess                   = 1.2 * df[CUM_COL].max()
        n_comp                    = len(COMPETITORS)
        delta_start, m_idx, total = get_param_indices_M43()

        # 初始值与边界: [p0, beta, q0, delta_out × J, m]
        init = ([0.001, 0.01, 0.01]
                + [0.0001] * n_comp
                + [m_guess])
        lo   = ([0,    -10,   0]
                + [-0.01] * n_comp
                + [0.9 * m_guess])
        hi   = ([1,     10,   1]
                + [0.01]  * n_comp
                + [20   * m_guess])

        res = least_squares(residuals_M43, init, bounds=(lo, hi),
                            args=(df, p_event_col, p_form, outflow_dict),
                            method="trf")
        if not res.success:
            return None

        params = res.x
        n      = len(df)
        k      = len(params)
        eps    = 1e-6

        y_pred = compute_prediction_M43(df, params, p_event_col, p_form, outflow_dict)

        # 数值 Jacobian
        J = []
        for i in range(k):
            p_eps      = params.copy()
            p_eps[i]  += eps
            y_eps      = compute_prediction_M43(df, p_eps, p_event_col, p_form, outflow_dict)
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

# --------- 加载迁移数据（仅迁出） ----------
def load_outflow_data(migration_path, main_df):
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

    outflow_col_mapping = {
        # "Aptos": "out_to_Aptos",
        # "Alephzero": "out_to_Alephzero",
        # "Arbitrum": "out_to_Arbitrum",
        # "Arweave": "out_to_Arweave",
        # "Avalanche": "out_to_Avalanche",
        # "Besu": "out_to_Besu",
        # "BNBChain": "out_to_BNBChain",
        "BTC": "out_to_BTC",
        "Cosmos": "out_to_Cosmos",
        # "ETC": "out_to_ETC",
        # "Erigon": "out_to_Erigon",
        # "Ethereumpow": "out_to_Ethereumpow",
        # "FLOW": "out_to_FLOW",
        # "Harmony": "out_to_Harmony",
        # "Helium": "out_to_Helium",
        # "Near": "out_to_Near",
        # "Nethermind": "out_to_Nethermind",
        # "Optimism": "out_to_Optimism",
        # "Polkadot": "out_to_Polkadot",
        # "Polygon": "out_to_Polygon",
        # "Reth": "out_to_Reth",
        # "Ronin": "out_to_Ronin",
        # "SKALE": "out_to_SKALE",
        # "Sui": "out_to_Sui",
        # "SecretNetwork": "out_to_Secretnetwork",  # 注意这里文件里是小写 n
        "Solana": "out_to_Solana",
        # "Starknet": "out_to_Starknet",
        # "THETA": "out_to_THETA",
        "TRON": "out_to_TRON",
        # "Zksync": "out_to_Zksync",
    }

    df_merged_indexed = df_merged.set_index(DATE_COL)
    main_dates        = pd.DatetimeIndex(main_df[DATE_COL].values)
    outflow_dict      = {}

    for coin in COMPETITORS:
        actual_col = outflow_col_mapping.get(coin)
        if actual_col and actual_col in df_merged.columns:
            outflow_dict[coin] = (df_merged_indexed
                                  .reindex(main_dates)[actual_col]
                                  .fillna(0).values)
            print(f"✅ 成功加载 {coin} 的迁出数据列: {actual_col}")
        else:
            outflow_dict[coin] = np.zeros(len(main_df))
            print(f"⚠️ 未找到 {coin} 对应的迁出列: {actual_col}")

    print("\n📈 迁出数据统计（窗口期内）:")
    for coin in COMPETITORS:
        M_out = outflow_dict[coin]
        nz    = np.sum(M_out > 0)
        if nz > 0:
            print(f"  {coin:20s}: 总数={np.sum(M_out):6.0f}, 非零天数={nz:4d}")
        else:
            print(f"  {coin:20s}: 无数据")

    return outflow_dict

# ----------------- 主程序 -----------------
def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}");  sys.exit(1)

    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    required_cols = [DATE_COL, NEW_COL, CUM_COL] + list(P_EVENT_LIST)
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        print(f"⚠️ 缺少必要列: {missing}");  sys.exit(1)

    df = df_raw[[DATE_COL, NEW_COL, CUM_COL] + list(P_EVENT_LIST)].copy()
    df = df.fillna(method="ffill").fillna(0)
    df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) &
            (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
    # 新增：窗口内累积归零
    df[CUM_COL] = df[NEW_COL].cumsum()

    if df.empty:
        print("⚠️ 日期窗口内无数据，退出。");  sys.exit(1)

    df["N_lag"] = df[CUM_COL].shift(1).fillna(0).values

    print(f"\n📊 数据窗口: {START_DATE} ~ {END_DATE},  共 {len(df)} 行")

    # 加载迁出数据（只需加载一次）
    outflow_dict = load_outflow_data(MIGRATION_PATH, df)
    if outflow_dict is None:
        print("⚠️ 无法加载迁出数据，退出。");  sys.exit(1)

    # 动态生成参数名
    param_names = ["p0", "beta", "q0"]
    for coin in COMPETITORS:
        param_names.append(f"delta_out_{coin}")
    param_names.append("m")

    results        = []
    combos_done    = 0
    combos_skipped = 0

    for p_event_col in P_EVENT_LIST:
        for p_form in ["linear"]:
            model_tag = f"P={p_event_col} | p_form={p_form}"
            print(f"\n→ 拟合 M5.3: {model_tag}")

            res = fit_M43(df, p_event_col, p_form, outflow_dict)

            if res is None:
                print("  ✖ 拟合失败或不收敛，跳过。")
                combos_skipped += 1
                continue

            combos_done += 1
            params  = res.x
            k       = len(params)
            y_pred  = compute_prediction_M43(df, params, p_event_col, p_form, outflow_dict)
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
                "model":       "M5.3",
                "start":       START_DATE,
                "end":         END_DATE,
                "p_event_col": p_event_col,
                "p_form":      p_form,
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