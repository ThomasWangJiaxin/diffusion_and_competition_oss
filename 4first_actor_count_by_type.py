import pandas as pd

# 加载“每个用户第一次事件”数据（已经是细粒度的了）
df = pd.read_csv('/home/lab0/survival_diffusion_github/Ethereum/eth_first_events_by_type_2025_12_31.csv', parse_dates=['created_at'])

# 提取日期列
df['date'] = df['created_at'].dt.date

# 按日期和事件类型统计新增用户数（每个用户只出现一次）
daily_type_dist = df.groupby(['date', 'event_type'])['actor_id'].count().reset_index(name='new_user_count')

# 保存为 CSV
daily_type_dist.to_csv('/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_by_type_2025_12_31.csv', index=False)

# 每天新增用户中的不同行为类型的数量