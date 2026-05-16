"""
将日频迁移数据聚合为 周/月/季度 频率
输入:  btc_global_migration_enhanced_daily_strict_rules.csv
输出:  btc_global_migration_enhanced_weekly_strict_rules.csv
       btc_global_migration_enhanced_monthly_strict_rules.csv
       btc_global_migration_enhanced_quarterly_strict_rules.csv

聚合规则:
  - in_from_* / out_to_* 列: sum（期间内迁移总量）
  - date 列: 每个周期的起始日（week=周一, month=月初, quarter=季初）
"""

import pandas as pd
import numpy as np

DAILY_PATH = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/eth_global_migration_enhanced_daily_strict_rules.csv"
OUT_WEEKLY      = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/eth_global_migration_enhanced_weekly_strict_rules.csv"
OUT_MONTHLY     = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/eth_global_migration_enhanced_monthly_strict_rules.csv"
OUT_QUARTERLY   = "/home/lab0/survival_diffusion_github/robustness_check/robustness_window/eth_global_migration_enhanced_quarterly_strict_rules.csv"

# ── 读取日频数据 ──────────────────────────────────────────────────────
df = pd.read_csv(DAILY_PATH)
df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=False)
df = df.sort_values('date').reset_index(drop=True)

# 识别所有 in_from_ / out_to_ 数值列（其余列除 date 外忽略）
flow_cols = [c for c in df.columns if c.startswith('in_from_') or c.startswith('out_to_')]
print(f"✅ 共识别 {len(flow_cols)} 个迁移列")
print(f"   日频数据范围: {df['date'].min().date()} ~ {df['date'].max().date()}, {len(df)} 行")

# ── 通用聚合函数 ─────────────────────────────────────────────────────
def aggregate_migration(df, freq, label):
    """
    freq:
      'W-MON' → 以周一为起点的周频（date = 该周周一）
      'MS'    → 月初（date = 月第一天）
      'QS'    → 季初（date = 季度第一天）
    """
    df_agg = (
        df.set_index('date')[flow_cols]
          .resample(freq)
          .sum()
          .reset_index()
    )
    # date 列已经是每个周期的起始日，确保为 datetime
    df_agg['date'] = pd.to_datetime(df_agg['date'])
    # 去掉全零行（无数据的远古/未来周期）
    df_agg = df_agg[df_agg[flow_cols].sum(axis=1) >= 0].copy()
    print(f"\n📅 {label} 聚合完成: {len(df_agg)} 行, "
          f"范围 {df_agg['date'].min().date()} ~ {df_agg['date'].max().date()}")
    # 简单统计
    total_in  = df_agg[[c for c in flow_cols if c.startswith('in_from_')]].sum().sum()
    total_out = df_agg[[c for c in flow_cols if c.startswith('out_to_')]].sum().sum()
    print(f"   总迁入: {total_in:.0f}, 总迁出: {total_out:.0f}")
    return df_agg

# ── 生成三个频率 ──────────────────────────────────────────────────────
df_weekly    = aggregate_migration(df, 'W-MON',  'Weekly')
df_monthly   = aggregate_migration(df, 'MS',     'Monthly')
df_quarterly = aggregate_migration(df, 'QS',     'Quarterly')

# ── 保存 ─────────────────────────────────────────────────────────────
df_weekly.to_csv(OUT_WEEKLY,    index=False)
df_monthly.to_csv(OUT_MONTHLY,  index=False)
df_quarterly.to_csv(OUT_QUARTERLY, index=False)

print(f"\n✅ 已保存:")
print(f"   {OUT_WEEKLY}")
print(f"   {OUT_MONTHLY}")
print(f"   {OUT_QUARTERLY}")

# ── 打印前几行供核验 ─────────────────────────────────────────────────
for label, df_check in [("Weekly", df_weekly), ("Monthly", df_monthly), ("Quarterly", df_quarterly)]:
    print(f"\n--- {label} 前3行 ---")
    print(df_check[['date'] + flow_cols[:4]].head(3).to_string(index=False))