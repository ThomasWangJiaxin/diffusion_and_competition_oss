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

# ===== 全局字体设置 =====
mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.titlesize']  = 14
mpl.rcParams['axes.labelsize']  = 13
mpl.rcParams['xtick.labelsize'] = 12
mpl.rcParams['ytick.labelsize'] = 12
mpl.rcParams['legend.fontsize'] = 12

# ============= 参数配置 =============
CSV_PATH       = "/home/lab0/survival_diffusion_github/competition_bass/BTCdev_day_timeline_event_all_with_price_event_features.csv"
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/sensitivity/outflow_window/btc_global_migration_enhanced_1080_daily_strict_rules.csv"
DATE_COL   = "date"
NEW_COL    = "btc_new_developers"
CUM_COL    = "btc_cum_users"
START_DATE = "2017-01-01"
END_DATE   = "2019-01-01"
OUTPUT_PNG = "/home/lab0/survival_diffusion_github/sensitivity/outflow_window/btc_peak1_1080_best_fit_plot.png"
OUTPUT_CSV = "/home/lab0/survival_diffusion_github/sensitivity/outflow_window/btc_peak1_1080_grid_search_results.csv"

# ============= 遍历列表 =============
P_EVENT_LIST = [
    "btc_p_event_lag1","btc_p_event_sum_7","btc_p_event_sum_14","btc_p_event_sum_21","btc_p_event_sum_30",
    # "btc_p_eip_p_event_lag1","btc_p_eip_p_event_sum_7","btc_p_eip_p_event_sum_14","btc_p_eip_p_event_sum_21","btc_p_eip_p_event_sum_90"
]
Q_EVENT_LIST = [
    "btc_q_event_lag1","btc_q_event_sum_7","btc_q_event_sum_14","btc_q_event_sum_21","btc_q_event_sum_30",
    # "btc_q_eip_q_event_lag1","btc_q_eip_q_event_sum_7","btc_q_eip_q_event_sum_14","btc_q_eip_q_event_sum_21","btc_q_eip_q_event_sum_90"
]
PRICE_LAG_COLS = [
    "btc_price_lag1","btc_ma_7d","btc_ma_14d","btc_ma_21d","btc_ma_30d"
]

# ============= 固定配置 =============
TARGET_PRICE_TF = "log"
TARGET_P_MODEL  = "additive"
TARGET_Q_FORM   = "linear"

COMPETITORS = ["ETH", "Dogecoin", "Lightning Network", "Monero", "Litecoin", "BTCD", "Zcash", "BCOIN", "TRON", "Stacks", "BitcoinCash", "LBTC", "BitcoinGpu", "Parity", "Rootstock"]

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
    mask  = y_true != 0
    mape  = np.mean(np.abs(resid[mask] / y_true[mask])) * 100 if mask.sum() > 0 else np.nan
    denom = np.sum(np.abs(y_true))
    wape  = np.sum(np.abs(resid)) / denom * 100 if denom > 0 else np.nan
    return {"MAD": mad, "SSE": sse, "MSE": mse, "RMSE": rmse,
            "R2": r2, "Adj_R2": adj_r2, "MAPE": mape, "WAPE": wape}

# ----------------- 工具函数 -----------------
def normalize(x):
    x   = np.array(x, dtype=float)
    std = np.std(x)
    if std <= 0:
        return x - np.mean(x)
    return (x - np.mean(x)) / (std + 1e-12)

def compute_q_t_from_array(event_arr, q_params, q_form):
    q0, beta = q_params
    ev = normalize(event_arr)
    if q_form == "linear":
        return np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":
        return np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":
        return q0 * np.exp(beta * ev)
    raise ValueError(f"未知 q_form: {q_form}")

def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    ev = normalize(df[p_event_col].values)
    if p_model == "additive":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * ev
    elif p_model == "nonlinear_event":
        p0, alpha, beta = params[:3]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0))
    elif p_model == "interaction_linear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * ev + gamma * (price_array * ev)
    elif p_model == "interaction_nonlinear":
        p0, alpha, beta, gamma = params[:4]
        p_t = p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev)
    else:
        raise ValueError(f"未知 p_model: {p_model}")
    return np.maximum(p_t, 0)

def get_param_indices(p_model):
    n_comp        = len(COMPETITORS)
    p_param_count = 3 if p_model in ["additive", "nonlinear_event"] else 4
    q_start       = p_param_count
    gamma_start   = q_start + 2
    delta_start   = gamma_start + n_comp
    m_idx         = delta_start + n_comp
    return p_param_count, q_start, gamma_start, delta_start, m_idx, m_idx + 1

def dN_pred_from_Nlag(N_lag, p_t_arr, q_t_arr, m,
                      inflow_dict, outflow_dict,
                      gamma_in_params, delta_out_params):
    remaining = np.maximum(m - N_lag, 0)
    base_rate = p_t_arr + q_t_arr * (N_lag / m)
    inflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            M_in_lag = np.concatenate([[0], inflow_dict[coin][:-1]])
            inflow_network_rate += gamma_in_params[i] * normalize(M_in_lag)
    outflow_network_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            M_out_lag = np.concatenate([[0], outflow_dict[coin][:-1]])
            outflow_network_rate += delta_out_params[i] * normalize(M_out_lag)
    constrained_growth = np.maximum(
    (base_rate + inflow_network_rate - outflow_network_rate) * remaining, 0)
    direct_migration = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct_migration += inflow_dict[coin]
    return constrained_growth + direct_migration

def compute_prediction_pair(df, params, price_array,
                             p_event_col, q_event_col,
                             p_model, q_form,
                             inflow_dict, outflow_dict):
    p_param_count, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
    p_params         = params[:p_param_count]
    q0, beta_q       = params[q_start], params[q_start + 1]
    gamma_in_params  = params[gamma_start: gamma_start + len(COMPETITORS)]
    delta_out_params = params[delta_start: delta_start + len(COMPETITORS)]
    m                = params[m_idx]
    p_t = compute_p_t_from_array(df, p_params, price_array, p_model, p_event_col)
    q_t = compute_q_t_from_array(df[q_event_col].values, (q0, beta_q), q_form)
    dN  = dN_pred_from_Nlag(df["N_lag"].values, p_t, q_t, m,
                             inflow_dict, outflow_dict,
                             gamma_in_params, delta_out_params)
    return dN, p_t, q_t

def residuals_pair(params, df, price_array,
                   p_event_col, q_event_col,
                   p_model, q_form,
                   inflow_dict, outflow_dict):
    _, q_start, _, _, m_idx, _ = get_param_indices(p_model)
    if params[m_idx] <= df[CUM_COL].max() or params[q_start] < 0:
        return np.ones(len(df)) * 1e6
    dN_pred, _, _ = compute_prediction_pair(
        df, params, price_array, p_event_col, q_event_col,
        p_model, q_form, inflow_dict, outflow_dict)
    if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0) or np.any(dN_pred < 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - dN_pred

def fit_bass_pair(df, price_array,
                  p_event_col, q_event_col,
                  p_model, q_form,
                  inflow_dict, outflow_dict):
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        n_comp  = len(COMPETITORS)
        if p_model in ["additive", "nonlinear_event"]:
            p_init = [0.001, 0.01, 0.01]; p_lo = [0,-10,-10]; p_hi = [1,10,10]
        else:
            p_init = [0.001,0.01,0.01,0.01]; p_lo=[0,-10,-10,-10]; p_hi=[1,10,10,10]
        q_init     = [0.01, 0.01];      q_lo = [0,-10];          q_hi = [1,10]
        gamma_init = [0.0001]*n_comp;   gamma_lo=[-0.01]*n_comp;  gamma_hi=[0.01]*n_comp
        delta_init = [0.0001]*n_comp;   delta_lo=[-0.01]*n_comp;  delta_hi=[0.01]*n_comp
        init = p_init + q_init + gamma_init + delta_init + [m_guess]
        lo   = p_lo   + q_lo   + gamma_lo   + delta_lo   + [0.875*m_guess]
        hi   = p_hi   + q_hi   + gamma_hi   + delta_hi   + [10*m_guess]
        res = least_squares(residuals_pair, init, bounds=(lo, hi), method="trf",
                            args=(df, price_array, p_event_col, q_event_col,
                                  p_model, q_form, inflow_dict, outflow_dict))
        if res.status <= 0:
            return None
        params = res.x
        n, k   = len(df), len(params)
        y_pred, _, _ = compute_prediction_pair(
            df, params, price_array, p_event_col, q_event_col,
            p_model, q_form, inflow_dict, outflow_dict)
        eps = 1e-6
        J   = []
        for i in range(k):
            p_eps = params.copy(); p_eps[i] += eps
            y_eps, _, _ = compute_prediction_pair(
                df, p_eps, price_array, p_event_col, q_event_col,
                p_model, q_form, inflow_dict, outflow_dict)
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

# --------- 加载迁移数据 ----------
def load_migration_data(migration_path, main_df):
    try:
        df_mig = pd.read_csv(migration_path)
        df_mig['date'] = pd.to_datetime(df_mig['date'], format='mixed', dayfirst=False)
    except Exception as e:
        print(f"⚠️ 无法读取迁移数据: {e}"); return None, None
    date_range = pd.date_range(start=main_df[DATE_COL].min(),
                               end=main_df[DATE_COL].max(), freq='D')
    df_merged  = pd.DataFrame({DATE_COL: date_range}).merge(
        df_mig, left_on=DATE_COL, right_on='date', how='left')
    inflow_col_mapping = {
        "BCOIN": "in_from_BCOIN", 
        "BTCD": "in_from_BTCD",
        "BitcoinCash": "in_from_Bitcoincash",      # ✅ 修正
        "BitcoinGpu": "in_from_Bitcoingpu",        # ✅ 修正
        "Dogecoin": "in_from_Dogecoin", 
        "ETH": "in_from_ETH",
        "LBTC": "in_from_LBTC", 
        "Lightning Network": "in_from_Lightningnetwork",
        "Litecoin": "in_from_Litecoin", 
        "Monero": "in_from_Monero",
        "Parity": "in_from_Parity", 
        "Rootstock": "in_from_Rootstock",
        "Stacks": "in_from_Stacks",
        "TRON": "in_from_TRON", 
        "Zcash": "in_from_ZCASH"                  # ✅ 修正
    }
    outflow_col_mapping = {
        "BCOIN": "out_to_BCOIN", 
        "BTCD": "out_to_BTCD",
        "BitcoinCash": "out_to_Bitcoincash",
        "BitcoinGpu": "out_to_Bitcoingpu",
        "Dogecoin": "out_to_Dogecoin", 
        "ETH": "out_to_ETH",
        "LBTC": "out_to_LBTC", 
        "Lightning Network": "out_to_Lightningnetwork",
        "Litecoin": "out_to_Litecoin", 
        "Monero": "out_to_Monero",
        "Parity": "out_to_Parity", 
        "Rootstock": "out_to_Rootstock",
        "Stacks": "out_to_Stacks", 
        "TRON": "out_to_TRON", 
        "Zcash": "out_to_ZCASH"
    }
    df_idx     = df_merged.set_index(DATE_COL)
    main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    inflow_dict, outflow_dict = {}, {}
    for coin in COMPETITORS:
        col = inflow_col_mapping.get(coin)
        inflow_dict[coin] = (
            df_idx.reindex(main_dates)[col].fillna(0).values
            if col and col in df_merged.columns
            else np.zeros(len(main_df)))
        col = outflow_col_mapping.get(coin)
        outflow_dict[coin] = (
            df_idx.reindex(main_dates)[col].fillna(0).values
            if col and col in df_merged.columns
            else np.zeros(len(main_df)))
    return inflow_dict, outflow_dict

# --------- 绘图函数 ----------
def plot_fit(dates, y_true, y_pred, metrics, combo_tag, save_path):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, y_true, color='#2166ac', linewidth=2.0, label='Actual new developers')
    ax.plot(dates, y_pred, color='#d6604d', linewidth=2.0, linestyle='--', label='Fitted new developers')
    ax.set_xlabel('Date', fontsize=13)
    ax.set_ylabel('Daily New Developers', fontsize=13)
    textstr = (f"Adj. $R^2$ = {metrics['Adj_R2']:.3f}\n"
               f"RMSE = {metrics['RMSE']:.2f}\n"
               f"WAPE = {metrics['WAPE']:.2f}%")
    ax.text(0.02, 0.97, textstr, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', fontfamily='serif',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray'))
    ax.set_title(f"Best Model: {combo_tag}", fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=90, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(axis='y', linestyle=':', alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"✅ 图已保存: {save_path}")
    plt.close()

# =================== 主程序 ===================
def main():
    # ---- 读取数据 ----
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}"); sys.exit(1)
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    # 检查所有需要的列
    all_event_cols = list(set(P_EVENT_LIST + Q_EVENT_LIST + PRICE_LAG_COLS))
    required = [DATE_COL, NEW_COL, CUM_COL] + all_event_cols
    missing  = [c for c in required if c not in df_raw.columns]
    if missing:
        print(f"❌ 缺少列: {missing}"); sys.exit(1)

    df_base = df_raw[[DATE_COL, NEW_COL, CUM_COL] + all_event_cols].copy()
    df_base = df_base.ffill().fillna(0)
    df_base = df_base[(df_base[DATE_COL] >= pd.to_datetime(START_DATE)) &
                      (df_base[DATE_COL] <= pd.to_datetime(END_DATE))].copy()
    if df_base.empty:
        print("❌ 过滤后数据为空"); sys.exit(1)

    # 窗口内累积归零
    cum_offset      = df_base[CUM_COL].iloc[0] - df_base[NEW_COL].iloc[0]
    df_base[CUM_COL] = df_base[CUM_COL] - cum_offset
    df_base["N_lag"] = df_base[CUM_COL].shift(1).fillna(0).values

    # 加载迁移数据（只需一次）
    inflow_dict, outflow_dict = load_migration_data(MIGRATION_PATH, df_base)
    if inflow_dict is None:
        print("❌ 迁移数据加载失败"); sys.exit(1)

    # 参数名列表（固定 additive 模型）
    param_names = ["p0", "alpha", "beta_p", "q0", "beta_q"]
    for coin in COMPETITORS: param_names.append(f"gamma_in_{coin}")
    for coin in COMPETITORS: param_names.append(f"delta_out_{coin}")
    param_names.append("m")

    # ---- 遍历所有组合 ----
    total_combos = len(P_EVENT_LIST) * len(Q_EVENT_LIST) * len(PRICE_LAG_COLS)
    print(f"\n📊 共 {total_combos} 个组合，开始遍历...\n")

    all_results  = []
    done, skip   = 0, 0

    for p_col in P_EVENT_LIST:
        for q_col in Q_EVENT_LIST:
            for price_col in PRICE_LAG_COLS:
                combo_tag = f"P={p_col} | Q={q_col} | price={price_col}({TARGET_PRICE_TF})"
                print(f"→ [{done+skip+1}/{total_combos}] {combo_tag}")

                # 构造价格数组
                raw_price = df_base[price_col].values.astype(float)
                if TARGET_PRICE_TF == "log":
                    price_arr = normalize(np.log(np.maximum(raw_price, 1e-8)))
                elif TARGET_PRICE_TF == "exp":
                    price_arr = normalize(np.exp(np.clip(raw_price, -50, 50)))
                else:
                    price_arr = normalize(raw_price)

                res = fit_bass_pair(df_base, price_arr,
                                    p_col, q_col,
                                    TARGET_P_MODEL, TARGET_Q_FORM,
                                    inflow_dict, outflow_dict)
                if res is None:
                    print("  ✖ 拟合失败，跳过")
                    skip += 1
                    continue

                params = res.x
                k      = len(params)
                y_pred, _, _ = compute_prediction_pair(
                    df_base, params, price_arr, p_col, q_col,
                    TARGET_P_MODEL, TARGET_Q_FORM, inflow_dict, outflow_dict)
                metrics = compute_metrics(df_base[NEW_COL].values, y_pred, k)
                done += 1

                # 构造结果行
                row = {
                    "p_event_col":  p_col,
                    "q_event_col":  q_col,
                    "price_col":    price_col,
                    "price_tf":     TARGET_PRICE_TF,
                    "p_model":      TARGET_P_MODEL,
                    "q_form":       TARGET_Q_FORM,
                    **metrics,
                    "cond":         float(res.cond) if not np.isnan(res.cond) else np.nan,
                }
                for i, name in enumerate(param_names):
                    if i < len(params):
                        pv  = res.pvals[i] if hasattr(res, 'pvals') else np.nan
                        sig = ("***" if pv < 0.001 else "**" if pv < 0.01
                               else "*" if pv < 0.05 else "†" if pv < 0.1 else "")
                        row[name]              = float(params[i])
                        row[f"se_{name}"]      = float(res.se[i])
                        row[f"t_{name}"]       = float(res.tvals[i])
                        row[f"p_{name}"]       = float(pv)
                        row[f"sig_{name}"]     = sig
                all_results.append(row)

    # ---- 保存 CSV ----
    df_results = pd.DataFrame(all_results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ 所有结果已保存: {OUTPUT_CSV}  (成功 {done} 次，跳过 {skip} 次)")

    if df_results.empty:
        print("❌ 无有效结果"); sys.exit(1)

    # ---- 打印最优 RMSE 模型 ----
    best_idx = df_results["RMSE"].idxmin()
    best_row = df_results.loc[best_idx]
    best_tag = (f"P={best_row['p_event_col']} | Q={best_row['q_event_col']} | "
                f"price={best_row['price_col']}({best_row['price_tf']})")

    print("\n" + "="*80)
    print(f"🏆 最低 RMSE 模型: {best_tag}")
    print("="*80)
    print(f"  RMSE    = {best_row['RMSE']:.4f}")
    print(f"  WAPE    = {best_row['WAPE']:.4f}%")
    print(f"  Adj_R2  = {best_row['Adj_R2']:.4f}")
    print(f"  R2      = {best_row['R2']:.4f}")
    print("\n  参数估计与显著性:")
    print(f"  {'参数':<28} {'估计值':>14} {'SE':>12} {'t':>10} {'p':>10} {'显著性':>6}")
    print("  " + "-"*82)
    for name in param_names:
        if name in best_row:
            est = best_row[name]
            se  = best_row.get(f"se_{name}", np.nan)
            tv  = best_row.get(f"t_{name}",  np.nan)
            pv  = best_row.get(f"p_{name}",  np.nan)
            sig = best_row.get(f"sig_{name}", "")
            print(f"  {name:<28} {est:>14.6e} {se:>12.4e} {tv:>10.3f} {pv:>10.4f} {sig:>6}")

    # ---- 重新拟合最优模型并绘图 ----
    raw_price_best = df_base[best_row['price_col']].values.astype(float)
    price_arr_best = normalize(np.log(np.maximum(raw_price_best, 1e-8)))

    res_best = fit_bass_pair(df_base, price_arr_best,
                             best_row['p_event_col'], best_row['q_event_col'],
                             TARGET_P_MODEL, TARGET_Q_FORM,
                             inflow_dict, outflow_dict)
    if res_best is not None:
        y_pred_best, _, _ = compute_prediction_pair(
            df_base, res_best.x, price_arr_best,
            best_row['p_event_col'], best_row['q_event_col'],
            TARGET_P_MODEL, TARGET_Q_FORM, inflow_dict, outflow_dict)
        metrics_best = compute_metrics(df_base[NEW_COL].values, y_pred_best, len(res_best.x))
        plot_fit(pd.to_datetime(df_base[DATE_COL].values),
                 df_base[NEW_COL].values, y_pred_best,
                 metrics_best, best_tag, OUTPUT_PNG)

if __name__ == "__main__":
    main()