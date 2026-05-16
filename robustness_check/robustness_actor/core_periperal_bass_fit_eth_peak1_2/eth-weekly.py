"""
ETH 稳健性检验 —— Core / Peripheral 开发者分类版本（周度）
===========================================================
对 Core 和 Peripheral 开发者分别拟合完整 Bass 竞争扩散模型。

数据来源:
  - 开发者新增序列 : eth_weekly_new_core_peripheral.csv
  - 事件/价格特征  : ETHdev_weekly_timeline_event_all_with_price_event_features.csv
  - 迁移数据 (日度): eth_daily_migration_core_peripheral_wide.csv（在脚本内聚合为周度）

使用方法:
  ACTOR = "Core"        # 切换 "Core" | "Peripheral"
  PEAK  = "peak2"       # 切换 "peak1" | "peak2"
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t
import math
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl

mpl.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'axes.titlesize': 14, 'axes.labelsize': 13,
    'xtick.labelsize': 12, 'ytick.labelsize': 12,
    'legend.fontsize': 12,
})

# ===================================================================
# ===== 配置区：修改此处切换 actor 类型 / peak 窗口 =====
# ===================================================================
ACTOR = "Core"        # "Core" | "Peripheral"
PEAK  = "peak2"       # "peak1" | "peak2"

# 峰值窗口定义（weekly，同主模型）
PEAK_WINDOWS = {
    "peak1": ("2017-01-02", "2018-12-31"),
    "peak2": ("2020-09-28", "2023-01-02"),
}
START_DATE, END_DATE = PEAK_WINDOWS[PEAK]

# ── 路径 ──────────────────────────────────────────────────────────
BASE = "/home/lab0/survival_diffusion_github"

ACTOR_CSV_PATH = f"{BASE}/robustness_check/robustness_actor/eth_weekly_new_core_peripheral.csv"
FEATURE_CSV    = f"{BASE}/competition_bass/ETHdev_weekly_timeline_event_all_with_price_event_features.csv"
DAILY_MIG_PATH = f"{BASE}/robustness_check/robustness_actor/eth_daily_migration_core_peripheral_wide.csv"

OUTPUT_CSV = (f"{BASE}/robustness_check/robustness_actor/core_periperal_bass_fit_eth_peak1_2/"
              f"eth_{PEAK}_{ACTOR.lower()}_weekly_grid_results.csv")
OUTPUT_PNG = (f"{BASE}/robustness_check/robustness_actor/core_periperal_bass_fit_eth_peak1_2/"
              f"eth_{PEAK}_{ACTOR.lower()}_weekly_best_fit.png")
# ===================================================================

DATE_COL = "date"

# 根据 actor 选择列名
if ACTOR == "Core":
    NEW_COL = "Core"
    CUM_COL = "cum_Core"
    MIG_IN_PREFIX  = "Core_inflow_"
    MIG_OUT_PREFIX = "Core_outflow_"
else:
    NEW_COL = "Peripheral"
    CUM_COL = "cum_Peripheral"
    MIG_IN_PREFIX  = "Peripheral_inflow_"
    MIG_OUT_PREFIX = "Peripheral_outflow_"

# ── 事件 / 价格列表（与主模型一致）──────────────────────────────
P_EVENT_LIST = [
    "eth_p_event_lag1", "eth_p_event_sum_2", "eth_p_event_sum_4",
    "eth_p_event_sum_6", "eth_p_event_sum_8", "eth_p_event_sum_10",
]
Q_EVENT_LIST = [
    "eth_q_event_lag1", "eth_q_event_sum_2", "eth_q_event_sum_4",
    "eth_q_event_sum_6", "eth_q_event_sum_8", "eth_q_event_sum_10",
]
PRICE_LAG_COLS = [
    "eth_price_lag1", "eth_ma_2p", "eth_ma_4p",
    "eth_ma_6p", "eth_ma_8p", "eth_ma_10p",
]

TARGET_PRICE_TF = "log"
TARGET_P_MODEL  = "additive"
TARGET_Q_FORM   = "linear"

# ── 竞争项目列表（按 peak 区分）────────────────────────────────
COMPETITORS_PEAK = {
    "peak1": [
        "BTC", "Solana", "Cosmos", "TRON",
    ],
    "peak2": [
        "BTC", "Solana", "Cosmos", "BNBChain", "Erigon", "Optimism",
        "TRON", "Aptos", "Sui", "Besu", "Nethermind", "Avalanche",
        "Polygon", "Near", "FLOW", "Harmony", "Reth",
        "EthereumPOW"
    ],
}
COMPETITORS = COMPETITORS_PEAK[PEAK]

# 每个竞争项目在日度迁移 CSV 中的列名尾缀
COMP_COL_MAP = {
    # peak1 & peak2 共有
    "BTC":         "BTC",
    "Solana":      "Solana",
    "Cosmos":      "Cosmos",
    "TRON":        "TRON",
    # peak2 专属
    "BNBChain":    "BNB",          # ← BNBChain → BNB
    "Erigon":      "Erigon",
    "Optimism":    "Optimism",
    "Aptos":       "APTOS",        # ← Aptos → APTOS
    "Sui":         "SUI",          # ← Sui → SUI
    "Besu":        "BESU",         # ← Besu → BESU
    "Nethermind":  "Nethermind",
    "Avalanche":   "Avalanche",
    "Polygon":     "Polygon",
    # "Arweave":     "Arweave",      # ⚠️ 见下方说明
    "Near":        "NEAR",         # ← Near → NEAR
    "FLOW":        "FLOW",
    "Harmony":     "Harmony",
    "Reth":        "RETH",         # ← Reth → RETH
    "EthereumPOW": "Ethereumpow",
    # "THETA":       "THETA",        # ⚠️ 见下方说明
}


# ─────────────────────────────────────────────────────────────────
# 评估指标
# ─────────────────────────────────────────────────────────────────
def compute_metrics(y_true, y_pred, k):
    y_true, y_pred = np.array(y_true, float), np.array(y_pred, float)
    n      = len(y_true)
    resid  = y_true - y_pred
    sse    = np.sum(resid ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2     = 1 - sse / ss_tot if ss_tot > 0 else np.nan
    adj_r2 = (1 - (1 - r2) * (n - 1) / (n - k - 1)
              if (n - k - 1 > 0 and ss_tot > 0) else np.nan)
    mask  = y_true != 0
    mape  = np.mean(np.abs(resid[mask] / y_true[mask])) * 100 if mask.sum() > 0 else np.nan
    denom = np.sum(np.abs(y_true))
    wape  = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan
    return {
        "MAD": np.mean(np.abs(resid)),
        "SSE": sse, "MSE": sse / n,
        "RMSE": math.sqrt(sse / n),
        "R2": r2, "Adj_R2": adj_r2,
        "MAPE": mape, "WAPE": wape,
    }


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────
def normalize(x):
    x   = np.array(x, float)
    std = np.std(x)
    return (x - np.mean(x)) / (std + 1e-12) if std > 0 else x - np.mean(x)

def compute_p_t(df, params, price_array, p_model, p_event_col):
    ev = normalize(df[p_event_col].values)
    p0, alpha, beta = params[:3]
    return np.maximum(p0 + alpha * price_array + beta * ev, 0)

def compute_q_t(event_arr, q0, beta_q, q_form):
    ev = normalize(event_arr)
    return np.maximum(q0 + beta_q * ev, 0)

def get_param_indices():
    """参数布局: [p0, alpha, beta_p, q0, beta_q, γ_in×J, δ_out×J, m]"""
    n = len(COMPETITORS)
    return dict(p_end=3, q_start=3, q_end=5,
                gi_start=5, gi_end=5+n,
                do_start=5+n, do_end=5+2*n,
                m_idx=5+2*n, total=5+2*n+1)

def dN_prediction(df, params, price_array, p_event_col, q_event_col,
                  inflow_dict, outflow_dict):
    idx = get_param_indices()
    p0, alpha, beta_p = params[0], params[1], params[2]
    q0, beta_q        = params[idx['q_start']], params[idx['q_start']+1]
    gamma_in  = params[idx['gi_start']:idx['gi_end']]
    delta_out = params[idx['do_start']:idx['do_end']]
    m         = params[idx['m_idx']]

    N_lag     = df["N_lag"].values
    remaining = np.maximum(m - N_lag, 0)

    p_t = compute_p_t(df, [p0, alpha, beta_p], price_array, TARGET_P_MODEL, p_event_col)
    q_t = compute_q_t(df[q_event_col].values, q0, beta_q, TARGET_Q_FORM)

    base_rate = p_t + q_t * (N_lag / m)

    inflow_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            lag = np.concatenate([[0], inflow_dict[coin][:-1]])
            inflow_rate += gamma_in[i] * normalize(lag)

    outflow_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            lag = np.concatenate([[0], outflow_dict[coin][:-1]])
            outflow_rate += delta_out[i] * normalize(lag)

    growth = np.maximum((base_rate + inflow_rate - outflow_rate) * remaining, 0)

    direct = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct += inflow_dict[coin]

    return growth + direct

def residuals_fn(params, df, price_array, p_event_col, q_event_col,
                 inflow_dict, outflow_dict):
    idx = get_param_indices()
    if params[idx['m_idx']] <= df[CUM_COL].max() or params[idx['q_start']] < 0:
        return np.ones(len(df)) * 1e6
    pred = dN_prediction(df, params, price_array, p_event_col, q_event_col,
                         inflow_dict, outflow_dict)
    if np.any(np.isnan(pred)) or np.allclose(pred, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - pred

def fit_model(df, price_array, p_event_col, q_event_col,
              inflow_dict, outflow_dict):
    try:
        n_comp  = len(COMPETITORS)
        m_guess = 1.2 * df[CUM_COL].max()

        init = ([0.001, 0.01, 0.01]
                + [0.01, 0.01]
                + [0.0001] * n_comp
                + [0.0001] * n_comp
                + [m_guess])
        lo   = ([0,   -10, -10] + [0,   -10]
                + [-0.01]*n_comp + [-0.01]*n_comp + [0.875*m_guess])
        hi   = ([1,    10,  10] + [1,    10]
                + [0.01]*n_comp  + [0.01]*n_comp  + [10*m_guess])

        res = least_squares(residuals_fn, init, bounds=(lo, hi), method="trf",
                            args=(df, price_array, p_event_col, q_event_col,
                                  inflow_dict, outflow_dict))
        if res.status < 0:
            return None

        params = res.x
        n, k   = len(df), len(params)
        y_pred = dN_prediction(df, params, price_array, p_event_col, q_event_col,
                               inflow_dict, outflow_dict)

        eps, J = 1e-6, []
        for i in range(k):
            p_eps = params.copy(); p_eps[i] += eps
            y_eps = dN_prediction(df, p_eps, price_array, p_event_col, q_event_col,
                                  inflow_dict, outflow_dict)
            J.append((y_eps - y_pred) / eps)
        J = np.array(J).T
        try:    cond = np.linalg.cond(J.T @ J)
        except: cond = np.nan

        sigma2 = np.sum((df[NEW_COL].values - y_pred)**2) / max(n - k, 1)
        try:
            cov = sigma2 * np.linalg.inv(J.T @ J + 1e-12 * np.eye(k))
            se  = np.sqrt(np.diag(cov))
        except:
            se = np.full(k, np.nan)

        tvals = params / (se + 1e-12)
        pvals = 2 * (1 - t.cdf(np.abs(tvals), df=max(n - k, 1)))
        res.se, res.tvals, res.pvals, res.cond = se, tvals, pvals, cond
        return res
    except Exception as e:
        print(f"  拟合异常: {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# 日度迁移 → 周度聚合（分 Core / Peripheral）
# ─────────────────────────────────────────────────────────────────
def build_weekly_migration(daily_mig_path, main_df):
    try:
        df_d = pd.read_csv(daily_mig_path)
        df_d.columns = df_d.columns.str.strip()
        df_d['date'] = pd.to_datetime(df_d['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}")
        return None, None

    # 聚合到周（week starting Monday）
    df_d = df_d.set_index('date').sort_index()
    df_w = df_d.resample('W-MON', label='left', closed='left').sum().reset_index()
    df_w = df_w.rename(columns={'date': DATE_COL})

    # 对齐 main_df 日期
    main_dates = pd.DataFrame({DATE_COL: pd.to_datetime(main_df[DATE_COL].values)})
    df_merged  = main_dates.merge(df_w, on=DATE_COL, how='left').fillna(0)

    inflow_dict, outflow_dict = {}, {}
    n = len(main_df)

    for coin in COMPETITORS:
        suffix  = COMP_COL_MAP.get(coin, coin)
        in_col  = MIG_IN_PREFIX  + suffix
        out_col = MIG_OUT_PREFIX + suffix

        inflow_dict[coin]  = (df_merged[in_col].values
                              if in_col  in df_merged.columns else np.zeros(n))
        outflow_dict[coin] = (df_merged[out_col].values
                              if out_col in df_merged.columns else np.zeros(n))

        in_ok  = in_col  in df_merged.columns
        out_ok = out_col in df_merged.columns
        status = "✅" if (in_ok and out_ok) else ("⚠️ in only" if in_ok else
                                                   "⚠️ out only" if out_ok else "❌")
        print(f"  {status}  {coin:20s}  in={in_col}  out={out_col}")

    return inflow_dict, outflow_dict


# ─────────────────────────────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────────────────────────────
def plot_fit(dates, y_true, y_pred, metrics, combo_tag, save_path):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, y_true, color='#2166ac', lw=2.0, label=f'Actual ({ACTOR})')
    ax.plot(dates, y_pred, color='#d6604d', lw=2.0, ls='--', label='Fitted')
    textstr = (f"Adj. $R^2$ = {metrics['Adj_R2']:.3f}\n"
               f"RMSE = {metrics['RMSE']:.2f}\n"
               f"WAPE = {metrics['WAPE']:.2f}%")
    ax.text(0.02, 0.97, textstr, transform=ax.transAxes, fontsize=12,
            va='top', fontfamily='serif',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', alpha=0.8, ec='gray'))
    ax.set_title(f"ETH {PEAK} – {ACTOR} Developers | {combo_tag}", fontsize=10)
    ax.set_xlabel('Date'); ax.set_ylabel(f'New {ACTOR} Developers (Weekly)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30, ha='right')
    ax.legend(); ax.grid(axis='y', ls=':', alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"✅ 图已保存: {save_path}")
    plt.close()


# ─────────────────────────────────────────────────────────────────
# 主程序
# ─────────────────────────────────────────────────────────────────
def main():
    print(f"\n🔧 Actor={ACTOR}  Peak={PEAK}  频率=weekly  窗口={START_DATE}~{END_DATE}")
    print(f"   竞争项目 ({len(COMPETITORS)}): {COMPETITORS}")

    # ── 1. 加载 Core/Peripheral 开发者序列 ────────────────────────
    try:
        df_actor = pd.read_csv(ACTOR_CSV_PATH)
        df_actor.columns = df_actor.columns.str.strip()
        print(f"   actor CSV 列名: {list(df_actor.columns)}")
        date_candidates = [c for c in df_actor.columns
                           if any(k in c.lower() for k in ('date', 'period', 'week', 'time'))]
        if DATE_COL not in df_actor.columns:
            if date_candidates:
                df_actor = df_actor.rename(columns={date_candidates[0]: DATE_COL})
                print(f"   日期列 '{date_candidates[0]}' → 重命名为 '{DATE_COL}'")
            else:
                print(f"❌ 找不到日期列，所有列: {list(df_actor.columns)}"); sys.exit(1)
        df_actor[DATE_COL] = pd.to_datetime(df_actor[DATE_COL], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"❌ 无法读取 actor CSV: {e}"); sys.exit(1)

    # ── 2. 加载事件/价格特征 ───────────────────────────────────────
    all_feat_cols = list(set(P_EVENT_LIST + Q_EVENT_LIST + PRICE_LAG_COLS))
    try:
        df_feat = pd.read_csv(FEATURE_CSV)
        df_feat.columns = df_feat.columns.str.strip()
        if DATE_COL not in df_feat.columns:
            date_candidates = [c for c in df_feat.columns
                               if any(k in c.lower() for k in ('date', 'period', 'week', 'time'))]
            if date_candidates:
                df_feat = df_feat.rename(columns={date_candidates[0]: DATE_COL})
        # 兼容 "2020-10-05 - 2020-10-11" 格式
        df_feat[DATE_COL] = (df_feat[DATE_COL]
                             .astype(str)
                             .str.split(' - ')
                             .str[0]
                             .str.strip())
        df_feat[DATE_COL] = pd.to_datetime(df_feat[DATE_COL], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"❌ 无法读取特征 CSV: {e}"); sys.exit(1)

    missing_feat = [c for c in all_feat_cols if c not in df_feat.columns]
    if missing_feat:
        print(f"⚠️ 特征 CSV 缺少列: {missing_feat}")

    # ── 3. 合并 ────────────────────────────────────────────────────
    df = df_actor[[DATE_COL, NEW_COL, CUM_COL]].merge(
        df_feat[[DATE_COL] + [c for c in all_feat_cols if c in df_feat.columns]],
        on=DATE_COL, how='left')
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    df = df.ffill().fillna(0)

    # ── 4. 窗口过滤 ────────────────────────────────────────────────
    df = df[(df[DATE_COL] >= pd.to_datetime(START_DATE)) &
            (df[DATE_COL] <= pd.to_datetime(END_DATE))].copy().reset_index(drop=True)
    if df.empty:
        print("❌ 窗口内无数据"); sys.exit(1)
    print(f"✅ 数据: {df[DATE_COL].min().date()} ~ {df[DATE_COL].max().date()}, {len(df)} 周")

    # ── 5. 累积量归零（窗口内重新 cumsum）──────────────────────────
    df[CUM_COL] = df[NEW_COL].cumsum()
    df["N_lag"] = df[CUM_COL].shift(1).fillna(0).values

    # ── 6. 迁移数据（日度→周度）──────────────────────────────────
    print("\n📦 加载并聚合迁移数据...")
    inflow_dict, outflow_dict = build_weekly_migration(DAILY_MIG_PATH, df)
    if inflow_dict is None:
        print("❌ 迁移数据加载失败"); sys.exit(1)

    # ── 7. 参数名列表 ──────────────────────────────────────────────
    param_names = (["p0", "alpha", "beta_p", "q0", "beta_q"]
                   + [f"gamma_in_{c}"  for c in COMPETITORS]
                   + [f"delta_out_{c}" for c in COMPETITORS]
                   + ["m"])

    # ── 8. 网格搜索 ────────────────────────────────────────────────
    combos = [(p, q, pr)
              for p in P_EVENT_LIST
              for q in Q_EVENT_LIST
              for pr in PRICE_LAG_COLS]
    print(f"\n📊 共 {len(combos)} 个组合，开始拟合...\n")

    all_results, done, skip = [], 0, 0

    for p_col, q_col, price_col in combos:
        tag = f"P={p_col}|Q={q_col}|pr={price_col}"
        print(f"→ [{done+skip+1}/{len(combos)}] {tag}")

        raw = df[price_col].values.astype(float)
        price_arr = normalize(np.log(np.maximum(raw, 1e-8)))

        res = fit_model(df, price_arr, p_col, q_col, inflow_dict, outflow_dict)
        if res is None:
            print("  ✖ 拟合失败"); skip += 1; continue

        params = res.x
        y_pred = dN_prediction(df, params, price_arr, p_col, q_col,
                               inflow_dict, outflow_dict)
        metrics = compute_metrics(df[NEW_COL].values, y_pred, len(params))
        done += 1

        row = {
            "actor": ACTOR, "peak": PEAK, "freq": "weekly",
            "p_event_col": p_col, "q_event_col": q_col,
            "price_col": price_col, "price_tf": TARGET_PRICE_TF,
            **metrics,
            "cond": float(res.cond) if not np.isnan(res.cond) else np.nan,
        }
        for i, name in enumerate(param_names):
            if i < len(params):
                pv  = res.pvals[i]
                sig = ("***" if pv < 0.001 else "**" if pv < 0.01
                       else "*" if pv < 0.05 else "†" if pv < 0.1 else "")
                row[name]          = float(params[i])
                row[f"se_{name}"]  = float(res.se[i])
                row[f"t_{name}"]   = float(res.tvals[i])
                row[f"p_{name}"]   = float(pv)
                row[f"sig_{name}"] = sig
        all_results.append(row)

    df_out = pd.DataFrame(all_results)
    df_out.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 结果已保存: {OUTPUT_CSV}  (成功 {done}, 跳过 {skip})")

    if df_out.empty:
        print("❌ 无有效结果"); sys.exit(1)

    # ── 9. 最优模型汇报 ────────────────────────────────────────────
    best = df_out.loc[df_out["RMSE"].idxmin()]
    best_tag = f"P={best['p_event_col']}|Q={best['q_event_col']}|pr={best['price_col']}"
    print(f"\n{'='*80}")
    print(f"🏆 最低 RMSE [{ACTOR} / {PEAK} / weekly]: {best_tag}")
    print(f"{'='*80}")
    print(f"  RMSE   = {best['RMSE']:.4f}")
    print(f"  WAPE   = {best['WAPE']:.4f}%")
    print(f"  Adj_R2 = {best['Adj_R2']:.4f}")
    header = f"  {'参数':<30} {'估计值':>14} {'SE':>12} {'t':>10} {'p':>10} {'sig':>5}"
    print(f"\n{header}")
    print("  " + "-"*83)
    for name in param_names:
        if name in best:
            print(f"  {name:<30} {best[name]:>14.4e} "
                  f"{best.get(f'se_{name}', np.nan):>12.4e} "
                  f"{best.get(f't_{name}', np.nan):>10.3f} "
                  f"{best.get(f'p_{name}', np.nan):>10.4f} "
                  f"{best.get(f'sig_{name}', ''):>5}")

    # ── 10. 最优模型绘图 ───────────────────────────────────────────
    raw_best   = df[best['price_col']].values.astype(float)
    price_best = normalize(np.log(np.maximum(raw_best, 1e-8)))
    res_best = fit_model(df, price_best,
                         best['p_event_col'], best['q_event_col'],
                         inflow_dict, outflow_dict)
    if res_best is not None:
        y_pred_best = dN_prediction(df, res_best.x, price_best,
                                    best['p_event_col'], best['q_event_col'],
                                    inflow_dict, outflow_dict)
        m_best = compute_metrics(df[NEW_COL].values, y_pred_best, len(res_best.x))
        plot_fit(pd.to_datetime(df[DATE_COL].values),
                 df[NEW_COL].values, y_pred_best,
                 m_best, best_tag, OUTPUT_PNG)


if __name__ == "__main__":
    main()