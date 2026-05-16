# price+p_event + m(t)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bass 模型扩展：p(t) + m(t) 可选形式（constant / add / mul / exp）
- 支持不同参数结构：
    * m_form == "constant": params 不包含 beta_m，结构与原模型一致（m0 在最后）
    * m_form in ["add","mul","exp"]: params 最后包含 beta_m（用于 m(t)）
- 支持带/不带交互项的 p(t) 模型（与你原始脚本一致）
- 输出：
    * OUTPUT_CSV (参数与拟合指标)
    * 每种模型的 pred_new_... 与 pred_cum_... 写入 df 并绘图
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import matplotlib.pyplot as plt
import os

# ============= 参数配置 =============
CSV_PATH = "/home/lab0/survival_diffusion_github/competition_bass/BTC_BCH_ETHdev.csv"
DATE_COL = "date"
NEW_COL = "eth_new_developers"
CUM_COL = "eth_cum_users"
PRICE_COL = "eth_price"
EVENT_COL = "eth_p_eip_event"

START_DATE = "2017-01-01"
END_DATE = "2019-01-01"

OUTPUT_PNG_NEW = "/home/lab0/survival_diffusion_github/competition_bass/eth_bass_price_eventfit_new.png"
OUTPUT_PNG_CUM = "/home/lab0/survival_diffusion_github/competition_bass/eth_bass_price_eventfit_cum.png"
OUTPUT_CSV = "/home/lab0/survival_diffusion_github/competition_bass/btc_bass_price_eventfit_results.csv"
# ===================================

# --------- 数据准备 ----------
def load_data():
    df = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    df = df[[DATE_COL, NEW_COL, CUM_COL, PRICE_COL, EVENT_COL]].sort_values(DATE_COL).reset_index(drop=True)
    df = df.fillna(method="ffill").fillna(0)

    # 全局标准化 price 与 event
    for col in [PRICE_COL, EVENT_COL]:
        mean_val, std_val = df[col].mean(), df[col].std()
        if std_val > 0:
            df[col] = (df[col] - mean_val) / std_val
        else:
            print(f"⚠️ 列 {col} 标准差为0，跳过标准化。")

    # log 变量及交互项（用于一些 p(t) 变体）
    df["log_price"] = np.log1p(np.maximum(df[PRICE_COL], 0))
    df["log_event"] = np.log1p(np.maximum(df[EVENT_COL], 0))
    df["interaction"] = df[PRICE_COL] * df[EVENT_COL]
    df["log_interaction"] = df["log_price"] * df["log_event"]
    return df

def select_date(df, start, end):
    mask = (df[DATE_COL] >= pd.to_datetime(start)) & (df[DATE_COL] <= pd.to_datetime(end))
    return df.loc[mask].copy()

# --------- Bass 动力学 ----------
def dN_pred(N, p_t, q, m_t):
    """
    N: 当前累积（向量）
    p_t: 潜在创新率（向量）
    q: 口碑系数（标量）
    m_t: 市场容量（向量或标量）
    返回 dN_pred 向量
    """
    remaining = np.maximum(m_t - N, 0)
    # 防止除以零；当 m_t==0 时直接返回0
    safe_m = np.where(m_t <= 0, 1e-9, m_t)
    return (p_t + q * (N / safe_m)) * remaining

# --------- p(t) 计算（与原脚本兼容）----------
def compute_p_t(df, params, model_type):
    # p 相关的参数始终在 params 前部，indexing 需要小心
    P = df[PRICE_COL].values
    E = df[EVENT_COL].values
    LP = df["log_price"].values
    LE = df["log_event"].values
    I = df["interaction"].values
    LI = df["log_interaction"].values

    # 根据 model_type 抽取前若干参数（不依赖于 m_form）
    if model_type == "linear_add":
        # params: [p0, alpha, beta, q, m0]  or  [p0, alpha, beta, q, m0, beta_m]
        p0, alpha, beta = params[0], params[1], params[2]
        p_t = np.maximum(p0 + alpha * P + beta * E, 0)

    elif model_type == "log_event":
        p0, alpha, beta = params[0], params[1], params[2]
        p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)), 0)

    elif model_type == "linear_interact":
        # params: [p0, alpha, beta, gamma, q, ...]
        p0, alpha, beta, gamma = params[0], params[1], params[2], params[3]
        p_t = np.maximum(p0 + alpha * P + beta * E + gamma * I, 0)

    elif model_type == "log_interact":
        p0, alpha, beta, gamma = params[0], params[1], params[2], params[3]
        p_t = np.maximum(p0 + alpha * P + beta * np.log1p(np.maximum(E, 0)) + gamma * I, 0)

    elif model_type == "logprice_add":
        p0, alpha, beta = params[0], params[1], params[2]
        p_t = np.maximum(p0 + alpha * LP + beta * E, 0)

    elif model_type == "logprice_logevent":
        p0, alpha, beta = params[0], params[1], params[2]
        p_t = np.maximum(p0 + alpha * LP + beta * LE, 0)

    elif model_type == "logprice_loginteract":
        p0, alpha, beta, gamma = params[0], params[1], params[2], params[3]
        p_t = np.maximum(p0 + alpha * LP + beta * LE + gamma * LI, 0)

    else:
        raise ValueError(f"未知 model_type: {model_type}")

    return p_t

# --------- m(t) 计算 ----------
def compute_m_t(df, m0, beta_m, m_form="constant"):
    P = df[PRICE_COL].values
    if m_form == "constant":
        return np.full(len(df), m0)
    elif m_form == "add":
        return np.maximum(m0 + (beta_m if beta_m is not None else 0.0) * P, 1e-6)
    elif m_form == "mul":
        return np.maximum(m0 * (1.0 + (beta_m if beta_m is not None else 0.0) * P), 1e-6)
    elif m_form == "exp":
        return np.maximum(m0 * np.exp((beta_m if beta_m is not None else 0.0) * P), 1e-6)
    else:
        raise ValueError(f"未知 m_form: {m_form}")

# --------- 帮助：从 params 提取 q, m0, beta_m（根据 model_type 与 m_form） ----------
def extract_market_params(params, model_type, m_form):
    """
    返回 (q, m0, beta_m)
    beta_m 为 None 表示未在参数向量中包含（m_form == "constant"）
    """
    if "interact" in model_type:
        # param order:
        # constant: [p0, alpha, beta, gamma, q, m0]
        # with beta_m: [p0, alpha, beta, gamma, q, m0, beta_m]
        if m_form == "constant":
            q = params[-2]
            m0 = params[-1]
            beta_m = None
        else:
            q = params[-3]
            m0 = params[-2]
            beta_m = params[-1]
    else:
        # non-interact:
        # constant: [p0, alpha, beta, q, m0]
        # with beta_m: [p0, alpha, beta, q, m0, beta_m]
        if m_form == "constant":
            q = params[-2]
            m0 = params[-1]
            beta_m = None
        else:
            q = params[-3]
            m0 = params[-2]
            beta_m = params[-1]
    return float(q), float(m0), (None if beta_m is None else float(beta_m))

# --------- 预测总流程 ----------
def compute_prediction(df, params, model_type, m_form="constant"):
    """
    返回：dN_predicted (向量), p_t (向量), m_t (向量)
    参数向量长度视 model_type 与 m_form 而定（见上文约定）
    """
    p_t = compute_p_t(df, params, model_type)
    q, m0, beta_m = extract_market_params(params, model_type, m_form)
    m_t = compute_m_t(df, m0, beta_m, m_form)
    N = df[CUM_COL].values
    dN = dN_pred(N, p_t, q, m_t)
    return dN, p_t, m_t

# --------- 残差函数 ----------
def residuals(params, df, model_type, m_form):
    dN_predicted, _, _ = compute_prediction(df, params, model_type, m_form)
    dN_true = df[NEW_COL].values

    # 检查基本参数合法性：q>=0, p0>=0, m0 > current max cum
    # 获取 q, m0
    try:
        q, m0, beta_m = extract_market_params(params, model_type, m_form)
    except Exception:
        return np.ones(len(df)) * 1e6

    # 简单参数约束（违反则返回大残差）
    if q < 0 or params[0] < 0:
        return np.ones(len(df)) * 1e6
    # 要求 m0 至少大于当前最大累积的一定比例（例如 > max(N) 的 0.9）
    if m0 <= df[CUM_COL].max() * 0.9:
        return np.ones(len(df)) * 1e6

    if np.any(np.isnan(dN_predicted)) or np.allclose(dN_predicted, 0):
        return np.ones(len(df)) * 1e6

    return dN_true - dN_predicted

# --------- 拟合 + 显著性检验 ----------
def fit_bass(df, model_type, m_form):
    # 根据 model_type 与 m_form 构造初始值与 bounds（参数顺序须严格对应 compute_p_t + 市场参数）
    max_cum = df[CUM_COL].max()
    # 模型前缀参数数量（p 部分）
    if "interact" in model_type:
        p_len = 4  # p0, alpha, beta, gamma
    else:
        p_len = 3  # p0, alpha, beta

    # 构造 init 和 bounds
    if m_form == "constant":
        # params: p_part (3 or 4) + [q, m0]
        init = [1e-4, 0.01, 0.01] if p_len == 3 else [1e-4, 0.01, 0.01, 0.01]
        init += [0.01, 1.2 * max_cum]
        lower = [-np.inf] * p_len + [0.0, 0.9 * max_cum]
        upper = [np.inf] * p_len + [10.0, 20 * max_cum]
    else:
        # params: p_part + [q, m0, beta_m]
        init = [1e-4, 0.01, 0.01] if p_len == 3 else [1e-4, 0.01, 0.01, 0.01]
        init += [0.01, 1.2 * max_cum, 0.01]
        lower = [-np.inf] * p_len + [0.0, 0.5 * max_cum, -5.0]
        upper = [np.inf] * p_len + [10.0, 20 * max_cum, 5.0]

    # 转为 numpy array
    init = np.array(init, dtype=float)
    bounds = (np.array(lower, dtype=float), np.array(upper, dtype=float))

    # 运行 least_squares
    res = least_squares(residuals, init, bounds=bounds, args=(df, model_type, m_form), method="trf", xtol=1e-8, ftol=1e-8)
    # 如果失败直接返回
    if not res.success:
        return res, None

    # 计算拟合统计（基于数值雅可比）
    params = res.x.copy()
    n = len(df)
    k = len(params)

    # 预测与雅可比估计（通过微小扰动算数值导数）
    y_pred, _, _ = compute_prediction(df, params, model_type, m_form)

    eps = 1e-6
    J = np.zeros((n, k))
    for i in range(k):
        params_eps = params.copy()
        params_eps[i] += eps
        y_pred_eps, _, _ = compute_prediction(df, params_eps, model_type, m_form)
        J[:, i] = (y_pred_eps - y_pred) / eps

    # 条件数
    try:
        cond = np.linalg.cond(J.T @ J)
    except Exception:
        cond = np.nan
    print(f"⚙️ Hessian 条件数 cond={cond:.2e}")

    y_true = df[NEW_COL].values
    resid_vec = y_true - y_pred
    sigma2 = np.sum(resid_vec ** 2) / max(1, (n - k))

    try:
        cov = sigma2 * np.linalg.inv(J.T @ J + 1e-9 * np.eye(J.shape[1]))
        se = np.sqrt(np.abs(np.diag(cov)))
    except Exception:
        se = np.full(k, np.nan)

    tvals = params / (se + 1e-12)
    pvals = 2 * (1 - t.cdf(np.abs(tvals), df=max(1, n - k)))

    res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond

    # 参数名称映射（便于输出）
    names_dict = {
        "linear_add": {
            "constant": ["p0", "alpha(price)", "beta(event)", "q", "m0"],
            "other":    ["p0", "alpha(price)", "beta(event)", "q", "m0", "beta_m"]
        },
        "log_event": {
            "constant": ["p0", "alpha(price)", "beta(logE)", "q", "m0"],
            "other":    ["p0", "alpha(price)", "beta(logE)", "q", "m0", "beta_m"]
        },
        "linear_interact": {
            "constant": ["p0", "alpha(price)", "beta(event)", "gamma(inter)", "q", "m0"],
            "other":    ["p0", "alpha(price)", "beta(event)", "gamma(inter)", "q", "m0", "beta_m"]
        },
        "log_interact": {
            "constant": ["p0", "alpha(price)", "beta(logE)", "gamma(inter)", "q", "m0"],
            "other":    ["p0", "alpha(price)", "beta(logE)", "gamma(inter)", "q", "m0", "beta_m"]
        },
        "logprice_add": {
            "constant": ["p0", "alpha(logP)", "beta(event)", "q", "m0"],
            "other":    ["p0", "alpha(logP)", "beta(event)", "q", "m0", "beta_m"]
        },
        "logprice_logevent": {
            "constant": ["p0", "alpha(logP)", "beta(logE)", "q", "m0"],
            "other":    ["p0", "alpha(logP)", "beta(logE)", "q", "m0", "beta_m"]
        },
        "logprice_loginteract": {
            "constant": ["p0", "alpha(logP)", "beta(logE)", "gamma(logP*logE)", "q", "m0"],
            "other":    ["p0", "alpha(logP)", "beta(logE)", "gamma(logP*logE)", "q", "m0", "beta_m"]
        }
    }

    key = "constant" if m_form == "constant" else "other"
    param_names = names_dict.get(model_type, {}).get(key, [f"param_{i}" for i in range(k)])

    print("\n--- 参数与显著性 ---")
    for nm, val, se_i, t_i, p_i in zip(param_names, params, se, tvals, pvals):
        print(f"{nm:20s} : {val:12.6f} | SE={se_i:10.6f} | t={t_i:8.3f} | p={p_i:.6e}")

    return res, param_names

# --------- 主程序 ----------
def main():
    df = load_data()
    df = select_date(df, START_DATE, END_DATE)
    print(f"数据长度: {len(df)} | 时间区间: {START_DATE} ~ {END_DATE}")

    models = [
        "linear_add", "log_event", "linear_interact", "log_interact",
        "logprice_add", "logprice_logevent", "logprice_loginteract"
    ]
    m_forms = ["constant", "add", "mul", "exp"]

    results = []
    valid_models = []

    for model_type in models:
        for m_form in m_forms:
            model_label = f"{model_type}__m_{m_form}"
            print(f"\n=== 拟合：{model_label} ===")
            try:
                res, param_names = fit_bass(df, model_type, m_form)
            except Exception as e:
                print(f"❌ 拟合异常: {e}")
                continue

            if (res is None) or (not res.success) or np.any(np.isnan(res.x)):
                print(f"⚠️ {model_label} 优化失败或参数异常，跳过。")
                continue

            # 预测并计算指标
            dN_predicted, p_t, m_t = compute_prediction(df, res.x, model_type, m_form)
            rmse = np.sqrt(np.mean((df[NEW_COL].values - dN_predicted) ** 2))
            sse = np.sum((df[NEW_COL].values - dN_predicted) ** 2)
            cum_predicted = df[CUM_COL].iloc[0] + np.cumsum(dN_predicted)

            # 写回 df（可能覆盖多个模型的列）
            df[f"pred_new_{model_label}"] = dN_predicted
            df[f"pred_cum_{model_label}"] = cum_predicted
            df[f"p_t_{model_label}"] = p_t
            df[f"m_t_{model_label}"] = m_t

            # 收集参数与统计量
            entry = {"model": model_label, "SSE": sse, "RMSE": rmse}
            for i, nm in enumerate(param_names):
                entry[nm] = res.x[i]
                entry[f"{nm}_SE"] = res.se[i] if hasattr(res, "se") else np.nan
                entry[f"{nm}_t"] = res.tvals[i] if hasattr(res, "tvals") else np.nan
                entry[f"{nm}_p"] = res.pvals[i] if hasattr(res, "pvals") else np.nan
            entry["cond"] = getattr(res, "cond", np.nan)

            results.append(entry)
            valid_models.append(model_label)
            print(f"✅ 拟合成功: {model_label} | RMSE={rmse:.4f}")

    # 保存结果 CSV
    if len(results) > 0:
        results_df = pd.DataFrame(results)
        results_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ 所有模型参数与统计量已保存至: {OUTPUT_CSV}")
    else:
        print("❌ 没有有效模型结果，退出。")
        return

    # 绘图：新增量与累积
    if len(valid_models) > 0:
        plt.figure(figsize=(12, 6))
        plt.plot(df[DATE_COL], df[NEW_COL], label="真实新增", color="black", linewidth=2)
        for label in valid_models:
            plt.plot(df[DATE_COL], df[f"pred_new_{label}"], "--", label=f"预测新增 ({label})")
        plt.legend(); plt.tight_layout()
        plt.savefig(OUTPUT_PNG_NEW, dpi=300)
        print(f"📊 新增图保存至: {OUTPUT_PNG_NEW}")

        plt.figure(figsize=(12, 6))
        plt.plot(df[DATE_COL], df[CUM_COL], label="真实累积 N(t)", color="black", linewidth=2)
        for label in valid_models:
            plt.plot(df[DATE_COL], df[f"pred_cum_{label}"], "--", label=f"预测累积 ({label})")
        plt.legend(); plt.grid(True, linestyle='--'); plt.tight_layout()
        plt.savefig(OUTPUT_PNG_CUM, dpi=300)
        print(f"📊 累积图保存至: {OUTPUT_PNG_CUM}")
    else:
        print("没有可绘制的模型。")

    # 可选：保存带预测的完整 df（去掉巨量列名时注意文件大小）
    out_df_path = os.path.splitext(OUTPUT_CSV)[0] + "_with_preds.csv"
    try:
        df.to_csv(out_df_path, index=False)
        print(f"✅ 带预测结果的完整数据保存至: {out_df_path}")
    except Exception as e:
        print(f"⚠️ 保存带预测数据时出错: {e}")

if __name__ == "__main__":
    main()
