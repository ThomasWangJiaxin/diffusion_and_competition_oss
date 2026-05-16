# 价格放入q(t)

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ============= 参数配置 =============
CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL   = "date"
NEW_COL    = "eth_new_developers"
CUM_COL    = "eth_cum_users"
PRICE_COL  = "eth_ma_7d"   # <-- 已经是滞后的价格列
START_DATE = "2017-01-01"
END_DATE   = "2019-01-01"

OUTPUT_PNG_NEW = "btc_bass_pricefit_new.png"
OUTPUT_PNG_CUM = "btc_bass_pricefit_cum.png"
OUTPUT_CSV     = "btc_bass_pricefit_results.csv"
# ===================================


# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df


def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    df = df.loc[mask].copy()

    # 用户输入的价格列直接使用
    df["price_input"] = df[PRICE_COL].values

    # ★ 使用 N(t-1) 预测 dN(t)
    df["N_lag"] = df[CUM_COL].shift(1)
    df["N_lag"] = df["N_lag"].fillna(df[CUM_COL].iloc[0])

    return df


# --------- Bass 离散模型（新版：使用 N_lag） ----------
def dN_pred(N_lag, p, q, m):
    remaining_market = np.maximum(m - N_lag, 0)
    return (p + q * (N_lag / m)) * remaining_market


# --------- 数据标准化 ----------
def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)


# --------- q 与价格挂钩 ----------
def compute_prediction_price_q(df, params, price_func):
    p0, alpha, m = params
    price = df["price_input"].values
    q_t = np.maximum(alpha * price_func(price), 0)  # q 随价格变化
    N_lag = df["N_lag"].values
    dN_predicted = dN_pred(N_lag, p0, q_t, m)
    return dN_predicted, q_t


def residuals_price_q(params, df, price_func):
    p0, alpha, m = params
    if m <= df[CUM_COL].max() or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _ = compute_prediction_price_q(df, params, price_func)
    return df[NEW_COL].values - dN_predicted


# --------- price 变换 ----------
def price_identity(price): 
    return normalize(price)

def price_log(price): 
    return normalize(np.log(np.maximum(price, 1e-8)))


# --------- 参数显著性检验 ----------
def significance(df, params, compute_func, k, price_func):
    eps = 1e-8
    n = len(df)
    y_pred, _ = compute_func(df, params, price_func)

    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_eps, _ = compute_func(df, params_eps, price_func)
        J.append((y_eps - y_pred) / eps)
    J = np.array(J).T

    y_true = df[NEW_COL].values
    residuals_vec = y_true - y_pred
    sigma2 = np.sum(residuals_vec**2) / (n - k)

    try:
        cov = sigma2 * np.linalg.inv(J.T @ J)
        se = np.sqrt(np.diag(cov))
    except:
        se = np.full(k, np.nan)

    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))

    return se, tvals, pvals


def print_parameter_table(model_name, params, se, tvals, pvals, param_names):
    print(f"\n--- {model_name} 参数显著性 ---")
    print(f"{'参数':<10}{'估计值':>12}{'SE':>12}{'t 值':>12}{'p 值':>14}")
    print("---------------------------------------------------")
    for name, val, s, tval, pval in zip(param_names, params, se, tvals, pvals):
        print(f"{name:<10}{val:>12.6f}{s:>12.6f}{tval:>12.3f}{pval:>14.6e}")
    print("---------------------------------------------------\n")


# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    results = []

    # ================= price-driven q ==================
    models = {
        "linear_price": price_identity,
        "log_price": price_log
    }

    for name, func in models.items():
        print(f"\n=== 拟合模型：{name} ===")
        m_guess = 1.2 * df[CUM_COL].max()

        res = least_squares(residuals_price_q,
                            x0=[0.01, 0.01, m_guess],  # p0, alpha, m
                            bounds=([1e-6, -10, 0.9*m_guess],
                                    [1, 10, 20*m_guess]),
                            args=(df, func),
                            method="trf")

        if not res.success:
            print("⚠️ 优化失败")
            continue

        params = res.x
        p0, alpha, m = params

        dN_predicted, q_t = compute_prediction_price_q(df, params, func)
        cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted)**2))

        se, tvals, pvals = significance(df, params, compute_prediction_price_q, 3, func)
        print(f"✔ {name}：p0={p0:.6f}, α={alpha:.6f}, m={m:.1f}, RMSE={rmse:.3f}")
        print_parameter_table(name, params, se, tvals, pvals, ["p0", "alpha", "m"])

        results.append({
            "model": name,
            "p0": p0,
            "alpha": alpha,
            "m": m,
            "RMSE": rmse
        })

        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_pred

    # 保存结果
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✔ 拟合结果已保存至：{OUTPUT_CSV}")

    # ---------- 绘图 ----------
    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black", linewidth=2)
    for name in models.keys():
        plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=name)
    plt.legend(); plt.title("每日新增")
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_NEW, dpi=300)

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积", color="black", linewidth=2)
    for name in models.keys():
        plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=name)
    plt.legend(); plt.title("累积开发者")
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_CUM, dpi=300)

    plt.show()


if __name__ == "__main__":
    main()
