# 写python：查询Bitcoin Core分别【/home/lab0/survival_diffusion_github/bitcoin_events_all.csv】和其他Repo，比如bitcoin SV【/home/lab0/survival_diffusion_github/bitcoinsv_events_all.csv】有重叠的用户数量，并记录每个重叠用户分别在两个repo上的首次不同类型的行为，最后输出重叠用户数量（不重复）以及这些重叠用户分别在两个repo上的首次不同类型的行为【首次行为数据同一用户放一起并按时间排序】的生成csv

import pandas as pd

# 1. 读取两个 repo 的事件数据
btc_df = pd.read_csv('/home/lab0/survival_diffusion_github/Bitcoin/bitcoin_events_timeline_unified_all_2025_12_31.csv', parse_dates=['created_at'])
bsv_df = pd.read_csv('/home/lab0/survival_diffusion_github/Bitcoin/?_events_all_2025_12_31.csv', parse_dates=['created_at'])
# ?为projects = ['bitcoincash', 'bitcoinsv', 'bitcoingpu', 'bitcoincashnode', 'parity', 'lightningnetwork', 'rootstock', 'stacks', 'bob', 'zcash', 'solanaold', 'solananew', 'tron', 'bnb']


# 2. 获取重叠用户 ID
# 但是由于bitcoin还存在timeline中没有actor id 因为只能根据actor_login来做
btc_users = set(btc_df['actor_id'].unique())
bsv_users = set(bsv_df['actor_id'].unique())
overlapping_users = btc_users & bsv_users
print(f"重叠用户数量: {len(overlapping_users)}")

# # 3. 筛选出重叠用户的事件
# btc_overlap = btc_df[btc_df['actor_id'].isin(overlapping_users)].copy()
# bsv_overlap = bsv_df[bsv_df['actor_id'].isin(overlapping_users)].copy()

# # 4. 获取两个 repo 中每个用户每种事件类型的首次行为
# btc_first = btc_overlap.sort_values('created_at').groupby(['actor_id', 'event_type']).first().reset_index()
# bsv_first = bsv_overlap.sort_values('created_at').groupby(['actor_id', 'event_type']).first().reset_index()

# # 5. 分别加上 repo 标签
# btc_first['repo'] = 'eth'
# bsv_first['repo'] = 'clo'

# # 6. 合并两个 repo 的首次事件
# combined_first = pd.concat([btc_first, bsv_first], ignore_index=True)

# # 7. 对每个用户的记录按时间排序
# combined_first = combined_first.sort_values(by=['actor_id', 'created_at'])

# # 8. 重排列顺序：将 created_at 和 repo 移动到第3、第4列
# cols = combined_first.columns.tolist()
# # 把 created_at 和 repo 拿出来
# cols.remove('created_at')
# cols.remove('repo')
# # 指定新顺序：前两列保持不变，后接 created_at 和 repo，然后其余列
# new_order = cols[:2] + ['created_at', 'repo'] + cols[2:]
# combined_first = combined_first[new_order]

# # 9. 保存为 CSV
# combined_first.to_csv('/home/lab0/survival_diffusion_github/Ethereum_compete/Privacy/btc_scrt_overlapping_users_first_events.csv', index=False)
# print("已保存每个重叠用户在两个 repo 上的首次行为记录（按类型划分）到 btc_scrt_overlapping_users_first_events.csv")
