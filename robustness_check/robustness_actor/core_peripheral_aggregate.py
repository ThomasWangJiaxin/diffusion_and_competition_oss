"""
将每日Core/Peripheral新增数据聚合为周度和月度
输入: btc_daily_new_core_peripheral.csv
输出: btc_weekly_core_peripheral.csv
       btc_monthly_core_peripheral.csv
"""

import pandas as pd
import numpy as np

INPUT_PATH   = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_daily_new_core_peripheral.csv"
OUTPUT_WEEK  = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_weekly_core_peripheral.csv"
OUTPUT_MONTH = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_monthly_core_peripheral.csv"

# ── 读取 ──────────────────────────────────────────────────
df = pd.read_csv(INPUT_PATH, parse_dates=['date'])
df = df.sort_values('date').reset_index(drop=True)
print(f"日度数据: {len(df)} 行，{df['date'].min().date()} 到 {df['date'].max().date()}")

# ── 聚合函数 ──────────────────────────────────────────────
def aggregate(df, freq, label):
    """
    freq: 'W-MON'（每周一为周起点）或 'MS'（月初）
    """
    agg = (
        df.set_index('date')
        [['Core', 'Peripheral', 'total_new_classified']]
        .resample(freq)
        .sum()
        .reset_index()
        .rename(columns={'date': 'period_start'})
    )

    # 重新计算累计（从聚合后的新增累加，保证一致性）
    agg['cum_Core']       = agg['Core'].cumsum()
    agg['cum_Peripheral'] = agg['Peripheral'].cumsum()
    agg['cum_total']      = agg['total_new_classified'].cumsum()

    # 诊断统计
    zero_core = (agg['Core'] == 0).mean()
    zero_peri = (agg['Peripheral'] == 0).mean()
    peak_mean_core = agg['Core'].max() / agg['Core'].mean() if agg['Core'].mean() > 0 else np.nan
    peak_mean_peri = agg['Peripheral'].max() / agg['Peripheral'].mean() if agg['Peripheral'].mean() > 0 else np.nan

    print(f"\n{'='*50}")
    print(f"{label}聚合结果: {len(agg)} 个周期")
    print(f"  Core    零值占比: {zero_core:.1%}   peak/mean: {peak_mean_core:.1f}x   总计: {agg['Core'].sum():,}")
    print(f"  Peripheral 零值占比: {zero_peri:.1%}   peak/mean: {peak_mean_peri:.1f}x   总计: {agg['Peripheral'].sum():,}")
    print(f"\n  Core新增描述统计:")
    print(agg['Core'].describe().to_string())
    print(f"\n  前10个{label}预览:")
    print(agg.head(10).to_string(index=False))

    return agg

# ── 周度：以周一为起点 ─────────────────────────────────────
df_weekly = aggregate(df, freq='W-MON', label='周度')
df_weekly.to_csv(OUTPUT_WEEK, index=False)
print(f"\n✅ 周度数据已保存: {OUTPUT_WEEK}")

# ── 月度：以月初为起点 ─────────────────────────────────────
df_monthly = aggregate(df, freq='MS', label='月度')
df_monthly.to_csv(OUTPUT_MONTH, index=False)
print(f"✅ 月度数据已保存: {OUTPUT_MONTH}")

# ── Bass可行性诊断汇总 ────────────────────────────────────
print("\n" + "=" * 50)
print("Bass模型可行性诊断汇总")
print("=" * 50)
print(f"{'指标':<25} {'日度':>10} {'周度':>10} {'月度':>10}")
print("-" * 55)

for label, data in [('日度', df), ('周度', df_weekly), ('月度', df_monthly)]:
    col = 'Core'
    zero = (data[col] == 0).mean()
    pm   = data[col].max() / data[col].mean() if data[col].mean() > 0 else np.nan
    if label == '日度':
        print(f"{'Core零值占比':<25} {zero:>10.1%}", end='')
    else:
        print(f" {zero:>10.1%}", end='')
print()

for label, data in [('日度', df), ('周度', df_weekly), ('月度', df_monthly)]:
    col = 'Core'
    pm = data[col].max() / data[col].mean() if data[col].mean() > 0 else np.nan
    if label == '日度':
        print(f"{'Core peak/mean':<25} {pm:>10.1f}x", end='')
    else:
        print(f" {pm:>10.1f}x", end='')
print()

print("\n判断标准: 零值占比<30% 且 peak/mean>3x → Bass可行")