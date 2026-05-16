# ETH Peak 1 Out-of-Sample Forecasting
# 3列：左=dN，中=cum做法1（全开环），右=cum做法2（forecast期用实际N_lag）
# 每图左上角图例，第一列右上角指标框

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

mpl.rcParams['font.family']     = 'serif'
mpl.rcParams['font.serif']      = ['Times New Roman']
mpl.rcParams['axes.labelsize']  = 11
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 9

# ============= 参数配置 =============
CSV_PATH       = "/home/lab0/survival_diffusion_github/competition_bass/ETHdev_day_timeline_event_all_with_price_event_features.csv"
MIGRATION_PATH = "/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv"
DATE_COL   = "date"
NEW_COL    = "eth_new_developers"
CUM_COL    = "eth_cum_users"
FULL_START = "2017-01-01"
FULL_END   = "2019-01-01"
OUTPUT_PNG = "eth_peak1_forecast_rolling.png"

TARGET_P_EVENT  = "eth_p_event_sum_30"
TARGET_Q_EVENT  = "eth_q_event_sum_7"
TARGET_PRICE    = "eth_price_lag1"
TARGET_PRICE_TF = "log"
TARGET_P_MODEL  = "additive"
TARGET_Q_FORM   = "linear"

# ===== ETH Peak 1 Rolling Periods =====
ROLLING_PERIODS = [
    {"label": "1st Rolling Period",
     "calib_end": "2017-06-30", "forecast_start": "2017-07-01"},
    {"label": "2nd Rolling Period",
     "calib_end": "2017-12-31", "forecast_start": "2018-01-01"},
    {"label": "3rd Rolling Period",
     "calib_end": "2018-06-30", "forecast_start": "2018-07-01"},
]

COMPETITORS = ["BTC", "Solana", "Cosmos", "TRON"]

# ----------------- 评估指标 -----------------
def compute_metrics(y_true, y_pred, k):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    n      = len(y_true)
    resid  = y_true - y_pred
    sse    = np.sum(resid ** 2)
    rmse   = math.sqrt(sse / n)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2     = 1 - sse / ss_tot if ss_tot > 0 else np.nan
    adj_r2 = (1 - (1 - r2) * (n - 1) / (n - k - 1)
              if (n - k - 1 > 0 and ss_tot > 0) else np.nan)
    wape   = np.sum(np.abs(resid)) / np.sum(np.abs(y_true)) * 100 \
             if np.sum(np.abs(y_true)) > 0 else np.nan
    return {"RMSE": rmse, "Adj_R2": adj_r2, "WAPE": wape}

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
    if q_form == "linear":   return np.maximum(q0 + beta * ev, 0)
    elif q_form == "log":    return np.maximum(q0 + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif q_form == "exp":    return q0 * np.exp(beta * ev)
    raise ValueError(f"未知 q_form: {q_form}")

def compute_p_t_from_array(df, params, price_array, p_model, p_event_col):
    ev = normalize(df[p_event_col].values)
    if p_model == "additive":
        p0, alpha, beta = params[:3]
        return np.maximum(p0 + alpha * price_array + beta * ev, 0)
    elif p_model == "nonlinear_event":
        p0, alpha, beta = params[:3]
        return np.maximum(p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)), 0)
    elif p_model == "interaction_linear":
        p0, alpha, beta, gamma = params[:4]
        return np.maximum(p0 + alpha * price_array + beta * ev + gamma * (price_array * ev), 0)
    elif p_model == "interaction_nonlinear":
        p0, alpha, beta, gamma = params[:4]
        return np.maximum(p0 + alpha * price_array + beta * np.log1p(np.maximum(ev, 0)) + gamma * (price_array * ev), 0)
    raise ValueError(f"未知 p_model: {p_model}")

def get_param_indices(p_model):
    n_comp        = len(COMPETITORS)
    p_param_count = 3 if p_model in ["additive", "nonlinear_event"] else 4
    q_start       = p_param_count
    gamma_start   = q_start + 2
    delta_start   = gamma_start + n_comp
    m_idx         = delta_start + n_comp
    return p_param_count, q_start, gamma_start, delta_start, m_idx, m_idx + 1

def build_norm_dicts(inflow_dict, outflow_dict):
    M_in_norms, M_out_norms = {}, {}
    for coin in COMPETITORS:
        if coin in inflow_dict:
            M_in_norms[coin]  = normalize(np.concatenate([[0], inflow_dict[coin][:-1]]))
        if coin in outflow_dict:
            M_out_norms[coin] = normalize(np.concatenate([[0], outflow_dict[coin][:-1]]))
    return M_in_norms, M_out_norms

def step_dN(i, N_lag_val, p_t, q_t, m,
            gamma_in_params, delta_out_params,
            M_in_norms, M_out_norms, inflow_dict):
    remaining    = max(m - N_lag_val, 0)
    base_rate    = p_t[i] + q_t[i] * (N_lag_val / m)
    inflow_rate  = sum(gamma_in_params[j]  * M_in_norms[c][i]
                       for j, c in enumerate(COMPETITORS) if c in M_in_norms)
    outflow_rate = sum(delta_out_params[j] * M_out_norms[c][i]
                       for j, c in enumerate(COMPETITORS) if c in M_out_norms)
    direct_mig   = sum(inflow_dict[c][i] for c in COMPETITORS if c in inflow_dict)
    return max((base_rate + inflow_rate - outflow_rate) * remaining + direct_mig, 0)

def get_pt_qt(df_full, params, price_arr_full, p_event_col, q_event_col, p_model, q_form):
    _, q_start, _, _, _, _ = get_param_indices(p_model)
    p_pc = 3 if p_model in ["additive", "nonlinear_event"] else 4
    p_t = compute_p_t_from_array(df_full, params[:p_pc], price_arr_full, p_model, p_event_col)
    q_t = compute_q_t_from_array(df_full[q_event_col].values,
                                  (params[q_start], params[q_start+1]), q_form)
    return p_t, q_t

def forecast_open(df_full, params, price_arr_full, p_event_col, q_event_col,
                  p_model, q_form, inflow_dict, outflow_dict):
    _, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
    p_t, q_t         = get_pt_qt(df_full, params, price_arr_full, p_event_col, q_event_col, p_model, q_form)
    m                = params[m_idx]
    gamma_in_params  = params[gamma_start: gamma_start + len(COMPETITORS)]
    delta_out_params = params[delta_start: delta_start + len(COMPETITORS)]
    M_in_norms, M_out_norms = build_norm_dicts(inflow_dict, outflow_dict)
    n = len(df_full)
    dN_pred, cum_pred = np.zeros(n), np.zeros(n)
    N_lag_val = df_full["N_lag"].values[0]
    for i in range(n):
        dN_i        = step_dN(i, N_lag_val, p_t, q_t, m,
                               gamma_in_params, delta_out_params,
                               M_in_norms, M_out_norms, inflow_dict)
        dN_pred[i]  = dN_i
        cum_pred[i] = N_lag_val + dN_i
        N_lag_val   = cum_pred[i]
    return dN_pred, cum_pred

def forecast_semiopen(df_full, params, price_arr_full, p_event_col, q_event_col,
                      p_model, q_form, inflow_dict, outflow_dict,
                      forecast_start_date, actual_cum):
    _, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
    p_t, q_t         = get_pt_qt(df_full, params, price_arr_full, p_event_col, q_event_col, p_model, q_form)
    m                = params[m_idx]
    gamma_in_params  = params[gamma_start: gamma_start + len(COMPETITORS)]
    delta_out_params = params[delta_start: delta_start + len(COMPETITORS)]
    M_in_norms, M_out_norms = build_norm_dicts(inflow_dict, outflow_dict)
    dates_full = pd.to_datetime(df_full[DATE_COL].values)
    n = len(df_full)
    dN_pred, cum_pred = np.zeros(n), np.zeros(n)
    N_lag_val = df_full["N_lag"].values[0]
    for i in range(n):
        if dates_full[i] >= forecast_start_date and i > 0:
            N_lag_val = actual_cum[i - 1]
        dN_i        = step_dN(i, N_lag_val, p_t, q_t, m,
                               gamma_in_params, delta_out_params,
                               M_in_norms, M_out_norms, inflow_dict)
        dN_pred[i]  = dN_i
        cum_pred[i] = N_lag_val + dN_i
        if dates_full[i] < forecast_start_date:
            N_lag_val = cum_pred[i]
    return dN_pred, cum_pred

def dN_pred_inline(df, params, price_array, p_event_col, q_event_col,
                   p_model, q_form, inflow_dict, outflow_dict):
    _, q_start, gamma_start, delta_start, m_idx, _ = get_param_indices(p_model)
    p_pc = 3 if p_model in ["additive", "nonlinear_event"] else 4
    p_t  = compute_p_t_from_array(df, params[:p_pc], price_array, p_model, p_event_col)
    q_t  = compute_q_t_from_array(df[q_event_col].values,
                                   (params[q_start], params[q_start+1]), q_form)
    m                = params[m_idx]
    gamma_in_params  = params[gamma_start: gamma_start + len(COMPETITORS)]
    delta_out_params = params[delta_start: delta_start + len(COMPETITORS)]
    N_lag = df["N_lag"].values
    remaining = np.maximum(m - N_lag, 0)
    base_rate = p_t + q_t * (N_lag / m)
    inflow_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in inflow_dict:
            inflow_rate += gamma_in_params[i] * normalize(np.concatenate([[0], inflow_dict[coin][:-1]]))
    outflow_rate = np.zeros_like(N_lag)
    for i, coin in enumerate(COMPETITORS):
        if coin in outflow_dict:
            outflow_rate += delta_out_params[i] * normalize(np.concatenate([[0], outflow_dict[coin][:-1]]))
    direct_mig = np.zeros_like(N_lag)
    for coin in COMPETITORS:
        if coin in inflow_dict:
            direct_mig += inflow_dict[coin]
    return (base_rate + inflow_rate - outflow_rate) * remaining + direct_mig

def residuals_pair(params, df, price_array, p_event_col, q_event_col,
                   p_model, q_form, inflow_dict, outflow_dict):
    _, q_start, _, _, m_idx, _ = get_param_indices(p_model)
    if params[m_idx] <= df[CUM_COL].max() or params[q_start] < 0:
        return np.ones(len(df)) * 1e6
    dN_pred = dN_pred_inline(df, params, price_array, p_event_col, q_event_col,
                              p_model, q_form, inflow_dict, outflow_dict)
    if np.any(np.isnan(dN_pred)) or np.allclose(dN_pred, 0):
        return np.ones(len(df)) * 1e6
    return df[NEW_COL].values - dN_pred

def fit_bass_pair(df, price_array, p_event_col, q_event_col,
                  p_model, q_form, inflow_dict, outflow_dict):
    try:
        m_guess = 1.2 * df[CUM_COL].max()
        n_comp  = len(COMPETITORS)
        if p_model in ["additive", "nonlinear_event"]:
            p_init=[0.001,0.01,0.01]; p_lo=[0,-10,-10]; p_hi=[1,10,10]
        else:
            p_init=[0.001,0.01,0.01,0.01]; p_lo=[0,-10,-10,-10]; p_hi=[1,10,10,10]
        q_init=[0.01,0.01]; q_lo=[0,-10]; q_hi=[1,10]
        g_init=[0.0001]*n_comp; g_lo=[-0.01]*n_comp; g_hi=[0.01]*n_comp
        d_init=[0.0001]*n_comp; d_lo=[-0.01]*n_comp; d_hi=[0.01]*n_comp
        init=p_init+q_init+g_init+d_init+[m_guess]
        lo=p_lo+q_lo+g_lo+d_lo+[0.875*m_guess]
        hi=p_hi+q_hi+g_hi+d_hi+[10*m_guess]
        res = least_squares(residuals_pair, init, bounds=(lo,hi), method="trf",
                            args=(df, price_array, p_event_col, q_event_col,
                                  p_model, q_form, inflow_dict, outflow_dict))
        if not res.success: return None
        params=res.x; n,k=len(df),len(params)
        y_pred = dN_pred_inline(df, params, price_array, p_event_col, q_event_col,
                                 p_model, q_form, inflow_dict, outflow_dict)
        eps=1e-6; J=[]
        for i in range(k):
            pe=params.copy(); pe[i]+=eps
            ye = dN_pred_inline(df, pe, price_array, p_event_col, q_event_col,
                                 p_model, q_form, inflow_dict, outflow_dict)
            J.append((ye-y_pred)/eps)
        J=np.array(J).T
        try: cond=np.linalg.cond(J.T@J)
        except: cond=np.nan
        sigma2=np.sum((df[NEW_COL].values-y_pred)**2)/(n-k)
        try:
            cov=sigma2*np.linalg.inv(J.T@J+1e-12*np.eye(k))
            se=np.sqrt(np.diag(cov))
        except: se=np.full(k,np.nan)
        tvals=params/(se+1e-12)
        pvals=2*(1-t.cdf(np.abs(tvals),df=n-k))
        res.se,res.tvals,res.pvals,res.cond=se,tvals,pvals,cond
        return res
    except Exception as e:
        print(f"  拟合异常: {e}"); return None

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
    in_map = {
        "BTC":    "in_from_BTC",
        "Cosmos": "in_from_Cosmos",
        "Solana": "in_from_Solana",
        "TRON":   "in_from_TRON",
    }
    out_map = {
        "BTC":    "out_to_BTC",
        "Cosmos": "out_to_Cosmos",
        "Solana": "out_to_Solana",
        "TRON":   "out_to_TRON",
    }
    df_idx     = df_merged.set_index(DATE_COL)
    main_dates = pd.DatetimeIndex(main_df[DATE_COL].values)
    inflow_dict, outflow_dict = {}, {}
    for coin in COMPETITORS:
        col = in_map.get(coin)
        inflow_dict[coin] = (df_idx.reindex(main_dates)[col].fillna(0).values
                             if col and col in df_merged.columns else np.zeros(len(main_df)))
        col = out_map.get(coin)
        outflow_dict[coin] = (df_idx.reindex(main_dates)[col].fillna(0).values
                              if col and col in df_merged.columns else np.zeros(len(main_df)))
    return inflow_dict, outflow_dict

def add_metrics_box(ax, metrics, loc='upper right'):
    txt = (f"RMSE = {metrics['RMSE']:.2f}\n"
           f"WAPE = {metrics['WAPE']:.2f}%\n")
        #    f"Adj.$R^2$ = {metrics['Adj_R2']:.4f}")
    x  = 0.98 if 'right' in loc else 0.02
    ha = 'right' if 'right' in loc else 'left'
    ax.text(x, 0.97, txt, transform=ax.transAxes,
            fontsize=8.5, va='top', ha=ha, fontfamily='serif',
            bbox=dict(boxstyle='round,pad=0.3',
                      facecolor='white', alpha=0.85, edgecolor='gray'))

def format_ax(ax, dates_full, forecast_start, colors,
              show_legend=False, legend_loc='upper left'):
    ax.axvline(x=forecast_start, color=colors['vline'], linewidth=0.9)
    ax.axvspan(dates_full[0],  forecast_start, alpha=0.05, color=colors['shade_c'])
    ax.axvspan(forecast_start, dates_full[-1],  alpha=0.05, color=colors['shade_f'])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')
    ax.grid(axis='y', linestyle=':', alpha=0.4)
    if show_legend:
        ax.legend(fontsize=8.5, loc=legend_loc, framealpha=0.85, edgecolor='gray')

def main():
    try:
        df_raw = pd.read_csv(CSV_PATH, parse_dates=[DATE_COL])
    except Exception as e:
        print(f"无法读取 CSV: {e}"); sys.exit(1)
    df_raw = df_raw.sort_values(DATE_COL).reset_index(drop=True)

    df_full = df_raw[[DATE_COL,NEW_COL,CUM_COL,
                      TARGET_P_EVENT,TARGET_Q_EVENT,TARGET_PRICE]].copy()
    df_full = df_full.ffill().fillna(0)
    df_full = df_full[(df_full[DATE_COL]>=pd.to_datetime(FULL_START)) &
                      (df_full[DATE_COL]<=pd.to_datetime(FULL_END))].copy().reset_index(drop=True)
    cum_offset       = df_full[CUM_COL].iloc[0] - df_full[NEW_COL].iloc[0]
    df_full[CUM_COL] = df_full[CUM_COL] - cum_offset
    df_full["N_lag"] = df_full[CUM_COL].shift(1).fillna(0).values

    inflow_dict, outflow_dict = load_migration_data(MIGRATION_PATH, df_full)
    if inflow_dict is None:
        print("❌ 迁移数据加载失败"); sys.exit(1)

    raw_price = df_full[TARGET_PRICE].values.astype(float)
    price_arr_full = normalize(np.log(np.maximum(raw_price, 1e-8))) \
                     if TARGET_PRICE_TF == "log" else normalize(raw_price)

    dates_full = pd.to_datetime(df_full[DATE_COL].values)
    actual_dN  = df_full[NEW_COL].values
    actual_cum = df_full[CUM_COL].values

    colors = {'actual':'#2c2c2c','calib':'#2166ac','forecast':'#d6604d',
              'vline':'#666666','shade_c':'#d6eaf8','shade_f':'#fde8e4'}

    fig, axes = plt.subplots(3, 3, figsize=(18, 12))
    fig.suptitle('ETH Peak 1 — Out-of-Sample Forecasting (Rolling Windows)',
                 fontsize=13, y=1.005)
    col_titles = ['Daily New Developers',
                  'Cumulative Developers (Open-loop)',
                  'Cumulative Developers (Semi-open)']
    for col, title in enumerate(col_titles):
        axes[0, col].set_title(title, fontsize=10, pad=8)

    for row_idx, period in enumerate(ROLLING_PERIODS):
        calib_end      = pd.to_datetime(period["calib_end"])
        forecast_start = pd.to_datetime(period["forecast_start"])
        label          = period["label"]

        mask_calib = df_full[DATE_COL] <= calib_end
        df_calib   = df_full[mask_calib].copy().reset_index(drop=True)
        price_calib = price_arr_full[mask_calib.values]
        in_calib  = {c: v[mask_calib.values] for c,v in inflow_dict.items()}
        out_calib = {c: v[mask_calib.values] for c,v in outflow_dict.items()}

        print(f"\n→ 拟合 {label}")
        res = fit_bass_pair(df_calib, price_calib,
                            TARGET_P_EVENT, TARGET_Q_EVENT,
                            TARGET_P_MODEL, TARGET_Q_FORM,
                            in_calib, out_calib)
        if res is None:
            print(f"  ❌ 拟合失败"); continue

        params = res.x
        k      = len(params)

        dN1, cum1 = forecast_open(df_full, params, price_arr_full,
                                   TARGET_P_EVENT, TARGET_Q_EVENT,
                                   TARGET_P_MODEL, TARGET_Q_FORM,
                                   inflow_dict, outflow_dict)
        dN2, cum2 = forecast_semiopen(df_full, params, price_arr_full,
                                       TARGET_P_EVENT, TARGET_Q_EVENT,
                                       TARGET_P_MODEL, TARGET_Q_FORM,
                                       inflow_dict, outflow_dict,
                                       forecast_start, actual_cum)

        mask_fc  = dates_full >= forecast_start
        mask_fit = ~mask_fc

        m_dN  = compute_metrics(actual_dN[mask_fc],  dN1[mask_fc],  k)
        m_cum1= compute_metrics(actual_cum[mask_fc], cum1[mask_fc], k)
        m_cum2= compute_metrics(actual_cum[mask_fc], cum2[mask_fc], k)

        print(f"  dN   RMSE={m_dN['RMSE']:.2f}  WAPE={m_dN['WAPE']:.2f}%  Adj.R²={m_dN['Adj_R2']:.4f}")
        print(f"  cum1 RMSE={m_cum1['RMSE']:.2f}  WAPE={m_cum1['WAPE']:.2f}%  Adj.R²={m_cum1['Adj_R2']:.4f}")
        print(f"  cum2 RMSE={m_cum2['RMSE']:.2f}  WAPE={m_cum2['WAPE']:.2f}%  Adj.R²={m_cum2['Adj_R2']:.4f}")

        for col_idx, (actual_arr, pred_arr, metrics) in enumerate([
                (actual_dN,  dN1,  m_dN),
                (actual_cum, cum1, m_cum1),
                (actual_cum, cum2, m_cum2),
        ]):
            ax = axes[row_idx, col_idx]
            ax.plot(dates_full, actual_arr,
                    color=colors['actual'], linewidth=1.2, label='Actual')
            ax.plot(dates_full[mask_fit], pred_arr[mask_fit],
                    color=colors['calib'], linewidth=1.3, linestyle='-', label='Fitted')
            ax.plot(dates_full[mask_fc],  pred_arr[mask_fc],
                    color=colors['forecast'], linewidth=1.3, linestyle='--', label='Forecast')
            ylabel = 'Daily New Developers' if col_idx == 0 else 'Cumulative Developers'
            ax.set_ylabel(f'{label}\n{ylabel}', fontsize=10)
            format_ax(ax, dates_full, forecast_start, colors,
                      show_legend=True, legend_loc='upper left')
            if col_idx == 0:
                add_metrics_box(ax, metrics, loc='upper right')

    for col in range(3):
        for row in range(2):
            axes[row, col].set_xlabel('')
        axes[2, col].set_xlabel('Date', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches='tight')
    print(f"\n✅ 图已保存: {OUTPUT_PNG}")
    plt.close()

if __name__ == "__main__":
    main()