# 修改下面代码：
# （1）bass model拟合应该用N(t-1)
# （2）event col列有btc_event_lag1	btc_event_sum_7	btc_event_mean_7	btc_event_vol_7	btc_event_sum_14	btc_event_mean_14	btc_event_vol_14	btc_event_sum_21	btc_event_mean_21	btc_event_vol_21	btc_event_sum_30	btc_event_mean_30	btc_event_vol_30	
# btc_p_event_lag1	btc_p_event_sum_7	btc_p_event_mean_7	btc_p_event_vol_7	btc_p_event_sum_14	btc_p_event_mean_14	btc_p_event_vol_14	btc_p_event_sum_21	btc_p_event_mean_21	btc_p_event_vol_21	btc_p_event_sum_30	btc_p_event_mean_30	btc_p_event_vol_30	
# btc_q_event_lag1	btc_q_event_sum_7	btc_q_event_mean_7	btc_q_event_vol_7	btc_q_event_sum_14	btc_q_event_mean_14	btc_q_event_vol_14	btc_q_event_sum_21	btc_q_event_mean_21	btc_q_event_vol_21	btc_q_event_sum_30	btc_q_event_mean_30	btc_q_event_vol_30	
# bip_event_lag1	bip_event_sum_7	bip_event_mean_7	bip_event_vol_7	bip_event_sum_14	bip_event_mean_14	bip_event_vol_14	bip_event_sum_21	bip_event_mean_21	bip_event_vol_21	bip_event_sum_30	bip_event_mean_30	bip_event_vol_30	
# bip_p_event_lag1	bip_p_event_sum_7	bip_p_event_mean_7	bip_p_event_vol_7	bip_p_event_sum_14	bip_p_event_mean_14	bip_p_event_vol_14	bip_p_event_sum_21	bip_p_event_mean_21	bip_p_event_vol_21	bip_p_event_sum_30	bip_p_event_mean_30	bip_p_event_vol_30	
# bip_q_event_lag1	bip_q_event_sum_7	bip_q_event_mean_7	bip_q_event_vol_7	bip_q_event_sum_14	bip_q_event_mean_14	bip_q_event_vol_14	bip_q_event_sum_21	bip_q_event_mean_21	bip_q_event_vol_21	bip_q_event_sum_30	bip_q_event_mean_30	bip_q_event_vol_30	
# btc_bip_event_lag1	btc_bip_event_sum_7	btc_bip_event_mean_7	btc_bip_event_vol_7	btc_bip_event_sum_14	btc_bip_event_mean_14	btc_bip_event_vol_14	btc_bip_event_sum_21	btc_bip_event_mean_21	btc_bip_event_vol_21	btc_bip_event_sum_30	btc_bip_event_mean_30	btc_bip_event_vol_30	
# btc_p_bip_p_event_lag1	btc_p_bip_p_event_sum_7	btc_p_bip_p_event_mean_7	btc_p_bip_p_event_vol_7	btc_p_bip_p_event_sum_14	btc_p_bip_p_event_mean_14	btc_p_bip_p_event_vol_14	btc_p_bip_p_event_sum_21	btc_p_bip_p_event_mean_21	btc_p_bip_p_event_vol_21	btc_p_bip_p_event_sum_30	btc_p_bip_p_event_mean_30	btc_p_bip_p_event_vol_30	
# btc_q_bip_q_event_lag1	btc_q_bip_q_event_sum_7	btc_q_bip_q_event_mean_7	btc_q_bip_q_event_vol_7	btc_q_bip_q_event_sum_14	btc_q_bip_q_event_mean_14	btc_q_bip_q_event_vol_14	btc_q_bip_q_event_sum_21	btc_q_bip_q_event_mean_21	btc_q_bip_q_event_vol_21	btc_q_bip_q_event_sum_30	btc_q_bip_q_event_mean_30	btc_q_bip_q_event_vol_30	
# btc_p_bip_event_lag1	btc_p_bip_event_sum_7	btc_p_bip_event_mean_7	btc_p_bip_event_vol_7	btc_p_bip_event_sum_14	btc_p_bip_event_mean_14	btc_p_bip_event_vol_14	btc_p_bip_event_sum_21	btc_p_bip_event_mean_21	btc_p_bip_event_vol_21	btc_p_bip_event_sum_30	btc_p_bip_event_mean_30	btc_p_bip_event_vol_30	
# btc_bip_p_event_lag1	btc_bip_p_event_sum_7	btc_bip_p_event_mean_7	btc_bip_p_event_vol_7	btc_bip_p_event_sum_14	btc_bip_p_event_mean_14	btc_bip_p_event_vol_14	btc_bip_p_event_sum_21	btc_bip_p_event_mean_21	btc_bip_p_event_vol_21	btc_bip_p_event_sum_30	btc_bip_p_event_mean_30	btc_bip_p_event_vol_30	
# btc_q_bip_event_lag1	btc_q_bip_event_sum_7	btc_q_bip_event_mean_7	btc_q_bip_event_vol_7	btc_q_bip_event_sum_14	btc_q_bip_event_mean_14	btc_q_bip_event_vol_14	btc_q_bip_event_sum_21	btc_q_bip_event_mean_21	btc_q_bip_event_vol_21	btc_q_bip_event_sum_30	btc_q_bip_event_mean_30	btc_q_bip_event_vol_30	
# btc_bip_q_event_lag1	btc_bip_q_event_sum_7	btc_bip_q_event_mean_7	btc_bip_q_event_vol_7	btc_bip_q_event_sum_14	btc_bip_q_event_mean_14	btc_bip_q_event_vol_14	btc_bip_q_event_sum_21	btc_bip_q_event_mean_21	btc_bip_q_event_vol_21	btc_bip_q_event_sum_30	btc_bip_q_event_mean_30	btc_bip_q_event_vol_30，
# 这些都表示第t天新增数量的同一行对应的是已经滞后的这些变量如btc_event_lag1，请分别带入bass中 其他功能都不变：
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "eth_new_developers"
CUM_COL = "eth_cum_users"
EVENT_COL = "etc_eip_p_event_sum_7"
START_DATE = "2017-01-01"
END_DATE = "2019-01-01"
OUTPUT_PNG_NEW = "eth_bass_eventfit_new_norm.png"
OUTPUT_PNG_CUM = "eth_bass_eventfit_cum_norm.png"
OUTPUT_CSV = "eth_bass_eventfit_results_t_p_norm.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL, EVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)

    # ✅ 标准化事件变量
    mean_val, std_val = df[EVENT_COL].mean(), df[EVENT_COL].std()
    if std_val > 0:
        df[EVENT_COL] = (df[EVENT_COL] - mean_val) / std_val
    else:
        print("⚠️ 事件变量标准差为0，跳过标准化。")
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

# --------- 模型定义 ----------
def dN_pred(N, p_t, q, m):
    remaining_market = np.maximum(m - N, 0)
    return (p_t + q * (N / m)) * remaining_market

def event_linear(x, beta=None):
    return x

def event_log(x, beta=None):
    return np.log(np.maximum(x + 1, 1e-8))

def event_exp_saturating(x, beta):
    return 1 - np.exp(-beta * x)

def event_exp_explosive(x, beta):
    return np.exp(beta * x)

def compute_prediction(df, params, model_type):
    if "exp" in model_type:
        p0, alpha, beta, q, m = params
    else:
        p0, alpha, q, m = params
        beta = None

    x = df[EVENT_COL].values
    if model_type == "linear_event":
        p_input = event_linear(x)
    elif model_type == "log_event":
        p_input = event_log(x)
    elif model_type == "exp_saturating_event":
        p_input = event_exp_saturating(x, beta)
    elif model_type == "exp_explosive_event":
        p_input = event_exp_explosive(x, beta)
    else:
        raise ValueError("Unknown model type")

    p_t = np.maximum(p0 + alpha * p_input, 0)
    N = df[CUM_COL].values
    return dN_pred(N, p_t, q, m), p_t

# --------- 残差函数 ----------
def residuals(params, df, model_type):
    if "exp" in model_type:
        p0, alpha, beta, q, m = params
        if m <= df[CUM_COL].max() or q < 0 or p0 < 0 or beta < 0:
            return np.ones(len(df)) * 1e6
    else:
        p0, alpha, q, m = params
        if m <= df[CUM_COL].max() or q < 0 or p0 < 0:
            return np.ones(len(df)) * 1e6

    dN_predicted, _ = compute_prediction(df, params, model_type)
    dN_true = df[NEW_COL].values
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return dN_true - dN_predicted

# --------- 参数拟合 + 显著性检验 ----------
def fit_bass(df, model_type):
    m_guess = 1.2 * df[CUM_COL].max()
    if "exp" in model_type:
        init = [1e-4, 0.01, 0.1, 0.01, m_guess]
        bounds = ([0, -10, 0, 0, 0.5*m_guess], [1, 10, 10, 1, 20*m_guess])
    else:
        init = [1e-4, 0.01, 0.01, m_guess]
        bounds = ([0, -10, 0, 0.5*m_guess], [1, 10, 1, 20*m_guess])

    res = least_squares(residuals, init, bounds=bounds, args=(df, model_type), method="trf")
    if not res.success:
        return res, None
    params = res.x

    eps = 1e-6
    n = len(df)
    k = len(params)
    y_pred, _ = compute_prediction(df, params, model_type)

    # 雅可比矩阵
    J = []
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_pred_eps, _ = compute_prediction(df, params_eps, model_type)
        grad_i = (y_pred_eps - y_pred) / eps
        J.append(grad_i)
    J = np.array(J).T

    cond = np.linalg.cond(J.T @ J)
    print(f"⚙️ Hessian 条件数 cond={cond:.2e}")
    y_true = df[NEW_COL].values
    residuals_vec = y_true - y_pred
    sigma2 = np.sum(residuals_vec**2) / (n - k)

    try:
        cov = sigma2 * np.linalg.inv(J.T @ J + 1e-6 * np.eye(J.shape[1]))
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        cov = np.full((J.shape[1], J.shape[1]), np.nan)
        se = np.full(J.shape[1], np.nan)

    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n - k))
    names = ["p0", "alpha", "beta", "q", "m"] if "exp" in model_type else ["p0", "alpha", "q", "m"]
    print("\n--- 参数显著性检验 ---")
    for name, val, se_i, t_i, p_i in zip(names, params, se, tvals, pvals):
        print(f"{name:5s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

    res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
    return res

# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)
    models = ["linear_event", "log_event", "exp_saturating_event", "exp_explosive_event"]
    results = []
    valid_models = []

    for name in models:
        print(f"\n=== 拟合模型：{name} ===")
        res = fit_bass(df, name)
        if (not res.success) or np.any(np.isnan(res.x)):
            print(f"⚠️ 模型 {name} 优化失败或参数异常，跳过。")
            continue

        dN_predicted, p_t = compute_prediction(df, res.x, name)
        rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
        sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)

        print(f"✅ 拟合成功：{name}, RMSE={rmse:.3f}")
        cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)
        df[f"pred_new_{name}"] = dN_predicted
        df[f"pred_cum_{name}"] = cum_predicted
        results.append({"model": name, **{f"param_{i}": val for i, val in enumerate(res.x)}, "SSE": sse, "RMSE": rmse})
        valid_models.append(name)

    if results:
        pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ 拟合结果保存至 {OUTPUT_CSV}")
    else:
        print("❌ 无有效模型结果。")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增值", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_new_{name}"], "--", label=f"预测新增 ({name})")
    plt.legend(); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    print(f"📊 新增图保存至 {OUTPUT_PNG_NEW}")

    plt.figure(figsize=(12, 6))
    plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
    for name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{name}"], "--", label=f"预测累积 ({name})")
    plt.legend(); plt.grid(True, linestyle='--'); plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    print(f"📊 累积图保存至 {OUTPUT_PNG_CUM}")

if __name__ == "__main__":
    main()