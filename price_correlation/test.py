# import pandas as pd

# # 1. 读取数据
# df = pd.read_csv("/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv")

# # 2. 转换 date 列为时间类型
# df['date'] = pd.to_datetime(df['date'])
# df = df.sort_values('date').set_index('date')

# # 3. 周 / 月 / 季度 聚合（求和）
# weekly = df.resample('W').sum()     # 按周
# monthly = df.resample('M').sum()    # 按月
# quarterly = df.resample('Q').sum()  # 按季度

# # 4. 保存结果
# weekly.to_csv("/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules_weekly.csv")
# monthly.to_csv("/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules_monthly.csv")
# quarterly.to_csv("/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules_quarterly.csv")

# print("Weekly / Monthly / Quarterly aggregation done!")

# ==========
# 合并Solana Old和Solana New两个文件，最后生成/home/lab0/survival_diffusion_github/Bitcoin/solana_events_all_2025_12_31.csv
# /home/lab0/survival_diffusion_github/Bitcoin/solanaold_events_all_2025_12_31.csv
# /home/lab0/survival_diffusion_github/Bitcoin/solananew_events_all_2025_12_31.csv

# import pandas as pd

# # 输入文件
# file_old = "/home/lab0/survival_diffusion_github/Ethereum/roninold_events_all_2025_12_31.csv"
# file_new = "/home/lab0/survival_diffusion_github/Ethereum/roninnew_events_all_2025_12_31.csv"

# # 输出文件
# output_file = "/home/lab0/survival_diffusion_github/Ethereum/ronin_events_all_2025_12_31.csv"

# # 读取两个CSV
# df_old = pd.read_csv(file_old)
# df_new = pd.read_csv(file_new)

# # 合并（纵向拼接）
# df_all = pd.concat([df_old, df_new], ignore_index=True)

# # 保存结果
# df_all.to_csv(output_file, index=False)

# print(f"合并完成，输出到: {output_file}")
# print("总行数:", len(df_all))



# 桑基图（BTC在中间 左边流入 右边流出）
# import pandas as pd
# import plotly.graph_objects as go

# # ===================================================================
# # 配置区域
# # ===================================================================

# # 输入文件路径
# input_file = '/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv'

# # 输出文件路径
# output_html = '/home/lab0/survival_diffusion_github/btc_migration_sankey.html'
# output_png = '/home/lab0/survival_diffusion_github/btc_migration_sankey.png'

# # 最小流量阈值（小于此值的流不显示）
# MIN_FLOW = 10  # 最少10人才显示

# # ===================================================================
# # 读取和处理数据
# # ===================================================================

# print("正在读取数据...")
# df = pd.read_csv(input_file)

# print(f"✅ 数据已加载: {len(df)} 天的记录")

# # ===================================================================
# # 汇总迁入数据（左侧）
# # ===================================================================

# print("\n汇总迁入数据...")
# inflow_cols = [col for col in df.columns if col.startswith('in_from_')]
# inflow_data = {}

# for col in inflow_cols:
#     chain = col.replace('in_from_', '')
#     total = df[col].sum()
#     if total >= MIN_FLOW:
#         inflow_data[chain] = total

# print(f"✅ 发现 {len(inflow_data)} 个迁入来源（总量 >= {MIN_FLOW}）")

# # ===================================================================
# # 汇总迁出数据（右侧）
# # ===================================================================

# print("汇总迁出数据...")
# outflow_cols = [col for col in df.columns if col.startswith('out_to_')]
# outflow_data = {}

# for col in outflow_cols:
#     chain = col.replace('out_to_', '')
#     total = df[col].sum()
#     if total >= MIN_FLOW:
#         outflow_data[chain] = total

# print(f"✅ 发现 {len(outflow_data)} 个迁出目标（总量 >= {MIN_FLOW}）")

# # ===================================================================
# # 构建桑基图数据结构
# # ===================================================================

# print("\n构建桑基图...")

# # 节点列表和位置
# nodes = []
# node_colors = []
# node_x = []  # X坐标：0=左边，0.5=中间，1=右边
# node_y = []  # Y坐标：垂直分布

# # 1️⃣ 添加左侧节点（迁入来源）
# left_chains = sorted(inflow_data.items(), key=lambda x: x[1], reverse=True)
# num_left = len(left_chains)

# for i, (chain, value) in enumerate(left_chains):
#     nodes.append(f"{chain} (IN)")
#     node_colors.append('#90EE90')  # 浅绿色
#     node_x.append(0.01)  # 左边
#     node_y.append((i + 1) / (num_left + 1))  # 均匀分布

# # 2️⃣ 添加中间节点（BTC）
# btc_index = len(nodes)
# nodes.append('BTC')
# node_colors.append('#4169E1')  # 皇家蓝
# node_x.append(0.5)  # 中间
# node_y.append(0.5)  # 中间

# # 3️⃣ 添加右侧节点（迁出目标）
# right_chains = sorted(outflow_data.items(), key=lambda x: x[1], reverse=True)
# num_right = len(right_chains)

# for i, (chain, value) in enumerate(right_chains):
#     nodes.append(f"{chain} (OUT)")
#     node_colors.append('#FFB6C1')  # 浅粉色
#     node_x.append(0.99)  # 右边
#     node_y.append((i + 1) / (num_right + 1))  # 均匀分布

# print(f"✅ 创建了 {len(nodes)} 个节点")
# print(f"   左侧（迁入）: {num_left} 个")
# print(f"   中间（BTC）: 1 个")
# print(f"   右侧（迁出）: {num_right} 个")

# # ===================================================================
# # 创建连接（links）
# # ===================================================================

# sources = []
# targets = []
# values = []
# labels = []
# link_colors = []

# # 迁入连接（左侧 → BTC）
# for i, (chain, total) in enumerate(left_chains):
#     sources.append(i)  # 左侧节点索引
#     targets.append(btc_index)  # BTC索引
#     values.append(total)
#     labels.append(f"{chain} → BTC<br>{total:,} developers")
#     link_colors.append('rgba(144, 238, 144, 0.3)')  # 浅绿色透明

# # 迁出连接（BTC → 右侧）
# right_start_index = btc_index + 1
# for i, (chain, total) in enumerate(right_chains):
#     sources.append(btc_index)  # BTC索引
#     targets.append(right_start_index + i)  # 右侧节点索引
#     values.append(total)
#     labels.append(f"BTC → {chain}<br>{total:,} developers")
#     link_colors.append('rgba(255, 182, 193, 0.3)')  # 浅粉色透明

# print(f"✅ 创建了 {len(values)} 条连接")

# # ===================================================================
# # 创建桑基图
# # ===================================================================

# print("\n生成桑基图...")

# total_inflow = sum(inflow_data.values())
# total_outflow = sum(outflow_data.values())
# net_flow = total_inflow - total_outflow

# fig = go.Figure(data=[go.Sankey(
#     arrangement='snap',  # 固定节点位置
#     node=dict(
#         pad=20,
#         thickness=25,
#         line=dict(color="white", width=2),
#         label=nodes,
#         color=node_colors,
#         x=node_x,
#         y=node_y,
#         customdata=[f"{node}" for node in nodes],
#         hovertemplate='%{customdata}<br>%{value:,} developers<extra></extra>'
#     ),
#     link=dict(
#         source=sources,
#         target=targets,
#         value=values,
#         label=labels,
#         color=link_colors,
#         hovertemplate='%{label}<extra></extra>'
#     )
# )])

# fig.update_layout(
#     title=dict(
#         text=f"<b>Bitcoin Developer Migration Flow</b><br>" + 
#              f"<sub>📥 Total Inflow: {total_inflow:,}   |   " +
#              f"📤 Total Outflow: {total_outflow:,}   |   " +
#              f"📊 Net Flow: {net_flow:+,}</sub>",
#         font=dict(size=22),
#         x=0.5,
#         xanchor='center'
#     ),
#     font=dict(size=11, family="Arial"),
#     height=900,
#     width=1600,
#     plot_bgcolor='#F8F9FA',
#     paper_bgcolor='#FFFFFF'
# )

# # 添加注释
# fig.add_annotation(
#     text="⬅️ Inflow Sources",
#     xref="paper", yref="paper",
#     x=0.05, y=1.02,
#     showarrow=False,
#     font=dict(size=14, color='green')
# )

# fig.add_annotation(
#     text="Outflow Targets ➡️",
#     xref="paper", yref="paper",
#     x=0.95, y=1.02,
#     showarrow=False,
#     font=dict(size=14, color='red')
# )

# # ===================================================================
# # 保存结果
# # ===================================================================

# print("\n保存文件...")

# # 保存为交互式HTML
# fig.write_html(output_html)
# print(f"✅ HTML文件已保存: {output_html}")

# # 保存为静态图片
# try:
#     fig.write_image(output_png, width=1600, height=900, scale=2)
#     print(f"✅ PNG文件已保存: {output_png}")
# except Exception as e:
#     print(f"⚠️  PNG保存失败 (需要安装 kaleido): {e}")

# # ===================================================================
# # 显示统计信息
# # ===================================================================

# print("\n" + "="*80)
# print("📊 Bitcoin Developer Migration Summary")
# print("="*80)

# print(f"\n📥 Top 10 Inflow Sources (迁入BTC):")
# for i, (chain, total) in enumerate(left_chains[:10], 1):
#     percentage = total / total_inflow * 100
#     bar = "█" * int(percentage / 2)
#     print(f"  {i:2d}. {chain:<20} {total:>6,} ({percentage:>5.1f}%) {bar}")

# print(f"\n📤 Top 10 Outflow Targets (从BTC迁出):")
# for i, (chain, total) in enumerate(right_chains[:10], 1):
#     percentage = total / total_outflow * 100
#     bar = "█" * int(percentage / 2)
#     print(f"  {i:2d}. {chain:<20} {total:>6,} ({percentage:>5.1f}%) {bar}")

# print(f"\n💡 Summary:")
# print(f"   Total Inflow:  {total_inflow:>8,} developers")
# print(f"   Total Outflow: {total_outflow:>8,} developers")
# print(f"   Net Flow:      {net_flow:>+8,} developers")

# if net_flow > 0:
#     print(f"\n   ✅ BTC has a net GAIN of {net_flow:,} developers")
# elif net_flow < 0:
#     print(f"\n   ⚠️  BTC has a net LOSS of {abs(net_flow):,} developers")
# else:
#     print(f"\n   ⚡ Inflow and outflow are balanced")

# print("\n" + "="*80)
# print("✅ 完成！请打开以下文件查看桑基图：")
# print(f"   {output_html}")
# print("="*80)

# 桑基图（只有两列）
# import pandas as pd
# import plotly.graph_objects as go

# # ===================================================================
# # 配置区域
# # ===================================================================

# # 输入文件路径
# input_file = '/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv'

# # 输出文件路径
# output_html = '/home/lab0/survival_diffusion_github/btc_migration_sankey_dual_column.html'
# output_png = '/home/lab0/survival_diffusion_github/btc_migration_sankey_dual_column.png'

# # 最小流量阈值（至少有一个方向超过此值才显示该项目）
# MIN_FLOW = 10

# # ===================================================================
# # 读取和处理数据
# # ===================================================================

# print("正在读取数据...")
# df = pd.read_csv(input_file)
# print(f"✅ 数据已加载: {len(df)} 天的记录")

# # ===================================================================
# # 汇总所有项目的双向流动
# # ===================================================================

# print("\n分析双向流动...")

# # 收集所有项目的迁入和迁出数据
# project_flows = {}

# # 处理迁入数据（项目 → BTC）
# inflow_cols = [col for col in df.columns if col.startswith('in_from_')]
# for col in inflow_cols:
#     chain = col.replace('in_from_', '')
#     inflow = df[col].sum()
#     if chain not in project_flows:
#         project_flows[chain] = {'inflow': 0, 'outflow': 0}
#     project_flows[chain]['inflow'] = inflow

# # 处理迁出数据（BTC → 项目）
# outflow_cols = [col for col in df.columns if col.startswith('out_to_')]
# for col in outflow_cols:
#     chain = col.replace('out_to_', '')
#     outflow = df[col].sum()
#     if chain not in project_flows:
#         project_flows[chain] = {'inflow': 0, 'outflow': 0}
#     project_flows[chain]['outflow'] = outflow

# # 筛选：至少有一个方向 >= MIN_FLOW
# filtered_projects = {
#     chain: flows 
#     for chain, flows in project_flows.items() 
#     if flows['inflow'] >= MIN_FLOW or flows['outflow'] >= MIN_FLOW
# }

# # 按总流量排序（inflow + outflow）
# sorted_projects = sorted(
#     filtered_projects.items(), 
#     key=lambda x: x[1]['inflow'] + x[1]['outflow'], 
#     reverse=True
# )

# print(f"✅ 发现 {len(sorted_projects)} 个项目（至少一个方向 >= {MIN_FLOW}）")

# # ===================================================================
# # 构建桑基图数据结构
# # ===================================================================

# print("\n构建桑基图...")

# # 节点列表
# nodes = []
# node_colors = []
# node_x = []
# node_y = []

# # 1️⃣ 左侧：BTC（单个节点，居中）
# btc_index = 0
# nodes.append('BTC')
# node_colors.append('#FFD700')  # 金色
# node_x.append(0.01)
# node_y.append(0.5)

# # 2️⃣ 右侧：所有其他项目（垂直排列）
# num_projects = len(sorted_projects)
# for i, (chain, flows) in enumerate(sorted_projects):
#     nodes.append(chain)
#     # 根据净流量着色
#     net_flow = flows['inflow'] - flows['outflow']
#     if net_flow > 0:
#         node_colors.append('#90EE90')  # 绿色（净流入BTC）
#     elif net_flow < 0:
#         node_colors.append('#FFB6C1')  # 粉色（净流出BTC）
#     else:
#         node_colors.append('#D3D3D3')  # 灰色（平衡）
    
#     node_x.append(0.99)
#     node_y.append((i + 1) / (num_projects + 1))

# print(f"✅ 创建了 {len(nodes)} 个节点")

# # ===================================================================
# # 创建连接
# # ===================================================================

# sources = []
# targets = []
# values = []
# labels = []
# link_colors = []

# total_inflow = 0
# total_outflow = 0

# for i, (chain, flows) in enumerate(sorted_projects):
#     project_index = i + 1  # 右侧项目的索引
    
#     # 迁入连接（项目 → BTC，绿色）
#     if flows['inflow'] > 0:
#         sources.append(project_index)
#         targets.append(btc_index)
#         values.append(flows['inflow'])
#         labels.append(f"<b>{chain} → BTC</b><br>{flows['inflow']:,} developers")
#         link_colors.append('rgba(34, 139, 34, 0.4)')  # 深绿色透明
#         total_inflow += flows['inflow']
    
#     # 迁出连接（BTC → 项目，红色）
#     if flows['outflow'] > 0:
#         sources.append(btc_index)
#         targets.append(project_index)
#         values.append(flows['outflow'])
#         labels.append(f"<b>BTC → {chain}</b><br>{flows['outflow']:,} developers")
#         link_colors.append('rgba(220, 20, 60, 0.4)')  # 深红色透明
#         total_outflow += flows['outflow']

# print(f"✅ 创建了 {len(values)} 条连接")
# print(f"   迁入连接（绿色）: {sum(1 for c in link_colors if '34, 139, 34' in c)}")
# print(f"   迁出连接（红色）: {sum(1 for c in link_colors if '220, 20, 60' in c)}")

# # ===================================================================
# # 创建桑基图
# # ===================================================================

# print("\n生成桑基图...")

# net_flow = total_inflow - total_outflow

# # 创建节点标签（显示净流量）
# node_labels = []
# for i, node in enumerate(nodes):
#     if node == 'BTC':
#         node_labels.append(f"<b>BTC</b><br>Net: {net_flow:+,}")
#     else:
#         # 找到对应项目的流量
#         for chain, flows in sorted_projects:
#             if chain == node:
#                 net = flows['inflow'] - flows['outflow']
#                 node_labels.append(f"<b>{node}</b><br>IN: {flows['inflow']:,}<br>OUT: {flows['outflow']:,}<br>Net: {net:+,}")
#                 break

# fig = go.Figure(data=[go.Sankey(
#     arrangement='snap',
#     node=dict(
#         pad=15,
#         thickness=30,
#         line=dict(color="white", width=2),
#         label=node_labels,
#         color=node_colors,
#         x=node_x,
#         y=node_y,
#         hovertemplate='%{label}<extra></extra>'
#     ),
#     link=dict(
#         source=sources,
#         target=targets,
#         value=values,
#         label=labels,
#         color=link_colors,
#         hovertemplate='%{label}<extra></extra>'
#     )
# )])

# fig.update_layout(
#     title=dict(
#         text=f"<b>Bitcoin Developer Migration Flow (Bidirectional)</b><br>" + 
#              f"<sub>🟢 Green: Inflow to BTC ({total_inflow:,})   |   " +
#              f"🔴 Red: Outflow from BTC ({total_outflow:,})   |   " +
#              f"📊 Net Flow: {net_flow:+,}</sub>",
#         font=dict(size=22),
#         x=0.5,
#         xanchor='center'
#     ),
#     font=dict(size=10, family="Arial"),
#     height=max(800, num_projects * 40),  # 根据项目数量自动调整高度
#     width=1400,
#     plot_bgcolor='#FAFAFA',
#     paper_bgcolor='#FFFFFF'
# )

# # 添加图例说明
# fig.add_annotation(
#     text="🟡 <b>BTC</b>",
#     xref="paper", yref="paper",
#     x=0.05, y=1.05,
#     showarrow=False,
#     font=dict(size=14, color='#FFD700'),
#     bgcolor='white',
#     bordercolor='#FFD700',
#     borderwidth=2
# )

# fig.add_annotation(
#     text="<b>Competing Projects</b><br>🟢 Net Inflow | 🌸 Net Outflow",
#     xref="paper", yref="paper",
#     x=0.95, y=1.05,
#     showarrow=False,
#     font=dict(size=12),
#     bgcolor='white',
#     bordercolor='gray',
#     borderwidth=1
# )

# # ===================================================================
# # 保存结果
# # ===================================================================

# print("\n保存文件...")

# fig.write_html(output_html)
# print(f"✅ HTML文件已保存: {output_html}")

# try:
#     fig.write_image(output_png, width=1400, height=max(800, num_projects * 40), scale=2)
#     print(f"✅ PNG文件已保存: {output_png}")
# except Exception as e:
#     print(f"⚠️  PNG保存失败: {e}")

# # ===================================================================
# # 详细统计
# # ===================================================================

# print("\n" + "="*80)
# print("📊 Bitcoin Developer Flow Analysis")
# print("="*80)

# print(f"\n{'Project':<25} {'Inflow→BTC':>12} {'BTC→Outflow':>12} {'Net Flow':>12} {'Status':<15}")
# print("-" * 80)

# for chain, flows in sorted_projects:
#     inflow = flows['inflow']
#     outflow = flows['outflow']
#     net = inflow - outflow
    
#     if net > 0:
#         status = "✅ Net Gainer"
#         color = ""
#     elif net < 0:
#         status = "⚠️  Net Loser"
#         color = ""
#     else:
#         status = "⚡ Balanced"
#         color = ""
    
#     print(f"{chain:<25} {inflow:>12,} {outflow:>12,} {net:>+12,} {status:<15}")

# print("-" * 80)
# print(f"{'TOTAL':<25} {total_inflow:>12,} {total_outflow:>12,} {net_flow:>+12,}")

# print(f"\n💡 Summary:")
# print(f"   Total projects analyzed: {len(sorted_projects)}")
# print(f"   BTC net flow: {net_flow:+,} developers")

# if net_flow > 0:
#     print(f"   ✅ BTC is a NET WINNER - attracting more developers")
# elif net_flow < 0:
#     print(f"   ⚠️  BTC is a NET LOSER - losing developers to competitors")
# else:
#     print(f"   ⚡ Perfect balance between inflow and outflow")

# # 找出最大迁入和迁出
# max_inflow_project = max(sorted_projects, key=lambda x: x[1]['inflow'])
# max_outflow_project = max(sorted_projects, key=lambda x: x[1]['outflow'])

# print(f"\n🏆 Top Contributors:")
# print(f"   Largest inflow source: {max_inflow_project[0]} ({max_inflow_project[1]['inflow']:,} devs)")
# print(f"   Largest outflow target: {max_outflow_project[0]} ({max_outflow_project[1]['outflow']:,} devs)")

# print("\n" + "="*80)
# print("✅ 完成！请打开以下文件查看桑基图：")
# print(f"   {output_html}")
# print("="*80)

# 桑基图 两列
# import pandas as pd
# import plotly.graph_objects as go

# # === 文件路径 ===
# CSV_PATH = "/home/lab0/survival_diffusion_github/btc_global_migration_enhanced_daily_strict_rules.csv"

# # === 读取数据 ===
# df = pd.read_csv(CSV_PATH, parse_dates=["date"])

# # === 选时间区间（可改） ===
# start_time = "2012-01-01"
# end_time   = "2025-12-31"

# df = df[(df["date"] >= start_time) & (df["date"] <= end_time)]

# # === 识别 in / out 列 ===
# in_cols  = [c for c in df.columns if c.startswith("in_from_")]
# out_cols = [c for c in df.columns if c.startswith("out_to_")]

# # === 汇总全时期流量 ===
# flows = []

# # 其他 → BTC
# for col in in_cols:
#     src = col.replace("in_from_", "")
#     val = df[col].sum()
#     if val > 0:
#         flows.append((src, "BTC", val))

# # BTC → 其他
# for col in out_cols:
#     tgt = col.replace("out_to_", "")
#     val = df[col].sum()
#     if val > 0:
#         flows.append(("BTC", tgt, val))

# flow_df = pd.DataFrame(flows, columns=["source", "target", "value"])

# # === 构造节点 ===
# labels = pd.unique(flow_df[["source", "target"]].values.ravel())
# label_to_id = {lab: i for i, lab in enumerate(labels)}

# flow_df["source_id"] = flow_df["source"].map(label_to_id)
# flow_df["target_id"] = flow_df["target"].map(label_to_id)

# # === 画 Sankey ===
# fig = go.Figure(data=[go.Sankey(
#     node=dict(
#         pad=15,
#         thickness=18,
#         label=labels
#     ),
#     link=dict(
#         source=flow_df["source_id"],
#         target=flow_df["target_id"],
#         value=flow_df["value"]
#     )
# )])

# fig.update_layout(
#     title_text="Developer Migration Flows Between Bitcoin and Competing Ecosystems",
#     font_size=12
# )

# fig.show()

# 桑基图 三列
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ===================================================================
# 配置区域
# ===================================================================

# 输入文件路径
input_file = '/home/lab0/survival_diffusion_github/eth_global_migration_enhanced_daily_strict_rules.csv'

# 输出文件路径
output_html = '/home/lab0/survival_diffusion_github/eth_migration_sankey.html'
output_png = '/home/lab0/survival_diffusion_github/eth_migration_sankey.png'

# 最小流量阈值（任一方向大于此值即显示）
MIN_FLOW = 5

# 🔥 字体大小范围配置
MIN_FONT_SIZE = 20  # 最小字号
MAX_FONT_SIZE = 40  # 最大字号（流量最大的项目）

# ===================================================================
# 读取和处理数据
# ===================================================================

print("正在读取数据...")
df = pd.read_csv(input_file)

print(f"✅ 数据已加载: {len(df)} 天的记录")

# ===================================================================
# 汇总迁入和迁出数据
# ===================================================================

print("\n汇总迁移数据...")

# 迁入数据
inflow_cols = [col for col in df.columns if col.startswith('in_from_')]
inflow_data = {}
for col in inflow_cols:
    chain = col.replace('in_from_', '')
    total = df[col].sum()
    inflow_data[chain] = total

# 迁出数据
outflow_cols = [col for col in df.columns if col.startswith('out_to_')]
outflow_data = {}
for col in outflow_cols:
    chain = col.replace('out_to_', '')
    total = df[col].sum()
    outflow_data[chain] = total

# 获取所有出现的链（合并迁入和迁出）
all_chains = set(inflow_data.keys()) | set(outflow_data.keys())

# 创建统一的数据结构：每个链的迁入、迁出、总流量
chain_flows = {}
for chain in all_chains:
    inflow = inflow_data.get(chain, 0)
    outflow = outflow_data.get(chain, 0)
    total_flow = inflow + outflow
    
    # 只保留总流量大于阈值的
    if total_flow >= MIN_FLOW:
        chain_flows[chain] = {
            'inflow': inflow,
            'outflow': outflow,
            'total': total_flow
        }

# 按总流量排序
sorted_chains = sorted(chain_flows.items(), key=lambda x: x[1]['total'], reverse=True)

print(f"✅ 发现 {len(sorted_chains)} 个项目（双向总流量 >= {MIN_FLOW}）")

# ===================================================================
# 🔥 计算每个项目的字体大小（根据流量）
# ===================================================================

# 提取所有流量值
flow_values = [flows['total'] for _, flows in sorted_chains]
max_flow = max(flow_values)
min_flow = min(flow_values)

# 计算字体大小的映射函数
def calculate_font_size(flow, min_val, max_val):
    """根据流量值计算字体大小"""
    if max_val == min_val:
        return MAX_FONT_SIZE
    # 线性映射到字体大小范围
    normalized = (flow - min_val) / (max_val - min_val)
    font_size = MIN_FONT_SIZE + (MAX_FONT_SIZE - MIN_FONT_SIZE) * normalized
    return int(font_size)

# 为每个链计算字体大小
chain_font_sizes = {}
for chain, flows in sorted_chains:
    font_size = calculate_font_size(flows['total'], min_flow, max_flow)
    chain_font_sizes[chain] = font_size

print("\n📊 字体大小分配 (Top 10):")
for i, (chain, flows) in enumerate(sorted_chains[:10], 1):
    font_size = chain_font_sizes[chain]
    print(f"  {i:2d}. {chain:<20} 流量: {flows['total']:>6,}  字号: {font_size}px")

# ===================================================================
# 构建桑基图数据结构
# ===================================================================

print("\n构建对称桑基图...")

nodes = []
node_labels_html = []  # 🔥 使用 HTML 格式的标签
node_colors = []
node_x = []
node_y = []

num_chains = len(sorted_chains)

# 1️⃣ 左侧节点（迁入）- 所有链的 IN 节点
left_indices = {}
for i, (chain, flows) in enumerate(sorted_chains):
    font_size = chain_font_sizes[chain]
    # 🔥 使用 HTML 标签设置字体大小
    label_html = f'<span style="font-size:{font_size}px"><b>{chain}</b></span>'
    
    nodes.append(chain)  # 原始名称（用于索引）
    node_labels_html.append(label_html)  # HTML 格式标签
    node_colors.append('#90EE90' if flows['inflow'] > 0 else '#E8E8E8')
    node_x.append(0.01)
    node_y.append((i + 1) / (num_chains + 1))
    left_indices[chain] = len(nodes) - 1

# 2️⃣ 中间节点（ETH）- 🔥 永远使用最大字号
eth_index = len(nodes)
eth_font_size = MAX_FONT_SIZE + 4  # ETH 字号比最大的还要大一点
nodes.append('BTC')
node_labels_html.append(f'<span style="font-size:{eth_font_size}px"><b>BTC</b></span>')
node_colors.append('#FFD700')
node_x.append(0.5)
node_y.append(0.5)

# 3️⃣ 右侧节点（迁出）- 所有链的 OUT 节点，位置与左侧对应
right_indices = {}
for i, (chain, flows) in enumerate(sorted_chains):
    font_size = chain_font_sizes[chain]
    label_html = f'<span style="font-size:{font_size}px"><b>{chain}</b></span>'
    
    nodes.append(chain)
    node_labels_html.append(label_html)
    node_colors.append('#FFB6C1' if flows['outflow'] > 0 else '#E8E8E8')
    node_x.append(0.99)
    node_y.append((i + 1) / (num_chains + 1))
    right_indices[chain] = len(nodes) - 1

print(f"✅ 创建了 {len(nodes)} 个节点")
print(f"   左侧: {num_chains} 个")
print(f"   中间: 1 个 (ETH, {eth_font_size}px)")
print(f"   右侧: {num_chains} 个")

# ===================================================================
# 创建连接
# ===================================================================

sources = []
targets = []
values = []
labels = []
link_colors = []

total_inflow = 0
total_outflow = 0

# 迁入连接（左侧 → ETH）
for chain, flows in sorted_chains:
    if flows['inflow'] > 0:
        sources.append(left_indices[chain])
        targets.append(eth_index)
        values.append(flows['inflow'])
        labels.append(f"{chain} → BTC<br>{flows['inflow']:,} developers")
        link_colors.append('rgba(144, 238, 144, 0.4)')
        total_inflow += flows['inflow']

# 迁出连接（ETH → 右侧）
for chain, flows in sorted_chains:
    if flows['outflow'] > 0:
        sources.append(eth_index)
        targets.append(right_indices[chain])
        values.append(flows['outflow'])
        labels.append(f"BTC → {chain}<br>{flows['outflow']:,} developers")
        link_colors.append('rgba(255, 182, 193, 0.4)')
        total_outflow += flows['outflow']

print(f"✅ 创建了 {len(values)} 条连接")

# ===================================================================
# 创建桑基图
# ===================================================================

print("\n生成桑基图...")

net_flow = total_inflow - total_outflow

fig = go.Figure(data=[go.Sankey(
    arrangement='snap',
    node=dict(
        pad=15,
        thickness=40,
        line=dict(color="white", width=2),
        label=node_labels_html,  # 🔥 使用 HTML 格式的标签
        color=node_colors,
        x=node_x,
        y=node_y,
        customdata=nodes,  # 原始名称用于悬停
        hovertemplate='%{customdata}<br>Flow: %{value:,}<extra></extra>'
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        label=labels,
        color=link_colors,
        hovertemplate='%{label}<extra></extra>'
    )
)])

fig.update_layout(
    title=dict(
        text=f"<b>Bitcoin Developer Migration Flow (Symmetric View)</b><br>" + 
             f"<sub>📥 Inflow: <span style='color:green'><b>{total_inflow:,}</b></span>   |   " +
             f"📤 Outflow: <span style='color:red'><b>{total_outflow:,}</b></span>   |   " +
             f"📊 Net: <b>{net_flow:+,}</b></sub>",
        font=dict(size=22),
        x=0.5,
        xanchor='center'
    ),
    font=dict(size=14, family="Arial", color="#2c3e50"),
    height=max(900, num_chains * 40),
    width=1800,
    plot_bgcolor='#F8F9FA',
    paper_bgcolor='#FFFFFF'
)

# 添加标签
fig.add_annotation(
    text="<b>⬅️ Inflow to ETH</b>",
    xref="paper", yref="paper",
    x=0.05, y=1.03,
    showarrow=False,
    font=dict(size=15, color='green')
)

fig.add_annotation(
    text="<b>🪙 ETH</b>",
    xref="paper", yref="paper",
    x=0.5, y=1.03,
    showarrow=False,
    font=dict(size=18, color='#FFD700')
)

fig.add_annotation(
    text="<b>Outflow from ETH ➡️</b>",
    xref="paper", yref="paper",
    x=0.95, y=1.03,
    showarrow=False,
    font=dict(size=15, color='red')
)

# ===================================================================
# 保存结果
# ===================================================================

print("\n保存文件...")

fig.write_html(output_html)
print(f"✅ HTML文件已保存: {output_html}")

try:
    fig.write_image(output_png, width=1800, height=max(900, num_chains * 40), scale=2)
    print(f"✅ PNG文件已保存: {output_png}")
except Exception as e:
    print(f"⚠️  PNG保存失败: {e}")

# ===================================================================
# 显示统计信息
# ===================================================================

print("\n" + "="*100)
print("📊 Bitcoin Developer Migration Summary (Symmetric View)")
print("="*100)

print(f"\n{'Project':<20} {'Font Size':<12} {'Inflow (←ETH)':<20} {'Outflow (ETH→)':<20} {'Total Flow':<15} {'Net':<10}")
print("-" * 120)

for chain, flows in sorted_chains[:15]:
    font_size = chain_font_sizes[chain]
    inflow = flows['inflow']
    outflow = flows['outflow']
    total = flows['total']
    net = inflow - outflow
    
    in_bar = "█" * min(int(inflow / 50), 15)
    out_bar = "█" * min(int(outflow / 50), 15)
    
    print(f"{chain:<20} {font_size:>3}px        {inflow:>6,} {in_bar:<15} {outflow:>6,} {out_bar:<15} {total:>6,} {net:>+10,}")

print("-" * 120)
print(f"{'TOTAL':<20} {'':12} {total_inflow:>6,} {'':15} {total_outflow:>6,} {'':15} {total_inflow+total_outflow:>6,} {net_flow:>+10,}")

print("\n💡 Observations:")
print(f"   • ETH has a net {'GAIN' if net_flow > 0 else 'LOSS'} of {abs(net_flow):,} developers")
print(f"   • Largest inflow source: {sorted_chains[0][0]} ({sorted_chains[0][1]['inflow']:,} developers, {chain_font_sizes[sorted_chains[0][0]]}px)")
largest_outflow = max(sorted_chains, key=lambda x: x[1]['outflow'])
print(f"   • Largest outflow target: {largest_outflow[0]} ({largest_outflow[1]['outflow']:,} developers, {chain_font_sizes[largest_outflow[0]]}px)")

print(f"\n📏 字体大小范围: {MIN_FONT_SIZE}px - {MAX_FONT_SIZE}px")
print(f"   ETH (中心节点): {eth_font_size}px")
print(f"   最大流量项目: {sorted_chains[0][0]} = {chain_font_sizes[sorted_chains[0][0]]}px")
print(f"   最小流量项目: {sorted_chains[-1][0]} = {chain_font_sizes[sorted_chains[-1][0]]}px")

print("\n" + "="*100)
print("✅ 完成！请打开以下文件查看对称桑基图：")
print(f"   {output_html}")
print("="*100)