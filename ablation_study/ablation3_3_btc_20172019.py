"""
M3.3 Ablation: Bass + Cryptocurrency Price + Out-flow Effects
=============================================================
p(t) = p0 + alpha * price(t)   (price only, no profession-logic events)
q(t) = q0                       (no herding-logic events)
In-flow  Effects: NO
Out-flow Effects: YES  — delta_out * M_j^out_norm(t-1)  [negative network effect]

DeltaN(t) = [p0 + alpha * price(t) + q0 * N(t-1)/m
             - sum_j delta_j^out * M_j^out_norm(t-1)] * (m - N(t-1))

Parameters: [p0, alpha, q0, delta_out x J, m]   total = 3 + J + 1
Loops over: PRICE_LAG_COLS x price_transforms{linear, log, exp}
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
CSV_PATH       = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv"
DATE_COL       = "date"
NEW_COL        = "btc_new_developers"
CUM_COL        = "btc_cum_users"
START_DATE     = "2017-01-01"
END_DATE       = "2019-01-01"
OUTPUT_CSV     = "/home/lab0/survival_diffusion_github/ablation_study/ablation_M3_3_btc_price_outflow_20172019.csv"

COMPETITORS = ["ETH", "Dogecoin", "Lightning Network", "Monero", "Litecoin", "BTCD", "Zcash", "BCOIN", "TRON", "Stacks", "BitcoinCash", "LBTC", "BitcoinGpu", "Parity", "Rootstock"]

PRICE_LAG_COLS = [
    # "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
    "btc_ma_7d"
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

# ----------------- 参数索引 -----------------
def get_param_indices_M23():
    """
    Layout: [p0, alpha, q0, delta_out x J, m]
    Index:    0    1     2   3 ... 2+J       2+J+1
    """
    n_comp      = len(COMPETITORS)
    delta_start = 3                        # p0=0, alpha=1, q0=2
    m_idx       = delta_start + n_comp
    total       = m_idx + 1
    return delta_start, m_idx, total

# ----------------- 核心预测函数 -----------------
def compute_prediction_M23(df, params, price_array, outflow_dict):
    n_comp                 = len(COMPETITORS)
    delta_start, m_idx, _  = get_param_indices_M23()

    p0        = params[0]
    alpha     = params[1]
    q0        = params[2]
    delta_out = params[delta_start: delta_start + n_comp]
    m         = params[m_idx]

    N_lag     = df["N_lag"].values
    remaining = np.maximum(m - N_lag, 0)
    base_rate = p0 + alpha * price_array + q0 * (N_lag / m)

    outflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            M_out      = outflow_dict[coin]
            M_out_lag  = np.concatenate([[0], M_out[:-1]])
            M_out_norm = normalize(M_out_lag)
            outflow_network_rate += delta_out[i] * M_out_norm

    total_rate = base_rate - outflow_network_rate
    return np.maximum(total_rate, 0) * remaining


def residuals_M23(params, df, price_array, outflow_dict):
    p0 = params[0]
    q0 = params[2]
    _, m_idx, _ = get_param_indices_M23()
    m  = params[m_idx]
    if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_pred = compute_prediction_M23(df, params, price_array, outflow_dict)
    if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - dN_pred


def fit_M23(df, price_array, outflow_dict):
    try:
        m_guess                    = 1.2 * df[CUM_COL].max()
        n_comp                     = len(COMPETITORS)
        delta_start, m_idx, total  = get_param_indices_M23()

        # [p0, alpha, q0, delta_out x J, m]
        init = ([0.001, 0.01, 0.01] + [0.0001] * n_comp + [m_guess])
        lo   = ([0,    -10,   0]    + [-0.01]  * n_comp + [0.9 * m_guess])
        hi   = ([1,     10,   1]    + [0.01]   * n_comp + [20  * m_guess])

        res = least_squares(residuals_M23, init, bounds=(lo, hi),
                            args=(df, price_array, outflow_dict),
                            method="trf")
        if not res.success:
            return None

        params = res.x
        n      = len(df)
        k      = len(params)
        eps    = 1e-6

        y_pred = compute_prediction_M23(df, params, price_array, outflow_dict)

        J = []
        for i in range(k):
            p_eps      = params.copy()
            p_eps[i]  += eps
            y_eps      = compute_prediction_M23(df, p_eps, price_array, outflow_dict)
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

    print(f"\n📊 迁移数据列名: {df_mig.columns.tolist()}")
    print(f"📊 迁移数据日期范围: {df_mig['date'].min()} 到 {df_mig['date'].max()}")

    if 'date' not in df_mig.columns:
        print("⚠️ 迁移数据缺少 'date' 列");  return None

    date_range = pd.date_range(start=main_df[DATE_COL].min(),
                               end=main_df[DATE_COL].max(), freq='D')
    df_full   = pd.DataFrame({DATE_COL: date_range})
    df_merged = df_full.merge(df_mig, left_on=DATE_COL, right_on='date', how='left')

    outflow_col_mapping = {
        "BCOIN": "out_to_BCOIN",
        # "BNBChain": "out_to_BNBChain",
        # "BOB": "out_to_BOB",
        "BTCD": "out_to_BTCD",
        "BitcoinCash": "out_to_BitcoinCash",
        # "eCash": "out_to_eCash",
        "BitcoinGpu": "out_to_BitcoinGpu",
        # "BitcoinSv": "out_to_Bitcoinsv",          # 注意文件里是 Bitcoinsv（小写 s）
        "Dogecoin": "out_to_Dogecoin",
        "ETH": "out_to_ETH",
        "LBTC": "out_to_LBTC",
        "Lightning Network": "out_to_Lightning Network",
        "Litecoin": "out_to_Litecoin",
        "Monero": "out_to_Monero",
        "Parity": "out_to_Parity",
        "Rootstock": "out_to_Rootstock",
        # "Solana": "out_to_Solana",
        "Stacks": "out_to_Stacks",
        "TRON": "out_to_TRON",
        "Zcash": "out_to_Zcash",
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
            print(f"Loaded outflow {coin}: {actual_col}")
        else:
            outflow_dict[coin] = np.zeros(len(main_df))
            print(f"Outflow column not found for {coin}: {actual_col}")

    print("Outflow data summary (window):")
    for coin in COMPETITORS:
        M_out = outflow_dict[coin]
        nz    = np.sum(M_out > 0)
        if nz > 0:
            print(f"  {coin:20s}: total={np.sum(M_out):6.0f}, nonzero_days={nz:4d}")
        else:
            print(f"  {coin:20s}: no data")

    return outflow_dict

# ----------------- 主程序 -----------------
def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}");  sys.exit(1)

    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    required_cols = [DATE_COL, NEW_COL, CUM_COL] + list(PRICE_LAG_COLS)
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        print(f"⚠️ 缺少必要列: {missing}");  sys.exit(1)

    df = df_raw[[DATE_COL, NEW_COL, CUM_COL] + list(PRICE_LAG_COLS)].copy()
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
    param_names = ["p0", "alpha", "q0"]
    for coin in COMPETITORS:
        param_names.append(f"delta_out_{coin}")
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
            model_tag = f"price={price_col}({pt_name})"
            print(f"\n-> Fitting M2.3: {model_tag}")

            res = fit_M23(df, price_arr, outflow_dict)

            if res is None:
                print("  X Fitting failed, skipping.")
                combos_skipped += 1
                continue

            combos_done += 1
            params  = res.x
            k       = len(params)
            y_pred  = compute_prediction_M23(df, params, price_arr, outflow_dict)
            metrics = compute_metrics(df[NEW_COL].values, y_pred, k)

            for name, val, se, tv, pv in zip(
                    param_names, params, res.se, res.tvals, res.pvals):
                print(f"  {name:25s} = {val:12.6f}  SE={se:.6f}  t={tv:.3f}  p={pv:.4f}")
            print(f"  MAD={metrics['MAD']:.4f}  RMSE={metrics['RMSE']:.4f}  "
                  f"R2={metrics['R2']:.4f}  Adj_R2={metrics['Adj_R2']:.4f}")
            print(f"  MAPE={metrics['MAPE']:.2f}%  WAPE={metrics['WAPE']:.2f}%")
            print(f"  cond = {res.cond:.4e}")

            row = {
                "model":     "M3.3",
                "start":     START_DATE,
                "end":       END_DATE,
                "price_col": price_col,
                "price_tf":  pt_name,
                **metrics,
                "cond":      float(res.cond),
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