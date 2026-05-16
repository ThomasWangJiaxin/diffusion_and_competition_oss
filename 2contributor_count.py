import pandas as pd

# 加载事件数据文件（请替换为你自己的路径）
df = pd.read_csv("/home/lab0/survival_diffusion_github/Ethereum/ronin_events_all_2025_12_31.csv")

# 确保 created_at 字段为 datetime 类型
df["created_at"] = pd.to_datetime(df["created_at"])

# 1. 统计不重复的 contributor 数量（根据 actor_id 唯一标识）
unique_contributors = df["actor_id"].nunique()
print("不重复的贡献者数量:", unique_contributors)

# 2. 每个开发者在每种行为上的第一次行为记录
first_events = df.sort_values("created_at").groupby(["actor_id", "event_type"]).first().reset_index()

# 将 "created_at" 列移动到前三列
created_at_column = first_events.pop('created_at')  # 移除 'created_at' 列
first_events.insert(2, 'created_at', created_at_column)  # 将 'created_at' 插入到第三列位置

# 可选：保存结果
first_events.to_csv("/home/lab0/survival_diffusion_github/Ethereum/ronin_first_events_by_type_2025_12_31.csv", index=False)
print("已导出每个开发者每种事件类型的首次行为记录到 ronin_first_events_by_type_2025_12_31.csv")

# bitcoin 不重复的贡献者数量: 113845
# bips 不重复的贡献者数量: 16144
# eth 不重复的贡献者数量: 76051
# eip 不重复的贡献者数量: 21552


# 批量
# import pandas as pd
# import os

# # 定义所有项目列表
# projects = [
#     'etc', 'ethereumpow', 'erigon', 'reth', 'besu', 'nethermind', 
#     'bnb', 'polygon', 'harmony', 'avalanche', 'arbitrum', 'optimism', 
#     'zksync', 'skale', 'roninold', 'roninnew', 'polkadot', 'cosmos', 
#     'tRON', 'solanaold', 'solananew', 'near', 'aptos', 'sui', 
#     'starknet', 'flow', 'arweave', 'helium', 'theta', 'secretnetwork', 
#     'alephzero'
# ]

# # 用于存储所有项目的统计结果
# summary_results = []

# # 批量处理所有项目
# for project in projects:
#     try:
#         print(f"\n{'='*80}")
#         print(f"正在处理项目: {project.upper()}")
#         print(f"{'='*80}")
        
#         # 加载事件数据文件
#         input_file = f"/home/lab0/survival_diffusion_github/Ethereum/{project}_events_all_2025_12_31.csv"
        
#         # 检查文件是否存在
#         if not os.path.exists(input_file):
#             print(f"⚠️  文件不存在，跳过: {input_file}")
#             continue
        
#         df = pd.read_csv(input_file)
        
#         # 确保 created_at 字段为 datetime 类型
#         df["created_at"] = pd.to_datetime(df["created_at"])
        
#         # 1. 统计不重复的 contributor 数量（根据 actor_id 唯一标识）
#         unique_contributors = df["actor_id"].nunique()
#         print(f"✅ 不重复的贡献者数量: {unique_contributors:,}")
        
#         # 记录到汇总结果
#         summary_results.append({
#             'project': project,
#             'unique_contributors': unique_contributors
#         })
        
#         # 2. 每个开发者在每种行为上的第一次行为记录
#         first_events = df.sort_values("created_at").groupby(["actor_id", "event_type"]).first().reset_index()
        
#         # 将 "created_at" 列移动到前三列
#         created_at_column = first_events.pop('created_at')  # 移除 'created_at' 列
#         first_events.insert(2, 'created_at', created_at_column)  # 将 'created_at' 插入到第三列位置
        
#         # 保存结果
#         output_file = f"/home/lab0/survival_diffusion_github/Ethereum/{project}_first_events_by_type_2025_12_31.csv"
#         first_events.to_csv(output_file, index=False)
        
#         print(f"✅ 已导出每个开发者每种事件类型的首次行为记录")
#         print(f"   输出文件: {output_file}")
#         print(f"   记录总数: {len(first_events):,}")
#         print(f"✅ {project.upper()} 处理完成！")
        
#     except Exception as e:
#         print(f"❌ 处理 {project.upper()} 时出错: {str(e)}")
#         continue

# # 输出汇总统计
# print(f"\n{'='*80}")
# print("📊 所有项目贡献者数量汇总")
# print(f"{'='*80}")
# print(f"{'项目':<20} {'不重复贡献者数量':>20}")
# print("-" * 80)

# for result in summary_results:
#     print(f"{result['project']:<20} {result['unique_contributors']:>20,}")

# print("-" * 80)
# print(f"{'总计项目数':<20} {len(summary_results):>20}")

# # 可选：保存汇总结果到CSV
# summary_df = pd.DataFrame(summary_results)
# summary_output = "/home/lab0/survival_diffusion_github/Ethereum/all_projects_contributors_summary.csv"
# summary_df.to_csv(summary_output, index=False)
# print(f"\n✅ 汇总结果已保存: {summary_output}")

# print(f"\n{'='*80}")
# print("🎊 所有项目批量处理完成！")
# print(f"{'='*80}")