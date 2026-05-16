# import gitlab
# import pandas as pd

# # 1. 匿名访问 GitLab（不传 token）
# gl = gitlab.Gitlab('https://gitlab.com')

# # 2. 获取项目
# project = gl.projects.get('bitcoin-cash-node/bitcoin-cash-node')

# # 3. 获取 Events
# events = project.events.list(get_all=True)
# events_data = []
# for e in events:
#     events_data.append({
#         "id": e.id,
#         "action_name": e.action_name,
#         "target_type": e.target_type,
#         "author_id": e.author_id,
#         "author_username": e.author_username,
#         "created_at": e.created_at,
#         "target_id": e.target_id,
#         "target_title": getattr(e, "target_title", None),
#         "note": getattr(e, "note", None)
#     })

# # 4. 获取 Contributors
# contributors = project.repository_contributors()
# contributors_data = []
# for c in contributors:
#     contributors_data.append({
#         "name": c['name'],
#         "email": c['email'],
#         "commits": c['commits'],
#         "additions": c.get('additions'),
#         "deletions": c.get('deletions')
#     })

# # 5. 保存 CSV
# pd.DataFrame(events_data).to_csv("events.csv", index=False, encoding="utf-8")
# pd.DataFrame(contributors_data).to_csv("contributors.csv", index=False, encoding="utf-8")

# print("✅ 导出完成：events.csv 和 contributors.csv")

# GitLab 的事件 API 主要记录的是用户在项目界面上的交互行为,commit 在 GitLab 中被视为 Git 仓库的一部分，它的历史记录由 Git 本身维护。GitLab 的事件 API 更关注的是Git 之外的、更高级别的协作行为。
# 分页抓取 (project.events.list(per_page=100, page=page)) 完整遍历了所有事件;不分页抓取 (project.events.list(get_all=True)) 默认有一个时间限制，可能只返回最近一段时间内的事件。
import gitlab
import csv
from multiprocessing import Pool, cpu_count

# 初始化 GitLab 连接（匿名访问）
gl = gitlab.Gitlab('https://gitlab.com', private_token=None)
project = gl.projects.get('bitcoin-cash-node/bitcoin-cash-node')

per_page = 100

def fetch_page(page):
    """抓取单页 events"""
    events = project.events.list(per_page=per_page, page=page)
    rows = []
    for e in events:
        rows.append([
            getattr(e, "id", ""),
            getattr(e, "action_name", ""),
            getattr(e, "target_type", ""),
            getattr(e, "target_id", ""),
            getattr(e, "target_iid", ""),
            getattr(e, "target_title", ""),
            e.author["id"] if hasattr(e, "author") else "",
            e.author["username"] if hasattr(e, "author") else "",
            getattr(e, "created_at", ""),
        ])
    return rows

if __name__ == "__main__":
    all_rows = []
    page = 1
    while True:
        rows = fetch_page(page)
        if not rows:  # 没数据了，说明到头了
            break
        all_rows.extend(rows)
        print(f"已抓取第 {page} 页，共 {len(all_rows)} 条")
        page += 1

    # 保存 CSV
    with open("bch_events.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "action_name", "target_type", "target_id", "target_iid",
            "target_title", "author_id", "author_username", "created_at"
        ])
        writer.writerows(all_rows)

    print(f"✅ 抓取完成，共 {len(all_rows)} 条事件，已保存到 bch_events.csv")

# import gitlab
# import csv

# # 匿名访问 GitLab
# gl = gitlab.Gitlab('https://gitlab.com')
# project = gl.projects.get('bitcoin-cash-node/bitcoin-cash-node')

# # 直接拿到所有事件（完整历史）
# events = project.events.list(get_all=True)

# rows = []
# for e in events:
#     rows.append([
#         getattr(e, "id", ""),
#         getattr(e, "action_name", ""),
#         getattr(e, "target_type", ""),
#         getattr(e, "target_id", ""),
#         getattr(e, "target_iid", ""),
#         getattr(e, "target_title", ""),
#         e.author["id"] if hasattr(e, "author") else "",
#         e.author["username"] if hasattr(e, "author") else "",
#         getattr(e, "created_at", ""),
#     ])

# # 保存 CSV
# with open("bch_nopage_events.csv", "w", newline="", encoding="utf-8") as f:
#     writer = csv.writer(f)
#     writer.writerow([
#         "id", "action_name", "target_type", "target_id", "target_iid",
#         "target_title", "author_id", "author_username", "created_at"
#     ])
#     writer.writerows(rows)

# print(f"✅ 抓取完成，共 {len(rows)} 条事件，已保存到 bch_nopage_events.csv")