# 写python代码不仅看event type吧 首先在/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all_2025_12_31.csv要确定哪些是core event type 哪些是边缘 event type（event分成两类）CORE_EVENTS = {
#     'PushEvent',
#     'PullRequestEvent',
#     'PullRequestReviewEvent',
#     'PullRequestReviewCommentEvent',
#     'CommitCommentEvent',
#     'ReleaseEvent',
#     'CreateEvent',
#     'DeleteEvent',
# }

# PERIPHERAL_EVENTS = {
#     'ForkEvent',
#     'IssuesEvent',
#     'IssueCommentEvent',
#     'WatchEvent',
#     'MemberEvent',
#     'PublicEvent',
#     'GollumEvent',         # wiki编辑
#     'SponsorshipEvent',
# }；其次确定每个stable_actor_id字段详细的event type（比如createevent prevent ）类型的计算和分布；然后确定每个人core event和边缘event type两个类型的event type数量和频率；然后设置阈值来确定core和边缘（core_ratio = core_events / total_events；core_ratio ≥ 0.5）；然后将actor_id和她的标签映射到每天新增的stable_actor_id字段【/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_full_event_timeline_event_2025_12_31.csv】中，这样就可以算到每天新增的不同类型actor_id的数量，确保每天新增的core+边缘人数加起来等于每天新增的总人数【即相同日期记录的总数】

"""
BTC Developer Classification: Core vs Peripheral
基于全历史event画像，将每个stable_actor_id分类为Core或Peripheral
然后映射到每天新增开发者数据中
"""

"""
BTC Developer Classification: Core vs Peripheral
基于全历史event画像，将每个actor分类为Core或Peripheral
然后映射到每天新增开发者数据中
"""

"""
BTC Developer Classification: Core vs Peripheral
基于全历史event画像分类，映射到每天新增数据
修复：event log用actor_id+actor_login双字段匹配stable_actor_id
"""

"""
BTC Developer Classification: Core vs Peripheral
基于全历史event画像分类，映射到每天新增数据
修复：event log用actor_id+actor_login双字段匹配stable_actor_id
"""

"""
BTC Developer Classification: Core vs Peripheral
基于全历史event画像分类，映射到每天新增数据
修复：event log用actor_id+actor_login双字段匹配stable_actor_id
"""

"""
BTC Developer Classification: Core vs Peripheral
基于全历史event画像分类，映射到每天新增数据
修复：event log用actor_id+actor_login双字段匹配stable_actor_id
"""

import pandas as pd
import numpy as np

# ============================================================
# 路径配置
# ============================================================
EVENT_LOG_PATH   = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all_2025_12_31.csv"
FIRST_ACTOR_PATH = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_first_actor_full_event_timeline_event_2025_12_31.csv"
OUTPUT_PROFILE   = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_actor_role_profile.csv"
OUTPUT_DAILY     = "/home/lab0/survival_diffusion_github/robustness_check/robustness_actor/btc_daily_new_core_peripheral.csv"

CORE_EVENTS = {
    'PushEvent','PullRequestEvent','PullRequestReviewEvent',
    'PullRequestReviewCommentEvent','CommitCommentEvent',
    'ReleaseEvent','CreateEvent','DeleteEvent','Event'
}
PERIPHERAL_EVENTS = {
    'ForkEvent','IssuesEvent','IssueCommentEvent','WatchEvent',
    'MemberEvent','PublicEvent','GollumEvent','SponsorshipEvent','DownloadEvent','DiscussionEvent'
}

# ============================================================
# Step 1: 读取event log
# ============================================================
print("=" * 60)
print("Step 1: 读取全量event log")
print("=" * 60)

df_events = pd.read_csv(EVENT_LOG_PATH, low_memory=False)
print(f"行数: {len(df_events):,}  列: {df_events.columns.tolist()}")

# ============================================================
# Step 2: event type分布
# ============================================================
print("\n" + "=" * 60)
print("Step 2: event type分布")
print("=" * 60)

event_dist = df_events['event_type'].value_counts().reset_index()
event_dist.columns = ['event_type', 'count']
event_dist['pct'] = (event_dist['count'] / event_dist['count'].sum() * 100).round(2)
event_dist['category'] = event_dist['event_type'].apply(
    lambda x: 'CORE' if x in CORE_EVENTS else ('PERIPHERAL' if x in PERIPHERAL_EVENTS else 'UNKNOWN')
)
print(event_dist.to_string(index=False))

# ============================================================
# Step 3: 画像 —— 关键修复：用actor_id和actor_login双索引
# ============================================================
print("\n" + "=" * 60)
print("Step 3: 全历史画像（双索引匹配）")
print("=" * 60)

df_events['event_category'] = df_events['event_type'].apply(
    lambda x: 'core' if x in CORE_EVENTS else ('peripheral' if x in PERIPHERAL_EVENTS else 'unknown')
)
df_valid = df_events[df_events['event_category'] != 'unknown'].copy()

# 与生成stable_actor_id的逻辑完全对称：
# 有actor_id → 用actor_id（去掉.0后的整数字符串）
# 没有actor_id → 用actor_login
df_valid['actor_id_clean'] = (
    df_valid['actor_id']
    .apply(lambda x: str(int(float(x))) if str(x) not in ('nan', 'None', '', '0') else np.nan)
)
df_valid['stable_actor_id'] = df_valid['actor_id_clean'].combine_first(df_valid['actor_login'])

# 按stable_actor_id统计core/peripheral
counts_by_id = (
    df_valid.groupby(['stable_actor_id', 'event_category'])
    .size().unstack(fill_value=0).reset_index()
)
for col in ['core', 'peripheral']:
    if col not in counts_by_id.columns:
        counts_by_id[col] = 0

print(f"画像actor数: {len(counts_by_id):,}")
print(f"stable_actor_id样本: {counts_by_id['stable_actor_id'].head(8).tolist()}")

# ============================================================
# Step 4: 打标签
# ============================================================
print("\n" + "=" * 60)
print("Step 4: 打标签（有任意Core event → Core）")
print("=" * 60)

counts_by_id['total_events']     = counts_by_id['core'] + counts_by_id['peripheral']
counts_by_id['core_ratio']       = (counts_by_id['core'] / counts_by_id['total_events']).round(4)
counts_by_id['role'] = counts_by_id.apply(
    lambda r: 'Core' if (r['core'] > 0 and r['core_ratio'] >= 0.1) else 'Peripheral', axis=1
)

# 备用方案A: core_count > peripheral_count
# counts_by_id['role'] = counts_by_id.apply(
#     lambda r: 'Core' if r['core'] > r['peripheral'] else 'Peripheral', axis=1)

# 备用方案B: core_ratio >= 0.3
# counts_by_id['role'] = counts_by_id['core_ratio'].apply(
#     lambda r: 'Core' if r >= 0.3 else 'Peripheral')

n_core  = (counts_by_id['role'] == 'Core').sum()
n_peri  = (counts_by_id['role'] == 'Peripheral').sum()
n_total = len(counts_by_id)
print(f"总actor: {n_total:,}  Core: {n_core:,} ({n_core/n_total*100:.1f}%)  Peripheral: {n_peri:,} ({n_peri/n_total*100:.1f}%)")

# 每个actor × 具体event_type 的计数（细粒度分布）
actor_event_detail = (
    df_valid.groupby(['stable_actor_id', 'event_type'])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# 确保所有已知event type列都存在（无记录的补0）
all_known_events = sorted(CORE_EVENTS | PERIPHERAL_EVENTS)
for ev in all_known_events:
    if ev not in actor_event_detail.columns:
        actor_event_detail[ev] = 0

# 列排序：先Core events，再Peripheral events
core_cols = sorted([e for e in CORE_EVENTS if e in actor_event_detail.columns])
peri_cols = sorted([e for e in PERIPHERAL_EVENTS if e in actor_event_detail.columns])
actor_event_detail = actor_event_detail[['stable_actor_id'] + core_cols + peri_cols]

# 合并：汇总统计 + 细粒度event type计数 + 角色标签
actor_profile = (
    counts_by_id
    .merge(actor_event_detail, on='stable_actor_id', how='left')
)

# 列顺序：stable_actor_id, role, core, peripheral, core_ratio, total_events, 各event type...
front_cols = ['stable_actor_id', 'role', 'core', 'peripheral', 'total_events', 'core_ratio']
remaining  = [c for c in actor_profile.columns if c not in front_cols]
actor_profile = actor_profile[front_cols + remaining]

actor_profile.to_csv(OUTPUT_PROFILE, index=False)
print(f"✅ 画像已保存: {OUTPUT_PROFILE}")
print(f"   列数: {len(actor_profile.columns)}  "
      f"（包含 {len(core_cols)} 个Core event列 + {len(peri_cols)} 个Peripheral event列）")
print(f"   列名: {actor_profile.columns.tolist()}")

# ============================================================
# Step 5: 读取每日新增 + 双路匹配
# ============================================================
print("\n" + "=" * 60)
print("Step 5: 映射到每天新增数据")
print("=" * 60)

df_daily = pd.read_csv(FIRST_ACTOR_PATH, low_memory=False)
print(f"行数: {len(df_daily):,}  列: {df_daily.columns.tolist()}")
print(f"stable_actor_id样本: {df_daily['stable_actor_id'].head(8).tolist()}")

# 日期处理
df_daily['created_at'] = pd.to_datetime(df_daily['created_at']).dt.date

# stable_actor_id是混合的：数字字符串 or login字符串
# 构建两张查找表：
#   map1: actor_id（str） → role
#   map2: actor_login（str） → role
# 两个文件的stable_actor_id生成逻辑完全一致，直接单路匹配
role_map = counts_by_id.set_index('stable_actor_id')['role']
df_daily['role'] = df_daily['stable_actor_id'].astype(str).map(role_map)

n_matched   = df_daily['role'].notna().sum()
n_unmatched = df_daily['role'].isna().sum()
print(f"\n匹配成功: {n_matched:,}  未匹配(归Peripheral): {n_unmatched:,}")
df_daily['role'] = df_daily['role'].fillna('Peripheral')

# 匹配后Core数量确认
print(f"匹配后Core行数: {(df_daily['role']=='Core').sum():,}")
print(f"匹配后Peripheral行数: {(df_daily['role']=='Peripheral').sum():,}")

# ============================================================
# Step 6: 按天汇总 + 校验
# ============================================================
print("\n" + "=" * 60)
print("Step 6: 按天汇总并校验")
print("=" * 60)

daily_counts = (
    df_daily.groupby(['created_at', 'role'])
    .size().unstack(fill_value=0).reset_index()
    .rename(columns={'created_at': 'date'})
)
for col in ['Core', 'Peripheral']:
    if col not in daily_counts.columns:
        daily_counts[col] = 0

daily_counts = daily_counts.sort_values('date').reset_index(drop=True)
daily_counts['total_new_classified'] = daily_counts['Core'] + daily_counts['Peripheral']

original_total = (
    df_daily.groupby('created_at').size()
    .rename('total_new_original').reset_index()
    .rename(columns={'created_at': 'date'})
)
daily_counts = daily_counts.merge(original_total, on='date', how='left')

mismatch = (daily_counts['total_new_classified'] != daily_counts['total_new_original']).sum()
if mismatch == 0:
    print("✅ 校验通过：Core + Peripheral = 原始新增总人数")
else:
    print(f"⚠️  {mismatch} 天存在差异")

daily_counts['cum_Core']       = daily_counts['Core'].cumsum()
daily_counts['cum_Peripheral'] = daily_counts['Peripheral'].cumsum()
daily_counts['cum_total']      = daily_counts['total_new_classified'].cumsum()

daily_counts = daily_counts[[
    'date','Core','Peripheral',
    'total_new_classified','total_new_original',
    'cum_Core','cum_Peripheral','cum_total'
]]
daily_counts.to_csv(OUTPUT_DAILY, index=False)
print(f"✅ 每日分类新增已保存: {OUTPUT_DAILY}")

# ============================================================
# Step 7: 汇总
# ============================================================
print("\n" + "=" * 60)
print("Step 7: 汇总统计")
print("=" * 60)
print(f"全期Core新增:       {daily_counts['Core'].sum():,}")
print(f"全期Peripheral新增: {daily_counts['Peripheral'].sum():,}")
print(f"全期新增总数:       {daily_counts['total_new_classified'].sum():,}")
print(f"\n前10天预览:")
print(daily_counts.head(10).to_string(index=False))