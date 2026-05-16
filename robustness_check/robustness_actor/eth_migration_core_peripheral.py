# 上下两个代码生成的结果是一致的 唯一不同的是下面代码已经把migration和profile生成的文件直接拿来用了 更快
"""
ETH 迁移开发者二分类：Core vs Peripheral
直接读取已生成的两个文件：
  1. eth_actor_role_profile.csv       → stable_actor_id 的角色标签
  2. eth_global_migration_enhanced_all_events.csv → 每条迁移事件

输出：
  eth_daily_migration_core_peripheral.csv
    每天 × 迁移方向（in/out） × 角色（Core/Peripheral） × 来源/目标链
"""
import pandas as pd
import numpy as np

# ============================================================
# 路径配置
# ============================================================
ROLE_PROFILE_PATH  = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_actor_role_profile.csv"
MIGRATION_EVENTS_PATH = "/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_all_events.csv"
OUTPUT_DAILY       = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_daily_migration_core_peripheral.csv"
OUTPUT_DAILY_WIDE  = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_daily_migration_core_peripheral_wide.csv"

# ============================================================
# Step 1: 读取角色画像
# ============================================================
print("=" * 60)
print("Step 1: 读取角色画像")
print("=" * 60)

df_profile = pd.read_csv(ROLE_PROFILE_PATH, low_memory=False)
print(f"行数: {len(df_profile):,}  列: {df_profile.columns.tolist()}")

# 构建 stable_actor_id → role 的映射
role_map = df_profile.set_index('stable_actor_id')['role'].to_dict()
n_core = sum(1 for v in role_map.values() if v == 'Core')
n_peri = sum(1 for v in role_map.values() if v == 'Peripheral')
print(f"角色分布: Core={n_core:,}  Peripheral={n_peri:,}  Total={len(role_map):,}")

# ============================================================
# Step 2: 读取迁移事件
# ============================================================
print("\n" + "=" * 60)
print("Step 2: 读取迁移事件")
print("=" * 60)

df_mig = pd.read_csv(MIGRATION_EVENTS_PATH, low_memory=False)
print(f"行数: {len(df_mig):,}  列: {df_mig.columns.tolist()}")
print(f"event_type唯一值: {df_mig['event_type'].unique()}")

df_mig['date'] = pd.to_datetime(df_mig['date']).dt.date

n_in  = (df_mig['event_type'] == 'inflow').sum()
n_out = (df_mig['event_type'] == 'outflow').sum()
print(f"迁入事件: {n_in:,}  迁出事件: {n_out:,}")

# ============================================================
# Step 3: 匹配角色
# ============================================================
print("\n" + "=" * 60)
print("Step 3: 匹配 user_id → Core/Peripheral")
print("=" * 60)

# migration events 里的 user_id 格式需要和 role_map 的 key 一致
# role_map key 是 stable_actor_id（可能是数字字符串或 login 字符串）
# 先尝试直接匹配，再尝试清洗后匹配
def clean_user_id(x):
    """与 stable_actor_id 生成逻辑保持一致"""
    s = str(x)
    if s in ('nan', 'None', '', '0'):
        return np.nan
    try:
        return str(int(float(s)))
    except Exception:
        return s

df_mig['user_id_clean'] = df_mig['user_id'].apply(clean_user_id)
df_mig['role'] = df_mig['user_id_clean'].map(role_map)

n_matched   = df_mig['role'].notna().sum()
n_unmatched = df_mig['role'].isna().sum()
print(f"匹配成功: {n_matched:,}  未匹配(归 Peripheral): {n_unmatched:,}")

# 未匹配的归 Peripheral（与主数据集处理方式一致）
df_mig['role'] = df_mig['role'].fillna('Peripheral')

print(f"最终 Core 迁移事件:       {(df_mig['role'] == 'Core').sum():,}")
print(f"最终 Peripheral 迁移事件: {(df_mig['role'] == 'Peripheral').sum():,}")

# ============================================================
# Step 4: 按天 × 方向 × 角色 × 链 汇总（长格式）
# ============================================================
print("\n" + "=" * 60)
print("Step 4: 按天汇总（长格式）")
print("=" * 60)

# 对迁入：按 date × role × from_chain 统计
df_in  = df_mig[df_mig['event_type'] == 'inflow'].copy()
df_out = df_mig[df_mig['event_type'] == 'outflow'].copy()

daily_in_long = (
    df_in.groupby(['date', 'role', 'from_chain'])
    .size().reset_index(name='count')
    .rename(columns={'from_chain': 'chain'})
)
daily_in_long['direction'] = 'inflow'

daily_out_long = (
    df_out.groupby(['date', 'role', 'to_chain'])
    .size().reset_index(name='count')
    .rename(columns={'to_chain': 'chain'})
)
daily_out_long['direction'] = 'outflow'

df_long = pd.concat([daily_in_long, daily_out_long], ignore_index=True)
df_long = df_long.sort_values(['date', 'direction', 'role', 'chain']).reset_index(drop=True)

df_long.to_csv(OUTPUT_DAILY, index=False)
print(f"✅ 长格式已保存: {OUTPUT_DAILY}")
print(f"   行数: {len(df_long):,}")

# ============================================================
# Step 5: 生成宽格式（每天一行，列为 Core_in_XXX / Peripheral_in_XXX 等）
# ============================================================
print("\n" + "=" * 60)
print("Step 5: 生成宽格式")
print("=" * 60)

# 构建列名：{role}_{direction}_{chain}，如 Core_inflow_ETH
df_long['col_name'] = (
    df_long['role'] + '_' + df_long['direction'] + '_' + df_long['chain']
)
df_wide = (
    df_long.pivot_table(index='date', columns='col_name', values='count', aggfunc='sum')
    .fillna(0).astype(int)
    .reset_index()
)

# 添加汇总列
core_in_cols  = [c for c in df_wide.columns if c.startswith('Core_inflow_')]
core_out_cols = [c for c in df_wide.columns if c.startswith('Core_outflow_')]
peri_in_cols  = [c for c in df_wide.columns if c.startswith('Peripheral_inflow_')]
peri_out_cols = [c for c in df_wide.columns if c.startswith('Peripheral_outflow_')]

df_wide['Core_total_inflow']       = df_wide[core_in_cols].sum(axis=1)
df_wide['Core_total_outflow']      = df_wide[core_out_cols].sum(axis=1)
df_wide['Peripheral_total_inflow'] = df_wide[peri_in_cols].sum(axis=1)
df_wide['Peripheral_total_outflow']= df_wide[peri_out_cols].sum(axis=1)
df_wide['total_inflow']            = df_wide['Core_total_inflow'] + df_wide['Peripheral_total_inflow']
df_wide['total_outflow']           = df_wide['Core_total_outflow'] + df_wide['Peripheral_total_outflow']

# 列排序：summary列放前面，明细列放后面
summary_cols = ['date',
                'Core_total_inflow', 'Core_total_outflow',
                'Peripheral_total_inflow', 'Peripheral_total_outflow',
                'total_inflow', 'total_outflow']
detail_cols  = sorted([c for c in df_wide.columns if c not in summary_cols])
df_wide = df_wide[summary_cols + detail_cols]

df_wide = df_wide.sort_values('date').reset_index(drop=True)
df_wide.to_csv(OUTPUT_DAILY_WIDE, index=False)
print(f"✅ 宽格式已保存: {OUTPUT_DAILY_WIDE}")
print(f"   行数: {len(df_wide):,}  列数: {len(df_wide.columns):,}")

# ============================================================
# Step 5b: 拆分为 Core / Peripheral 两张表
#          列名还原为原始 eth_global_migration_enhanced_daily 格式
#          即: in_from_XXX / out_to_XXX + total_in / total_out
# ============================================================
print("\n" + "=" * 60)
print("Step 5b: 拆分 Core / Peripheral 并还原列名")
print("=" * 60)

def build_role_table(df_wide, role, all_chains_in, all_chains_out):
    """
    从宽格式中提取指定角色的迁入/迁出列，
    把列名从 {role}_inflow_{chain} 还原为 in_from_{chain} / out_to_{chain}
    """
    rename_map = {}
    for chain in all_chains_in:
        old = f"{role}_inflow_{chain}"
        if old in df_wide.columns:
            rename_map[old] = f"in_from_{chain}"
    for chain in all_chains_out:
        old = f"{role}_outflow_{chain}"
        if old in df_wide.columns:
            rename_map[old] = f"out_to_{chain}"

    cols_to_keep = ['date'] + list(rename_map.keys())
    df_role = df_wide[cols_to_keep].rename(columns=rename_map).copy()

    # 还原 total_in / total_out 汇总列
    in_cols  = [c for c in df_role.columns if c.startswith('in_from_')]
    out_cols = [c for c in df_role.columns if c.startswith('out_to_')]
    df_role['total_in']  = df_role[in_cols].sum(axis=1)
    df_role['total_out'] = df_role[out_cols].sum(axis=1)

    # 列排序：date, total_in, total_out, in_from_*, out_to_*
    front = ['date', 'total_in', 'total_out']
    rest  = sorted(in_cols) + sorted(out_cols)
    return df_role[front + rest].sort_values('date').reset_index(drop=True)

# 获取所有出现过的链名
all_chains_in  = sorted(set(
    c.replace('Core_inflow_', '').replace('Peripheral_inflow_', '')
    for c in df_wide.columns
    if '_inflow_' in c and not c.endswith('_inflow')
    and not c.startswith('total') and not c.startswith('Core_total')
    and not c.startswith('Peripheral_total')
))
all_chains_out = sorted(set(
    c.replace('Core_outflow_', '').replace('Peripheral_outflow_', '')
    for c in df_wide.columns
    if '_outflow_' in c and not c.endswith('_outflow')
    and not c.startswith('total') and not c.startswith('Core_total')
    and not c.startswith('Peripheral_total')
))

# 也可以直接从 detail_cols 解析，更健壮
all_chains_in  = sorted(set(
    c.split('_inflow_', 1)[1]
    for c in df_wide.columns if '_inflow_' in c
    and not c.startswith('total') and not c.endswith('inflow')
))
all_chains_out = sorted(set(
    c.split('_outflow_', 1)[1]
    for c in df_wide.columns if '_outflow_' in c
    and not c.startswith('total') and not c.endswith('outflow')
))

df_core = build_role_table(df_wide, 'Core', all_chains_in, all_chains_out)
df_peri = build_role_table(df_wide, 'Peripheral', all_chains_in, all_chains_out)

OUTPUT_CORE = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_migration_core_daily.csv"
OUTPUT_PERI = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/eth_migration_peripheral_daily.csv"

df_core.to_csv(OUTPUT_CORE, index=False)
df_peri.to_csv(OUTPUT_PERI, index=False)

print(f"✅ Core 迁移表已保存:       {OUTPUT_CORE}")
print(f"   行数: {len(df_core):,}  列数: {len(df_core.columns):,}")
print(f"✅ Peripheral 迁移表已保存: {OUTPUT_PERI}")
print(f"   行数: {len(df_peri):,}  列数: {len(df_peri.columns):,}")
print(f"\nCore 表列名:       {df_core.columns.tolist()}")
print(f"Peripheral 表列名: {df_peri.columns.tolist()}")

# ============================================================
# Step 6: 校验 + 汇总
# ============================================================
print("\n" + "=" * 60)
print("Step 6: 校验与汇总")
print("=" * 60)

# 校验：Core + Peripheral 每日合计应等于原始迁移事件总计
orig_daily_in  = df_in.groupby('date').size().rename('orig_in')
orig_daily_out = df_out.groupby('date').size().rename('orig_out')

check_in = (
    df_wide.set_index('date')['total_inflow']
    .compare(orig_daily_in.reindex(df_wide['date'].values).fillna(0).astype(int))
)
check_out = (
    df_wide.set_index('date')['total_outflow']
    .compare(orig_daily_out.reindex(df_wide['date'].values).fillna(0).astype(int))
)

if check_in.empty and check_out.empty:
    print("✅ 校验通过：Core + Peripheral 合计 = 原始迁移事件总计")
else:
    print(f"⚠️  迁入差异行数: {len(check_in)}  迁出差异行数: {len(check_out)}")

print(f"\n全期汇总:")
print(f"  Core    迁入总计: {df_wide['Core_total_inflow'].sum():,}")
print(f"  Core    迁出总计: {df_wide['Core_total_outflow'].sum():,}")
print(f"  Peripheral 迁入总计: {df_wide['Peripheral_total_inflow'].sum():,}")
print(f"  Peripheral 迁出总计: {df_wide['Peripheral_total_outflow'].sum():,}")

print(f"\n宽格式前5行预览:")
print(df_wide[summary_cols].head().to_string(index=False))

print("\n" + "=" * 60)
print("✅ 全部完成！输出文件：")
print(f"  长格式: {OUTPUT_DAILY}")
print(f"  宽格式: {OUTPUT_DAILY_WIDE}")
print("=" * 60)