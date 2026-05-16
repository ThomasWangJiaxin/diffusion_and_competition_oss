# 【price+p_event】+q_event
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
DATE_COL = "date"
NEW_COL = "btc_new_developers"
CUM_COL = "btc_cum_users"
PRICE_COL = "btc_price"
P_EVENT_COL = "btc_p_bip_p_event"   # <-- X_E for p(t)
QEVENT_COL = "btc_q_event"    # <-- event for q(t)

START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "eth_bass_pqfit_new_dev_p4q3.png"
OUTPUT_PNG_CUM = "eth_bass_pqfit_cum_dev_p4q3.png"
OUTPUT_CSV = "eth_bass_pqfit_results_p4q3.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    # 注意：这里把 P_EVENT_COL 和 QEVENT_COL 都读进来
    df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, P_EVENT_COL, QEVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

def normalize(x):
    x = np.array(x, dtype=float)
    return (x - np.mean(x)) / (np.std(x) + 1e-8)


# --------- q(t) 函数 (使用 QEVENT_COL) ----------
def compute_q_t(df, q_params, q_form):
    q0, beta = q_params
    # q 使用 QEVENT_COL (btc_q_event)
    event_q = normalize(df[QEVENT_COL].values)
    if q_form == "linear":
        q_t = np.maximum(q0 + beta * event_q, 0)
    elif q_form == "log":
        q_t = np.maximum(q0 + beta * np.log1p(np.maximum(event_q, 0)), 0)
    elif q_form == "exp":
        q_t = q0 * np.exp(beta * event_q)
    else:
        raise ValueError("未知 q_form")
    return q_t


# --------- p(t) 四种模型 (使用 P_EVENT_COL) ----------
def compute_p_t(df, params, price_func, model_type):
    # price_x 来自 PRICE_COL，经 price_func 变换后再标准化
    price_x = normalize(price_func(df[PRICE_COL].values))
    # event_x 特别来自 P_EVENT_COL （btc_p_event）
    event_x = normalize(df[P_EVENT_COL].values)

    if model_type == "additive":  # (1) 线性独立： p0 + α X_P + β X_E
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_x + beta * event_x

    elif model_type == "nonlinear_event":  # (2) 非线性事件驱动： p0 + α X_P + β log( X_E + 1)
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_x + beta * np.log1p(np.maximum(event_x, 0))

    elif model_type == "interaction_linear":  # (3) 交互线性： p0 + α X_P + β X_E + γ (X_P * X_E)
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_x + beta * event_x + gamma * (price_x * event_x)

    elif model_type == "interaction_nonlinear":  # (4) 非线性交互： p0 + α X_P + β log(X_E+1) + γ (X_P * X_E)
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_x + beta * np.log1p(np.maximum(event_x, 0)) + gamma * (price_x * event_x)

    else:
        raise ValueError("未知 p(t) 模型类型")

    return np.maximum(p_t, 0)


# --------- Bass 模型 ----------
def dN_pred(N, p_t, q_t, m):
    remaining = np.maximum(m - N, 0)
    return (p_t + q_t * (N / m)) * remaining


def compute_prediction(df, params, price_func, p_model, q_form):
    # 根据 p_model 决定参数拆分位置
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
        p_params = params[:p_param_count]
        # 接下里依次是 q0, beta_q, m
        q0, beta_q, m = params[p_param_count:p_param_count+3]
    else:
        p_param_count = 4
        p_params = params[:p_param_count]
        q0, beta_q, m = params[p_param_count:p_param_count+3]

    p_t = compute_p_t(df, p_params, price_func, p_model)
    q_t = compute_q_t(df, (q0, beta_q), q_form)
    N = df[CUM_COL].values
    return dN_pred(N, p_t, q_t, m), p_t, q_t


def residuals(params, df, price_func, p_model, q_form):
    # 检查 m, q0 合理性
    if p_model in ["additive", "nonlinear_event"]:
        p_param_count = 3
    else:
        p_param_count = 4
    q0 = params[p_param_count]
    m = params[p_param_count+2]
    if m <= df[CUM_COL].max() or q0 < 0:
        return np.ones(len(df)) * 1e6

    dN_predicted, _, _ = compute_prediction(df, params, price_func, p_model, q_form)
    dN_true = df[NEW_COL].values
    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6
    return dN_true - dN_predicted


# --------- 拟合函数 (返回 res, params, tvals/pvals, param_names) ----------
def fit_bass(df, price_func, p_model, q_form):
    m_guess = 1.2 * df[CUM_COL].max()

    if p_model in ["additive", "nonlinear_event"]:
        # 参数顺序: p0, alpha, beta, q0, beta_q, m
        init = [0.001, 0.01, 0.01, 0.01, 0.01, m_guess]
        bounds = ([0, -10, -10, 0, -10, 0.9*m_guess],
                  [1, 10, 10, 1, 10, 20*m_guess])
        param_names = ["p0", "alpha", "beta", "q0", "beta_q", "m"]
    else:
        # 参数顺序: p0, alpha, beta, gamma, q0, beta_q, m
        init = [0.001, 0.01, 0.01, 0.01, 0.01, 0.01, m_guess]
        bounds = ([0, -10, -10, -10, 0, -10, 0.9*m_guess],
                  [1, 10, 10, 10, 1, 10, 20*m_guess])
        param_names = ["p0", "alpha", "beta", "gamma", "q0", "beta_q", "m"]

    res = least_squares(residuals, init, bounds=bounds,
                        args=(df, price_func, p_model, q_form), method="trf")
    if not res.success:
        return None, None, None, param_names

    params = res.x
    eps = 1e-6
    n = len(df)
    k = len(params)
    y_pred, _, _ = compute_prediction(df, params, price_func, p_model, q_form)

    # 数值雅可比（用于协方差估计）
    J = []
    for i in range(k):
        p_eps = params.copy()
        p_eps[i] += eps
        y_pred_eps, _, _ = compute_prediction(df, p_eps, price_func, p_model, q_form)
        J.append((y_pred_eps - y_pred) / eps)
    J = np.array(J).T

    residuals_vec = df[NEW_COL].values - y_pred
    sigma2 = np.sum(residuals_vec**2) / (n - k)
    try:
        cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
        se = np.sqrt(np.diag(cov))
    except np.linalg.LinAlgError:
        se = np.full(k, np.nan)

    tvals = params / se
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=n-k))

    # attach
    res.se, res.tvals, res.pvals = se, tvals, pvals
    return res, params, (tvals, pvals), param_names


# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)

    # PRICE_FUNCS：传入原始 price 列，compute_p_t 内会 normalize
    PRICE_FUNCS = {
        "linear_price": lambda x: x,
        "log_price": lambda x: np.log(np.maximum(x, 1e-8)),
        "pct_price": lambda x: np.concatenate([[0], np.diff(x) / np.maximum(x[:-1], 1e-8)])
    }

    p_models = ["additive", "nonlinear_event", "interaction_linear", "interaction_nonlinear"]
    q_forms = ["linear", "log", "exp"]

    results = []
    valid_models = []

    plt.figure(figsize=(12,6))
    plt.plot(df[DATE_COL], df[NEW_COL], color='black', label="真实新增", linewidth=2)

    for pf_name, pf_func in PRICE_FUNCS.items():
        for p_model in p_models:
            for q_form in q_forms:
                model_name = f"{p_model} + {pf_name} + {q_form}_q"
                print(f"\n=== 拟合模型: {model_name} ===")
                res, params, (tvals, pvals), param_names = fit_bass(df, pf_func, p_model, q_form)
                if res is None:
                    print(f"⚠️ {model_name} 拟合失败")
                    continue

                dN_pred, p_t, q_t = compute_prediction(df, params, pf_func, p_model, q_form)
                rmse = np.sqrt(np.mean((df[NEW_COL] - dN_pred)**2))
                sse = np.sum((df[NEW_COL] - dN_pred)**2)

                print(f"✅ {model_name} 拟合成功 (RMSE={rmse:.3f})")
                print("--- 参数显著性 ---")
                for n, v, tval, pval in zip(param_names, params, tvals, pvals):
                    print(f"{n:8s}: val={v:.6f}, t={tval:.3f}, p={pval:.3e}")

                # 保存行
                row = {"model": model_name, "SSE": sse, "RMSE": rmse}
                for n, v, tval, pval in zip(param_names, params, tvals, pvals):
                    row[f"{n}"] = v
                    row[f"t_{n}"] = tval
                    row[f"p_{n}"] = pval
                results.append(row)

                # 存预测序列用于画图
                df[f"pred_new_{model_name}"] = dN_pred
                df[f"pred_cum_{model_name}"] = df[CUM_COL].iloc[0] + np.cumsum(dN_pred)
                valid_models.append(model_name)

                plt.plot(df[DATE_COL], dN_pred, '--', label=model_name)

    # 写 CSV（会包含所有参数、t/p）
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 所有拟合结果与显著性检验已保存至 {OUTPUT_CSV}")

    # 新增曲线对比图
    plt.xlabel("日期")
    plt.ylabel("新增开发者数 dN/dt")
    plt.title("Bass 模型：p(t)×q(t) 各形式拟合对比 (12 模型)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_NEW, dpi=300)
    plt.show()

    # 累积曲线对比图
    plt.figure(figsize=(12,6))
    plt.plot(df[DATE_COL], df[CUM_COL], color='black', label="真实累积", linewidth=2)
    for model_name in valid_models:
        plt.plot(df[DATE_COL], df[f"pred_cum_{model_name}"], '--', label=model_name)
    plt.xlabel("日期")
    plt.ylabel("累积开发者数 N(t)")
    plt.title("Bass 模型 累积曲线对比 (12 模型)")
    plt.legend()
    plt.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig(OUTPUT_PNG_CUM, dpi=300)
    plt.show()


if __name__ == "__main__":
    main()