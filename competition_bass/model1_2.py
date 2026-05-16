# 适用weekly,monthly,quarterly数据

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ===================== 参数配置 =====================
CSV_PATH   = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_monthly_timeline_event_all_with_price_event_features.csv"

# 你设置 index 选择区间（例如 weekly）
# BTC weekly: 253-357; ETH weekly: 159-263
# BTC monthly: 59-83; ETH monthly:38-62
# BTC quarterly: 21-29; ETH quarterly:14-22

# 第一列是 index，不用日期筛选，用 index 选区间
START_IDX  = 38
END_IDX    = 62

NEW_COL    = "eth_new_developers"
CUM_COL    = "eth_cum_users"
PRICE_COL  = "eth_price_lag1"    # <-- 选择你要使用的一列（滞后价/ma/vol/trend等）

# btc_price_lag1 ln_btc_price_lag1 btc_return_1p btc_return_2p btc_vol_2p btc_ma_2p btc_trend_2p btc_return_4p btc_vol_4p btc_ma_4p btc_trend_4p btc_return_6p btc_vol_6p btc_ma_6p btc_trend_6p btc_return_8p btc_vol_8p btc_ma_8p btc_trend_8p btc_return_10p btc_vol_10p btc_ma_10p btc_trend_10p

OUTPUT_PNG_NEW = "btc_bass_pricefit_new_week.png"
OUTPUT_PNG_CUM = "btc_bass_pricefit_cum_week.png"
OUTPUT_CSV     = "btc_bass_pricefit_results_week.csv"
# ====================================================


# ============= 数据准备 =============
def load_data():
    df = pd.read_csv(CSV_PATH)

    # 自动识别 index 列，删除它
    if df.columns[0].lower() in ["index", "unnamed: 0"]:
        df = df.drop(df.columns[0], axis=1)

    # 仅保留必要的列
    df = df[[NEW_COL, CUM_COL, PRICE_COL]].reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df


def select_range(df, start_idx, end_idx):
    df = df.iloc[start_idx:end_idx].copy()

    # 价格输入列
    df["price_input"] = df[PRICE_COL].values

    # 使用 N(t-1) 预测 dN(t)
    df["N_lag"] = df[CUM_COL].shift(1)
    df["N_lag"] = df["N_lag"].fillna(df[CUM_COL].iloc[0])

    return df


# ============= Bass 离散模型 =============
def dN_pred(N_lag, p_t, q, m):
    remaining_market = np.maximum(m - N_lag, 0)
    return (p_t + q * (N_lag / m)) * remaining_market


# ============= 标准化处理（价格用） =============
def normalize(x):
    x = np.array(x)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)


def is_return_column(colname):
    return "return" in colname.lower()

def price_identity(price): 
    if is_return_column(PRICE_COL):
        return price
    return normalize(price)

def price_log(price): 
    if is_return_column(PRICE_COL):
        return np.log(np.maximum(price, 1e-8))
    return normalize(np.log(np.maximum(price, 1e-8)))


# ============= constant p ============
def compute_pred_constant_p(df, params):
    p0, q, m = params
    N_lag = df["N_lag"].values
    p_t = np.full(len(df), p0)
    return dN_pred(N_lag, p_t, q, m), p_t


def residuals_constant_p(params, df):
    p0, q, m = params
    if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _ = compute_pred_constant_p(df, params)
    return df[NEW_COL].values - dN_predicted


# ============= price-driven p(t) =============
def compute_prediction(df, params, price_func):
    p0, alpha, q, m = params

    price = df["price_input"].values
    p_input = price_func(price)
    p_t = np.maximum(p0 + alpha * p_input, 0)

    N_lag = df["N_lag"].values
    return dN_pred(N_lag, p_t, q, m), p_t


def residuals(params, df, price_func):
    p0, alpha, q, m = params
    if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
        return np.ones(len(df)) * 1e6
    dN_predicted, _ = compute_prediction(df, params, price_func)
    return df[NEW_COL].values - dN_predicted


# ============= 参数显著性检验 =============
def significance(df, params, compute_pred_func, k):
    eps = 1e-8
    n = len(df)
    y_pred, _ = compute_pred_func(df, params)

    # 数值雅可比矩阵
    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_eps, _ = compute_pred_func(df, params_eps)
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


def print_parameter_table(model_name, params, se, tvals, pvals, names):
    print(f"\n--- {model_name} 参数显著性 ---")
    print(f"{'参数':<10}{'估计值':>12}{'SE':>12}{'t 值':>12}{'p 值':>14}")
    print("---------------------------------------------------")
    for n, v, s, tval, pval in zip(names, params, se, tvals, pvals):
        print(f"{n:<10}{v:>12.6f}{s:>12.6f}{tval:>12.3f}{pval:>14.6e}")
    print("---------------------------------------------------\n")


# ============= 主程序 =============
def main():
    df = load_data()
    df = select_range(df, START_IDX, END_IDX)

    results = []
    valid_models = []

    # ===== baseline =====
    print("\n=== 拟合模型：constant_p ===")
    m_guess = 1.2 * df[CUM_COL].max()

    res0 = least_squares(
        residuals_constant_p,
        x0=[0.01, 0.3, m_guess],
        bounds=([1e-6, 0, 0.5*m_guess], [1, 1, 20*m_guess]),
        args=(df,)
    )

    if res0.success:
        params = res0.x
        dN_pred0, _ = compute_pred_constant_p(df, params)
        cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_pred0)

        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_pred0)**2))
        print(f"✔ baseline：p0={params[0]:.6f}, q={params[1]:.6f}, m={params[2]:.1f}, RMSE={rmse:.3f}")

        se, tvals, pvals = significance(df, params, compute_pred_constant_p, 3)
        print_parameter_table("constant_p", params, se, tvals, pvals, ["p0","q","m"])

        results.append({"model":"constant_p","p0":params[0],"alpha":0,"q":params[1],"m":params[2],"RMSE":rmse})
        df["pred_new_constant_p"] = dN_pred0
        df["pred_cum_constant_p"] = cum_pred
        # constant_p 不加入绘图
        # valid_models.append("constant_p")

    # ===== price-driven =====
    models = {
        "linear_price": price_identity,
        "log_price":    price_log
    }

    for name, func in models.items():
        print(f"\n=== 拟合模型：{name} ===")
        m_guess = 1.2 * df[CUM_COL].max()

        res = least_squares(
            residuals,
            x0=[1e-4, 0.01, 0.01, m_guess],
            bounds=([0,-10,0,0.9*m_guess],[1,10,1,20*m_guess]),
            args=(df, func)
        )

        if not res.success:
            print("⚠️ 优化失败")
            continue

        params = res.x
        dN_predicted, p_t = compute_prediction(df, params, func)
        cum_pred = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)

        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted)**2))

        se, tvals, pvals = significance(df, params, lambda D, P: compute_prediction(D, P, func), 4)

        print(f"✔ {name}：p0={params[0]:.6f}, α={params[1]:.6f}, q={params[2]:.6f}, m={params[3]:.1f}, RMSE={rmse:.3f}")
        print_parameter_table(name, params, se, tvals, pvals, ["p0","alpha","q","m"])

        results.append({"model":name,"p0":params[0],"alpha":params[1],"q":params[2],"m":params[3],"RMSE":rmse})
        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_pred
        valid_models.append(name)

    # 保存
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"✔ 拟合结果已保存到 {OUTPUT_CSV}")

    # ===== 绘图 =====
    plt.figure(figsize=(12,6))
    plt.plot(df.index, df[NEW_COL], label="真实新增", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df.index, df[f"pred_new_{name}"], "--", label=name)
    plt.legend(); plt.title("新增拟合")
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_NEW, dpi=300)

    plt.figure(figsize=(12,6))
    plt.plot(df.index, df[CUM_COL], label="真实累积", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df.index, df[f"pred_cum_{name}"], "--", label=name)
    plt.legend(); plt.title("累积拟合")
    plt.tight_layout(); plt.savefig(OUTPUT_PNG_CUM, dpi=300)

    plt.show()


if __name__ == "__main__":
    main()
