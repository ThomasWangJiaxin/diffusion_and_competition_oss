# 区分核心和边缘开发者
# 区分核心和边缘开发者并输出每日汇总统计
import pandas as pd
from datetime import timedelta

# 路径
path = "/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_all.csv"

# 读取并预处理
df = pd.read_csv(path)
df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
df = df.dropna(subset=['actor_id', 'created_at'])
df['date'] = df['created_at'].dt.date

# Step 1️⃣ 每个 actor 的首次事件记录
first_event = (
    df.sort_values('created_at')
      .groupby('actor_id', as_index=False)
      .first()
      [['actor_id', 'created_at', 'event_type']]
      .rename(columns={'created_at': 'first_event_time', 'event_type': 'first_event_type'})
)
first_event['first_event_date'] = first_event['first_event_time'].dt.date

# Step 2️⃣ 每个 actor 的总体特征（活跃统计 + 时间跨度）
agg_features = (
    df.groupby('actor_id')
      .agg(
          total_events=('id', 'count'),
          first_date=('created_at', 'min'),
          last_date=('created_at', 'max'),
      )
      .assign(active_days=lambda x: (x['last_date'] - x['first_date']).dt.days + 1)
)

# Step 3️⃣ 每个 actor 的事件类型分布
event_dist = (
    df.groupby(['actor_id', 'event_type'])
      .size()
      .unstack(fill_value=0)
      .add_prefix('count_')
)

# Step 4️⃣ 合并所有特征
actor_features = (
    first_event
    .merge(agg_features, on='actor_id')
    .merge(event_dist, on='actor_id', how='left')
)

# Step 5️⃣ 定义核心/边缘分类规则
def classify_actor(row):
    if row['total_events'] > 50 and row['active_days'] > 30:
        return 'core'
    else:
        return 'peripheral'

actor_features['actor_type'] = actor_features.apply(classify_actor, axis=1)

# Step 6️⃣ 生成每日新增用户表
actor_features = actor_features.sort_values('first_event_time')
out_path_detail = "/home/lab0/survival_diffusion_github/Bitcoin/actor_features_by_day.csv"
actor_features.to_csv(out_path_detail, index=False)

# Step 7️⃣ 生成每日汇总表
daily_summary = (
    actor_features
    .groupby('first_event_date')
    .agg(
        new_actors=('actor_id', 'nunique'),
        core_actors=('actor_type', lambda x: (x == 'core').sum()),
        peripheral_actors=('actor_type', lambda x: (x == 'peripheral').sum())
    )
    .reset_index()
)

# Step 8️⃣ 保存每日汇总结果
out_path_summary = "/home/lab0/survival_diffusion_github/Bitcoin/daily_new_actors_summary.csv"
daily_summary.to_csv(out_path_summary, index=False)

print("✅ 已生成两个文件：")
print(f"1️⃣ 每日新增actor详细特征：{out_path_detail}")
print(f"2️⃣ 每日新增开发者汇总表：{out_path_summary}")
