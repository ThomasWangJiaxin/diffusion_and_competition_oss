"""
M7.1 Ablation: Bass + Cryptocurrency Price + Profession-logic Events
====================================================================
p(t) = p0 + alpha * price(t) + beta * p_event(t)
q(t) = q0                      (no herding-logic events)
In-flow  Effects: NO
Out-flow Effects: NO

ΔN(t) = [p0 + alpha * price(t) + beta * p_event(t) + q0 * N(t-1)/m]
        * (m - N(t-1))

price_transforms: linear | log | exp
p_form options:   linear | log

Parameters: [p0, alpha, beta, q0, m]   total = 5
Loops over: PRICE_LAG_COLS × price_transforms{linear,log,exp}
            × P_EVENT_LIST × p_forms{linear,log}
            = 2 × 3 × 2 × 2 = 24 combinations
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
CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL   = "date"
NEW_COL    = "eth_new_developers"
CUM_COL    = "eth_cum_users"
START_DATE = "2017-01-01"
END_DATE   = "2019-01-01"
OUTPUT_CSV = "/home/lab0/survival_diffusion_github/ablation_study/ablation_M7_1_eth_price_pevent_20172019.csv"

PRICE_LAG_COLS = [
    # "eth_price_lag1","eth_ma_7d","eth_ma_14d","eth_ma_21d","eth_ma_30d"
    "eth_price_lag1"
]
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

def compute_p_t(price_array, p_event_arr, p0, alpha, beta, p_form):
    """
    p(t) = p0 + alpha * price(t) + beta * p_event(t)
    price_array already normalized outside; p_event normalized here.
    """
    ev  = normalize(p_event_arr)
    if p_form == "linear":
        p_t = p0 + alpha * price_array + beta * ev
    elif p_form == "log":
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
    else:
        raise ValueError(f"未知 p_form: {p_form}")
    return np.maximum(p_t, 0)

# ----------------- 参数索引 -----------------
def get_param_indices_M61():
    """
    参数布局: [p0, alpha, beta, q0, m]
    索引:       0    1     2    3   4
    """
    return {"p0": 0, "alpha": 1, "beta": 2, "q0": 3, "m": 4, "total": 5}

# ----------------- 核心预测函数 -----------------
def compute_prediction_M61(df, params, price_array, p_event_col, p_form):
    """
    ΔN(t) = [p0 + alpha*price(t) + beta*p_event(t) + q0*N(t-1)/m]
            * (m - N(t-1))
    """
    idx   = get_param_indices_M61()
    p0    = params[idx["p0"]]
    alpha = params[idx["alpha"]]
    beta  = params[idx["beta"]]
    q0    = params[idx["q0"]]
    m     = params[idx["m"]]

    N_lag     = df["N_lag"].values
    remaining = np.maximum(m - N_lag, 0)

    p_t  = compute_p_t(price_array, df[p_event_col].values, p0, alpha, beta, p_form)
    rate = p_t + q0 * (N_lag / m)

    return np.maximum(rate, 0) * remaining


def residuals_M61(params, df, price_array, p_event_col, p_form):
    idx = get_param_indices_M61()
    p0  = params[idx["p0"]]
    q0  = params[idx["q0"]]
    m   = params[idx["m"]]

    if m <= df[CUM_COL].max() or q0 < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6

    dN_pred = compute_prediction_M61(df, params, price_array, p_event_col, p_form)
    if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0):
        return np.ones(len(df)) * 1e6

    return df[NEW_COL].values - dN_pred


def fit_M61(df, price_array, p_event_col, p_form):
    try:
        m_guess = 1.2 * df[CUM_COL].max()

        # 初始值与边界: [p0, alpha, beta, q0, m]
        init = [0.001, 0.01,  0.01,  0.01, m_guess]
        lo   = [0,    -10,   -10,    0,    0.9 * m_guess]
        hi   = [1,     10,    10,    1,    20  * m_guess]

        res = least_squares(residuals_M61, init, bounds=(lo, hi),
                            args=(df, price_array, p_event_col, p_form),
                            method="trf")
        if not res.success:
            return None

        params = res.x
        n      = len(df)
        k      = len(params)
        eps    = 1e-6

        y_pred = compute_prediction_M61(df, params, price_array, p_event_col, p_form)

        # 数值 Jacobian
        J = []
        for i in range(k):
            p_eps      = params.copy()
            p_eps[i]  += eps
            y_eps      = compute_prediction_M61(df, p_eps, price_array, p_event_col, p_form)
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

# ----------------- 主程序 -----------------
def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}");  sys.exit(1)

    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    required_cols = ([DATE_COL, NEW_COL, CUM_COL]
                     + list(PRICE_LAG_COLS)
                     + list(P_EVENT_LIST))
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        print(f"⚠️ 缺少必要列: {missing}");  sys.exit(1)

    df = df_raw[[DATE_COL, NEW_COL, CUM_COL]
                + list(PRICE_LAG_COLS)
                + list(P_EVENT_LIST)].copy()
    df = df.fillna(method="ffill").fillna(0)
    df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) &
            (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    
    # 新增：窗口内累积归零
    df[CUM_COL] = df[NEW_COL].cumsum()

    if df.empty:
        print("⚠️ 日期窗口内无数据，退出。");  sys.exit(1)

    df["N_lag"] = df[CUM_COL].shift(1).fillna(0).values

    print(f"\n📊 数据窗口: {START_DATE} ~ {END_DATE},  共 {len(df)} 行")

    param_names    = ["p0", "alpha", "beta", "q0", "m"]
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
                    model_tag = (f"price={price_col}({pt_name}) | "
                                 f"P={p_event_col}({p_form})")
                    print(f"\n→ 拟合 M7.1: {model_tag}")

                    res = fit_M61(df, price_arr, p_event_col, p_form)

                    if res is None:
                        print("  ✖ 拟合失败或不收敛，跳过。")
                        combos_skipped += 1
                        continue

                    combos_done += 1
                    params  = res.x
                    k       = len(params)
                    y_pred  = compute_prediction_M61(
                        df, params, price_arr, p_event_col, p_form)
                    metrics = compute_metrics(df[NEW_COL].values, y_pred, k)

                    # 打印结果
                    for name, val, se, tv, pv in zip(
                            param_names, params, res.se, res.tvals, res.pvals):
                        print(f"  {name:10s} = {val:12.6f}  SE={se:.6f}  "
                              f"t={tv:.3f}  p={pv:.4f}")
                    print(f"  MAD={metrics['MAD']:.4f}  RMSE={metrics['RMSE']:.4f}  "
                          f"R²={metrics['R2']:.4f}  Adj_R²={metrics['Adj_R2']:.4f}")
                    print(f"  MAPE={metrics['MAPE']:.2f}%  WAPE={metrics['WAPE']:.2f}%")
                    print(f"  cond(J'J) = {res.cond:.4e}")

                    row = {
                        "model":       "M7.1",
                        "start":       START_DATE,
                        "end":         END_DATE,
                        "price_col":   price_col,
                        "price_tf":    pt_name,
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