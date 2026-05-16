# """
# BTC Developer Migration Classification: Core vs Peripheral
# 结合开发者角色分类 + 跨链迁移事件
# 生成每天Core/Peripheral开发者的迁入迁出数据
# """
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import os

# # ===================================================================
# # 路径配置
# # ===================================================================
# EVENT_LOG_PATH   = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all_2025_12_31.csv"
# FIRST_ACTOR_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_full_event_timeline_event_2025_12_31.csv"
# ACTOR_PROFILE    = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_actor_role_profile.csv"

# # 所有竞争链事件文件
# BTC_PATH  = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all_2025_12_31.csv"
# ETH_PATH  = "/home/lab0/survival_diffusion_github/Ethereum/eth_events_timeline_unified_all_2025_12_31.csv"
# CHAINS_FORMAT1 = ['bitcoincash','bitcoinsv','bitcoingpu','bitcoincashnode','parity',
#                   'lightningnetwork','rootstock','stacks','bob','zcash','solana','tron','bnb']
# CHAINS_FORMAT2 = ['lbtc','btcd','bcoin','litecoin','dogecoin','monero']

# OUT_DIR = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/"
# os.makedirs(OUT_DIR, exist_ok=True)

# OUTPUT_MIGRATION_CLASSIFIED = OUT_DIR + "btc_migration_classified.csv"
# OUTPUT_DAILY_CORE           = OUT_DIR + "btc_daily_migration_core.csv"
# OUTPUT_DAILY_PERIPHERAL     = OUT_DIR + "btc_daily_migration_peripheral.csv"
# OUTPUT_DAILY_COMBINED       = OUT_DIR + "btc_daily_migration_core_peripheral.csv"

# CORE_EVENTS = {
#     'PushEvent','PullRequestEvent','PullRequestReviewEvent',
#     'PullRequestReviewCommentEvent','CommitCommentEvent',
#     'ReleaseEvent','CreateEvent','DeleteEvent','Event'
# }
# PERIPHERAL_EVENTS = {
#     'ForkEvent','IssuesEvent','IssueCommentEvent','WatchEvent',
#     'MemberEvent','PublicEvent','GollumEvent','SponsorshipEvent',
#     'DownloadEvent','DiscussionEvent'
# }

# CUTOFF_DATE          = datetime(2025, 12, 31).date()
# PERMANENT_EXIT_DAYS  = 90

# # ===================================================================
# # Step 1: 加载或生成 actor 角色映射
# # ===================================================================
# print("="*70)
# print("Step 1: 加载 actor 角色映射")
# print("="*70)

# if os.path.exists(ACTOR_PROFILE):
#     print(f"  直接加载已有画像: {ACTOR_PROFILE}")
#     actor_profile = pd.read_csv(ACTOR_PROFILE, low_memory=False)
# else:
#     print("  画像文件不存在，重新生成...")
#     df_events = pd.read_csv(EVENT_LOG_PATH, low_memory=False)
#     df_events['event_category'] = df_events['event_type'].apply(
#         lambda x: 'core' if x in CORE_EVENTS
#                   else ('peripheral' if x in PERIPHERAL_EVENTS else 'unknown'))
#     df_valid = df_events[df_events['event_category'] != 'unknown'].copy()
#     df_valid['actor_id_clean'] = df_valid['actor_id'].apply(
#         lambda x: str(int(float(x)))
#         if str(x) not in ('nan','None','','0') else np.nan)
#     df_valid['stable_actor_id'] = df_valid['actor_id_clean'].combine_first(df_valid['actor_login'])
#     counts = (df_valid.groupby(['stable_actor_id','event_category'])
#               .size().unstack(fill_value=0).reset_index())
#     for col in ['core','peripheral']:
#         if col not in counts.columns:
#             counts[col] = 0
#     counts['total_events'] = counts['core'] + counts['peripheral']
#     counts['core_ratio']   = (counts['core'] / counts['total_events']).round(4)
#     counts['role'] = counts.apply(
#         lambda r: 'Core' if (r['core'] > 0 and r['core_ratio'] >= 0.1) else 'Peripheral', axis=1)
#     actor_profile = counts[['stable_actor_id','role','core','peripheral',
#                              'total_events','core_ratio']]
#     actor_profile.to_csv(ACTOR_PROFILE, index=False)

# # 构建 stable_actor_id → role 映射
# role_map = actor_profile.set_index('stable_actor_id')['role'].to_dict()
# n_core = sum(1 for v in role_map.values() if v == 'Core')
# n_peri = sum(1 for v in role_map.values() if v == 'Peripheral')
# print(f"  画像总数: {len(role_map):,}  Core: {n_core:,}  Peripheral: {n_peri:,}")

# # ===================================================================
# # Step 2: 加载所有链的事件数据
# # ===================================================================
# print("\n" + "="*70)
# print("Step 2: 加载所有链的事件数据")
# print("="*70)

# PROJECT_LABELS = {BTC_PATH: 'BTC', ETH_PATH: 'ETH'}
# for chain in CHAINS_FORMAT1:
#     p = f"/home/lab0/survival_diffusion_github/Bitcoin/{chain}_events_all_2025_12_31.csv"
#     PROJECT_LABELS[p] = chain.upper() if len(chain) <= 5 else chain.replace('_','').title()
# for chain in CHAINS_FORMAT2:
#     p = f"/home/lab0/survival_diffusion_github/Bitcoin/{chain}_events_timeline_unified_all_2025_12_31.csv"
#     PROJECT_LABELS[p] = chain.upper() if len(chain) <= 5 else chain.capitalize()

# dfs = []
# for path, label in PROJECT_LABELS.items():
#     if not os.path.exists(path):
#         print(f"  ⚠️  {label} 文件不存在，跳过")
#         continue
#     df = pd.read_csv(path, low_memory=False)
#     df['project'] = label
#     dfs.append(df)
#     print(f"  ✅ {label:<20} {len(df):>10,} 条")

# df_all = pd.concat(dfs, ignore_index=True)
# df_all['created_at'] = pd.to_datetime(df_all['created_at'])
# df_all['user_id'] = df_all['actor_id'].fillna(df_all['actor_login'])
# df_all = df_all.sort_values(['user_id','created_at']).reset_index(drop=True)
# print(f"\n  合并后总记录: {len(df_all):,}  唯一用户: {df_all['user_id'].nunique():,}")

# # ===================================================================
# # Step 3: 生成跨链迁移路径（复用原有逻辑）
# # ===================================================================
# print("\n" + "="*70)
# print("Step 3: 生成跨链迁移路径")
# print("="*70)

# def get_migration_sequence(group):
#     seq = group.sort_values('created_at')
#     projects = seq['project'].tolist()
#     times    = seq['created_at'].tolist()
#     clean_p, clean_t, prev = [], [], None
#     for p, t in zip(projects, times):
#         if p != prev:
#             clean_p.append(p); clean_t.append(t); prev = p
#     return pd.Series({
#         'path_detail': list(zip(clean_p, clean_t)),
#         'path_str':    '-'.join(clean_p),
#     })

# user_paths = df_all.groupby('user_id').apply(get_migration_sequence).reset_index()
# btc_users  = user_paths[user_paths['path_str'].str.contains('BTC', na=False)].copy()
# print(f"  含BTC路径的用户: {len(btc_users):,}")

# # ===================================================================
# # Step 4: 提取迁入/迁出事件 + 打角色标签
# # ===================================================================
# print("\n" + "="*70)
# print("Step 4: 提取迁入/迁出事件并打角色标签")
# print("="*70)

# # ---- 4a: 构建 user_id → stable_actor_id 映射 ----
# # 从 bitcoin_first_actor 文件获取 user_id 与 stable_actor_id 的对应关系
# df_first = pd.read_csv(FIRST_ACTOR_PATH, low_memory=False)
# df_first['actor_id_clean'] = df_first['actor_id'].apply(
#     lambda x: str(int(float(x)))
#     if str(x) not in ('nan','None','','0') else np.nan) \
#     if 'actor_id' in df_first.columns else np.nan

# # user_id 在迁移代码中 = actor_id（原始值）或 actor_login
# # stable_actor_id 在分类代码中 = int(actor_id) 字符串 or actor_login
# # 构建映射：原始 actor_id → stable_actor_id（用于角色查找）
# def to_stable_id(raw_id):
#     """将原始 user_id 转换为 stable_actor_id 格式"""
#     s = str(raw_id)
#     try:
#         return str(int(float(s)))
#     except (ValueError, OverflowError):
#         return s  # 是 login 字符串

# # ---- 4b: 提取迁入/迁出 ----
# migration_events = []
# for _, row in btc_users.iterrows():
#     user   = row['user_id']
#     detail = row['path_detail']
#     if not detail:
#         continue

#     projects = [p for p, _ in detail]
#     times    = [t for _, t in detail]
#     btc_idx  = [i for i, p in enumerate(projects) if p == 'BTC']
#     if not btc_idx:
#         continue

#     # 角色查找：将 user_id 转换为 stable_actor_id 格式
#     stable_id = to_stable_id(user)
#     role = role_map.get(stable_id, 'Peripheral')  # 未匹配默认 Peripheral

#     # 迁入：首次进入 BTC 前有其他链
#     first_btc = btc_idx[0]
#     if first_btc > 0:
#         prev_proj = projects[first_btc - 1]
#         in_date   = times[first_btc].date()
#         migration_events.append({
#             'user_id':    user,
#             'stable_id':  stable_id,
#             'role':       role,
#             'type':       f'in_from_{prev_proj}',
#             'from_chain': prev_proj,
#             'to_chain':   'BTC',
#             'date':       in_date,
#             'event_type': 'inflow',
#         })

#     # 迁出：最后一个 BTC 之后有其他链，且距截止日 ≥ 90 天
#     last_btc = btc_idx[-1]
#     if last_btc < len(projects) - 1:
#         next_proj = projects[last_btc + 1]
#         out_date  = times[last_btc + 1].date()
#         if (CUTOFF_DATE - out_date).days >= PERMANENT_EXIT_DAYS:
#             migration_events.append({
#                 'user_id':    user,
#                 'stable_id':  stable_id,
#                 'role':       role,
#                 'type':       f'out_to_{next_proj}',
#                 'from_chain': 'BTC',
#                 'to_chain':   next_proj,
#                 'date':       out_date,
#                 'event_type': 'outflow',
#             })

# df_mig = pd.DataFrame(migration_events)
# if not df_mig.empty:
#     df_mig = df_mig.drop_duplicates(subset=['user_id','type','date'])

# print(f"  迁入事件: {len(df_mig[df_mig['event_type']=='inflow']):,}")
# print(f"  迁出事件: {len(df_mig[df_mig['event_type']=='outflow']):,}")
# print(f"  Core迁移事件:       {len(df_mig[df_mig['role']=='Core']):,}")
# print(f"  Peripheral迁移事件: {len(df_mig[df_mig['role']=='Peripheral']):,}")

# df_mig.to_csv(OUTPUT_MIGRATION_CLASSIFIED, index=False)
# print(f"\n  ✅ 分类迁移事件已保存: {OUTPUT_MIGRATION_CLASSIFIED}")

# # ===================================================================
# # Step 5: 按天、按链、按角色汇总
# # ===================================================================
# print("\n" + "="*70)
# print("Step 5: 按天、按链、按角色汇总")
# print("="*70)

# def build_daily_pivot(df_role, role_name):
#     """为某个角色构建每日迁入迁出宽表"""
#     if df_role.empty:
#         return pd.DataFrame()

#     df_in  = df_role[df_role['event_type'] == 'inflow']
#     df_out = df_role[df_role['event_type'] == 'outflow']

#     # 迁入宽表
#     if not df_in.empty:
#         daily_in = (df_in.groupby(['date','type']).size()
#                     .unstack(fill_value=0))
#         daily_in['total_in'] = daily_in.sum(axis=1)
#     else:
#         daily_in = pd.DataFrame()

#     # 迁出宽表
#     if not df_out.empty:
#         daily_out = (df_out.groupby(['date','type']).size()
#                      .unstack(fill_value=0))
#         daily_out['total_out'] = daily_out.sum(axis=1)
#     else:
#         daily_out = pd.DataFrame()

#     if not daily_in.empty and not daily_out.empty:
#         daily = pd.concat([daily_in, daily_out], axis=1).fillna(0).astype(int)
#     elif not daily_in.empty:
#         daily = daily_in.fillna(0).astype(int)
#     elif not daily_out.empty:
#         daily = daily_out.fillna(0).astype(int)
#     else:
#         return pd.DataFrame()

#     daily = daily.sort_index().reset_index()
#     daily.insert(0, 'role', role_name)
#     return daily

# # 分别构建 Core 和 Peripheral 的日表
# df_core_mig = df_mig[df_mig['role'] == 'Core']
# df_peri_mig = df_mig[df_mig['role'] == 'Peripheral']

# daily_core = build_daily_pivot(df_core_mig, 'Core')
# daily_peri = build_daily_pivot(df_peri_mig, 'Peripheral')

# # 保存各自的文件
# if not daily_core.empty:
#     daily_core.to_csv(OUTPUT_DAILY_CORE, index=False)
#     print(f"  ✅ Core迁移日表已保存: {OUTPUT_DAILY_CORE}")
#     print(f"     行数: {len(daily_core):,}  列数: {len(daily_core.columns)}")
# else:
#     print("  ⚠️  Core 无迁移数据")

# if not daily_peri.empty:
#     daily_peri.to_csv(OUTPUT_DAILY_PERIPHERAL, index=False)
#     print(f"  ✅ Peripheral迁移日表已保存: {OUTPUT_DAILY_PERIPHERAL}")
#     print(f"     行数: {len(daily_peri):,}  列数: {len(daily_peri.columns)}")
# else:
#     print("  ⚠️  Peripheral 无迁移数据")

# # 合并表（长格式，role列区分）
# if not daily_core.empty or not daily_peri.empty:
#     parts = [x for x in [daily_core, daily_peri] if not x.empty]
#     daily_combined = pd.concat(parts, ignore_index=True).fillna(0)
#     # 将整数列转回 int
#     int_cols = [c for c in daily_combined.columns if c not in ['date','role']]
#     daily_combined[int_cols] = daily_combined[int_cols].astype(int)
#     daily_combined.to_csv(OUTPUT_DAILY_COMBINED, index=False)
#     print(f"\n  ✅ 合并宽表已保存: {OUTPUT_DAILY_COMBINED}")

# # ===================================================================
# # Step 6: 校验 + 汇总诊断
# # ===================================================================
# print("\n" + "="*70)
# print("Step 6: 校验与诊断")
# print("="*70)

# if not df_mig.empty:
#     # 按角色统计
#     print("\n  角色分布:")
#     for role in ['Core','Peripheral']:
#         sub = df_mig[df_mig['role'] == role]
#         n_in  = len(sub[sub['event_type'] == 'inflow'])
#         n_out = len(sub[sub['event_type'] == 'outflow'])
#         print(f"    {role:<12}: 迁入 {n_in:>6,}  迁出 {n_out:>6,}")

#     # 校验：Core + Peripheral = 总迁移
#     total_in  = len(df_mig[df_mig['event_type'] == 'inflow'])
#     total_out = len(df_mig[df_mig['event_type'] == 'outflow'])
#     core_in   = len(df_core_mig[df_core_mig['event_type'] == 'inflow'])
#     peri_in   = len(df_peri_mig[df_peri_mig['event_type'] == 'inflow'])
#     core_out  = len(df_core_mig[df_core_mig['event_type'] == 'outflow'])
#     peri_out  = len(df_peri_mig[df_peri_mig['event_type'] == 'outflow'])

#     assert core_in + peri_in == total_in,   "⚠️ 迁入校验失败"
#     assert core_out + peri_out == total_out, "⚠️ 迁出校验失败"
#     print(f"\n  ✅ 校验通过: Core+Peripheral = 总迁移事件")

#     # 迁入来源 Top5
#     print("\n  迁入来源 Top 5:")
#     for role in ['Core','Peripheral']:
#         sub = df_mig[(df_mig['role']==role) & (df_mig['event_type']=='inflow')]
#         if not sub.empty:
#             top = sub['from_chain'].value_counts().head(5)
#             print(f"    [{role}]")
#             for chain, cnt in top.items():
#                 print(f"      从 {chain:<15}: {cnt:>5,}")

#     # 迁出目标 Top5
#     print("\n  迁出目标 Top 5:")
#     for role in ['Core','Peripheral']:
#         sub = df_mig[(df_mig['role']==role) & (df_mig['event_type']=='outflow')]
#         if not sub.empty:
#             top = sub['to_chain'].value_counts().head(5)
#             print(f"    [{role}]")
#             for chain, cnt in top.items():
#                 print(f"      迁出到 {chain:<15}: {cnt:>5,}")

# print("\n" + "="*70)
# print("🎉 完成！输出文件:")
# print(f"  {OUTPUT_MIGRATION_CLASSIFIED}")
# print(f"  {OUTPUT_DAILY_CORE}")
# print(f"  {OUTPUT_DAILY_PERIPHERAL}")
# print(f"  {OUTPUT_DAILY_COMBINED}")
# print("="*70)


# 上下两个代码生成的结果是一致的 唯一不同的是下面代码已经把migration和profile生成的文件直接拿来用了 更快
"""
BTC 迁移开发者二分类：Core vs Peripheral
直接读取已生成的两个文件：
  1. btc_actor_role_profile.csv       → stable_actor_id 的角色标签
  2. btc_global_migration_enhanced_all_events.csv → 每条迁移事件

输出：
  btc_daily_migration_core_peripheral.csv
    每天 × 迁移方向（in/out） × 角色（Core/Peripheral） × 来源/目标链
"""
import pandas as pd
import numpy as np

# ============================================================
# 路径配置
# ============================================================
ROLE_PROFILE_PATH  = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_actor_role_profile.csv"
MIGRATION_EVENTS_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_all_events.csv"
OUTPUT_DAILY       = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_daily_migration_core_peripheral.csv"
OUTPUT_DAILY_WIDE  = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_daily_migration_core_peripheral_wide.csv"

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
#          列名还原为原始 btc_global_migration_enhanced_daily 格式
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

OUTPUT_CORE = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_migration_core_daily.csv"
OUTPUT_PERI = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_migration_peripheral_daily.csv"

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