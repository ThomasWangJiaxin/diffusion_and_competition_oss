# 按天统计新增用户的不同类型【不同类型分类方法根据event类型来分三类：
# （1）核心开发者（Core Developers）： 直接参与代码开发和维护。
# 典型事件：PushEvent, PullRequestEvent, PullRequestReviewEvent, PullRequestReviewCommentEvent, CommitCommentEvent, ReleaseEvent, CreateEvent（分支创建）, DeleteEvent。
# （2）外围贡献者（Peripheral Contributors）： 参与贡献，但不一定是核心代码提交者，例如提交问题、评论或分叉仓库。
# 典型事件：ForkEvent, IssueCommentEvent, IssuesEvent。
# （3）观察者（Observers）： 不直接贡献代码，主要关注项目或参与社区讨论。
# 典型事件：WatchEvent
# 最后生成每天不同类型的新增用户的数量和累计数量csv
import pandas as pd

# 读取数据
try:
    df = pd.read_csv('/home/lab0/survival_diffusion_github/Ethereum/eth_first_actor_count_timeline_event_2025_12_31.csv')
except FileNotFoundError as e:
    print(f"Error: CSV file not found. Please check file paths. {e}")
    exit(1)

# 确保日期格式一致
df['date'] = pd.to_datetime(df['date'])

# 定义用户类型对应的 event_type
core_dev_events = ['PushEvent', 'PullRequestEvent', 'PullRequestReviewEvent', 
                   'PullRequestReviewCommentEvent', 'CommitCommentEvent', 
                   'ReleaseEvent', 'CreateEvent', 'DeleteEvent']
periph_contrib_events = ['ForkEvent', 'IssueCommentEvent', 'IssuesEvent']
observer_events = ['WatchEvent']

# 按 event_type 分类用户类型
df['user_type'] = 'Unknown'
df.loc[df['event_type'].isin(core_dev_events), 'user_type'] = 'CoreDev'
df.loc[df['event_type'].isin(periph_contrib_events), 'user_type'] = 'PeripheralContrib'
df.loc[df['event_type'].isin(observer_events), 'user_type'] = 'Observer'

# 按天统计新增用户数量
daily_stats = df.groupby(['date', 'user_type']).size().unstack(fill_value=0)
daily_stats = daily_stats.rename(columns={
    'CoreDev': 'new_core_dev',
    'PeripheralContrib': 'new_periph_contrib',
    'Observer': 'new_observer'
})

# 按日期排序
daily_stats = daily_stats.sort_index()

# 计算累计用户数量
daily_stats['cum_core_dev'] = daily_stats['new_core_dev'].cumsum()
daily_stats['cum_periph_contrib'] = daily_stats['new_periph_contrib'].cumsum()
daily_stats['cum_observer'] = daily_stats['new_observer'].cumsum()

# 填充缺失的日期（如果有）
all_dates = pd.date_range(start=daily_stats.index.min(), end=daily_stats.index.max(), freq='D')
daily_stats = daily_stats.reindex(all_dates).fillna(0)

# 重置索引，转换为日期列
daily_stats = daily_stats.reset_index().rename(columns={'index': 'date'})

# 保存到 CSV 文件
output_file = '/home/lab0/survival_diffusion_github/Ethereum/eth_first_user_type_stats_2025_12_31.csv'
daily_stats.to_csv(output_file, index=False, date_format='%Y-%m-%d')
print(f"Output saved to {output_file}")