# # Bitcoin
# import pandas as pd
# import requests
# import os
# from io import StringIO

# # 数据库连接配置
# host = '172.28.1.2'
# port = 8123
# database = 'github'
# user = 'w3r'
# password = 'Web3Resear.ch'  # 如果有密码，请填写

# # 构造 SQL 查询
# query = """
# SELECT * 
# FROM events
# WHERE repository_id = '1181927'
# ORDER BY created_at
# FORMAT TabSeparatedWithNames
# """
# # WHERE repository_url = 'https://api.github.com/repos/aleph-zero-foundation/aleph-node'

# # ClickHouse HTTP 接口 URL
# url = f"http://{host}:{port}"

# # 查询参数
# params = {
#     'query': query,
#     'user': user,
#     'password': password,
#     'database': database
# }

# try:
#     # 发送 HTTP 请求
#     response = requests.get(url, params=params)
#     response.raise_for_status()  # 检查请求是否成功

#     # 将返回的 TSV 数据转换为 pandas DataFrame
#     data = response.text
#     df = pd.read_csv(StringIO(data), sep='\t')

#     # 确保字段名与预期一致（可选：如果字段名不匹配，可以手动指定）
#     expected_columns = ['id', 'event_type', 'actor_id', 'actor_login', 'actor_display_login', 'actor_gravatar_id', 
#                         'actor_url', 'actor_avatar_url', 'repository_id', 'repository_name', 'repository_url', 
#                         'org_id', 'org_login', 'org_gravatar_id', 'org_url', 'org_avatar_url', 'created_at', 
#                         'public', 'payload', 'other']
#     if list(df.columns) != expected_columns:
#         print("警告：返回的字段名与预期不一致，实际字段名：", list(df.columns))
#         df.columns = expected_columns  # 强制设置字段名（如果需要）

#     # 确定保存路径
#     save_folder = '/home/lab0/survival_diffusion_github/Bitcoin'

#     # 确保文件夹存在
#     os.makedirs(save_folder, exist_ok=True)

#     # 生成并保存第一个 CSV 文件：所有记录
#     df.to_csv(os.path.join(save_folder, 'bitcoin_events_all_2025_12_31.csv'), index=False)

#     # 计算每天所有类型 event 的数量
#     df['created_at'] = pd.to_datetime(df['created_at'])  # 确保 created_at 字段是日期类型
#     df['date'] = df['created_at'].dt.date  # 提取日期部分

#     # 按照日期和 event_type 计算每个类型的数量
#     event_count_per_day = df.groupby(['date', 'event_type']).size().reset_index(name='event_count')

#     # 保存为 CSV
#     event_count_per_day.to_csv(os.path.join(save_folder, 'bitcoin_event_count_per_day_2025_12_31.csv'), index=False)

#     # # 计算每天累积的 event 数量
#     # df['cumulative_event_count'] = df.groupby('date').cumcount() + 1

#     # # 保存为 CSV
#     # df[['date', 'cumulative_event_count']].drop_duplicates().to_csv(
#     #     os.path.join(save_folder, 'bitcoin_cumulative_event_count.csv'), index=False)

#     print("CSV files have been generated and saved to:", save_folder)

# except Exception as e:
#     print(f"查询过程中发生错误: {e}")



# Ethereum
# import pandas as pd
# import requests
# import os
# from io import StringIO

# # 数据库连接配置
# host = '172.28.1.2'
# port = 8123
# database = 'github'
# user = 'w3r'
# password = 'Web3Resear.ch'  # 如果有密码，请填写

# # 构造 SQL 查询
# query = """
# SELECT * 
# FROM events
# WHERE repository_id = '15452919'
# ORDER BY created_at
# FORMAT TabSeparatedWithNames
# """
# # WHERE repository_url = 'https://api.github.com/repos/aleph-zero-foundation/aleph-node'

# # ClickHouse HTTP 接口 URL
# url = f"http://{host}:{port}"

# # 查询参数
# params = {
#     'query': query,
#     'user': user,
#     'password': password,
#     'database': database
# }

# try:
#     # 发送 HTTP 请求
#     response = requests.get(url, params=params)
#     response.raise_for_status()  # 检查请求是否成功

#     # 将返回的 TSV 数据转换为 pandas DataFrame
#     data = response.text
#     df = pd.read_csv(StringIO(data), sep='\t')

#     # 确保字段名与预期一致（可选：如果字段名不匹配，可以手动指定）
#     expected_columns = ['id', 'event_type', 'actor_id', 'actor_login', 'actor_display_login', 'actor_gravatar_id', 
#                         'actor_url', 'actor_avatar_url', 'repository_id', 'repository_name', 'repository_url', 
#                         'org_id', 'org_login', 'org_gravatar_id', 'org_url', 'org_avatar_url', 'created_at', 
#                         'public', 'payload', 'other']
#     if list(df.columns) != expected_columns:
#         print("警告：返回的字段名与预期不一致，实际字段名：", list(df.columns))
#         df.columns = expected_columns  # 强制设置字段名（如果需要）

#     # 确定保存路径
#     save_folder = '/home/lab0/survival_diffusion_github/Ethereum'

#     # 确保文件夹存在
#     os.makedirs(save_folder, exist_ok=True)

#     # 生成并保存第一个 CSV 文件：所有记录
#     df.to_csv(os.path.join(save_folder, 'eth_events_all_2025_12_31.csv'), index=False)

#     # 计算每天所有类型 event 的数量
#     df['created_at'] = pd.to_datetime(df['created_at'])  # 确保 created_at 字段是日期类型
#     df['date'] = df['created_at'].dt.date  # 提取日期部分

#     # 按照日期和 event_type 计算每个类型的数量
#     event_count_per_day = df.groupby(['date', 'event_type']).size().reset_index(name='event_count')

#     # 保存为 CSV
#     event_count_per_day.to_csv(os.path.join(save_folder, 'eth_event_count_per_day_2025_12_31.csv'), index=False)

#     # # 计算每天累积的 event 数量
#     # df['cumulative_event_count'] = df.groupby('date').cumcount() + 1

#     # # 保存为 CSV
#     # df[['date', 'cumulative_event_count']].drop_duplicates().to_csv(
#     #     os.path.join(save_folder, 'bitcoin_cumulative_event_count.csv'), index=False)

#     print("CSV files have been generated and saved to:", save_folder)

# except Exception as e:
#     print(f"查询过程中发生错误: {e}")


# Litecoin
# import pandas as pd
# import requests
# import os
# from io import StringIO

# # 数据库连接配置
# host = '172.28.1.2'
# port = 8123
# database = 'github'
# user = 'w3r'
# password = 'Web3Resear.ch'  # 如果有密码，请填写

# # 构造 SQL 查询
# query = """
# SELECT * 
# FROM events
# WHERE repository_id = '4646198'
# ORDER BY created_at
# FORMAT TabSeparatedWithNames
# """
# # WHERE repository_url = 'https://api.github.com/repos/aleph-zero-foundation/aleph-node'

# # ClickHouse HTTP 接口 URL
# url = f"http://{host}:{port}"

# # 查询参数
# params = {
#     'query': query,
#     'user': user,
#     'password': password,
#     'database': database
# }

# try:
#     # 发送 HTTP 请求
#     response = requests.get(url, params=params)
#     response.raise_for_status()  # 检查请求是否成功

#     # 将返回的 TSV 数据转换为 pandas DataFrame
#     data = response.text
#     df = pd.read_csv(StringIO(data), sep='\t')

#     # 确保字段名与预期一致（可选：如果字段名不匹配，可以手动指定）
#     expected_columns = ['id', 'event_type', 'actor_id', 'actor_login', 'actor_display_login', 'actor_gravatar_id', 
#                         'actor_url', 'actor_avatar_url', 'repository_id', 'repository_name', 'repository_url', 
#                         'org_id', 'org_login', 'org_gravatar_id', 'org_url', 'org_avatar_url', 'created_at', 
#                         'public', 'payload', 'other']
#     if list(df.columns) != expected_columns:
#         print("警告：返回的字段名与预期不一致，实际字段名：", list(df.columns))
#         df.columns = expected_columns  # 强制设置字段名（如果需要）

#     # 确定保存路径
#     save_folder = '/home/lab0/survival_diffusion_github/Bitcoin_compete'

#     # 确保文件夹存在
#     os.makedirs(save_folder, exist_ok=True)

#     # 生成并保存第一个 CSV 文件：所有记录
#     df.to_csv(os.path.join(save_folder, 'litecoin_events_all_2025_12_31.csv'), index=False)

#     # 计算每天所有类型 event 的数量
#     df['created_at'] = pd.to_datetime(df['created_at'])  # 确保 created_at 字段是日期类型
#     df['date'] = df['created_at'].dt.date  # 提取日期部分

#     # 按照日期和 event_type 计算每个类型的数量
#     event_count_per_day = df.groupby(['date', 'event_type']).size().reset_index(name='event_count')

#     # 保存为 CSV
#     event_count_per_day.to_csv(os.path.join(save_folder, 'litecoin_event_count_per_day_2025_12_31.csv'), index=False)

#     # # 计算每天累积的 event 数量
#     # df['cumulative_event_count'] = df.groupby('date').cumcount() + 1

#     # # 保存为 CSV
#     # df[['date', 'cumulative_event_count']].drop_duplicates().to_csv(
#     #     os.path.join(save_folder, 'bitcoin_cumulative_event_count.csv'), index=False)

#     print("CSV files have been generated and saved to:", save_folder)

# except Exception as e:
#     print(f"查询过程中发生错误: {e}")


# Dogecoin
# import pandas as pd
# import requests
# import os
# from io import StringIO

# # 数据库连接配置
# host = '172.28.1.2'
# port = 8123
# database = 'github'
# user = 'w3r'
# password = 'Web3Resear.ch'  # 如果有密码，请填写

# # 构造 SQL 查询
# query = """
# SELECT * 
# FROM events
# WHERE repository_id = '14981376'
# ORDER BY created_at
# FORMAT TabSeparatedWithNames
# """
# # WHERE repository_url = 'https://api.github.com/repos/aleph-zero-foundation/aleph-node'

# # ClickHouse HTTP 接口 URL
# url = f"http://{host}:{port}"

# # 查询参数
# params = {
#     'query': query,
#     'user': user,
#     'password': password,
#     'database': database
# }

# try:
#     # 发送 HTTP 请求
#     response = requests.get(url, params=params)
#     response.raise_for_status()  # 检查请求是否成功

#     # 将返回的 TSV 数据转换为 pandas DataFrame
#     data = response.text
#     df = pd.read_csv(StringIO(data), sep='\t')

#     # 确保字段名与预期一致（可选：如果字段名不匹配，可以手动指定）
#     expected_columns = ['id', 'event_type', 'actor_id', 'actor_login', 'actor_display_login', 'actor_gravatar_id', 
#                         'actor_url', 'actor_avatar_url', 'repository_id', 'repository_name', 'repository_url', 
#                         'org_id', 'org_login', 'org_gravatar_id', 'org_url', 'org_avatar_url', 'created_at', 
#                         'public', 'payload', 'other']
#     if list(df.columns) != expected_columns:
#         print("警告：返回的字段名与预期不一致，实际字段名：", list(df.columns))
#         df.columns = expected_columns  # 强制设置字段名（如果需要）

#     # 确定保存路径
#     save_folder = '/home/lab0/survival_diffusion_github/Bitcoin_compete'

#     # 确保文件夹存在
#     os.makedirs(save_folder, exist_ok=True)

#     # 生成并保存第一个 CSV 文件：所有记录
#     df.to_csv(os.path.join(save_folder, 'dogecoin_events_all_2025_12_31.csv'), index=False)

#     # 计算每天所有类型 event 的数量
#     df['created_at'] = pd.to_datetime(df['created_at'])  # 确保 created_at 字段是日期类型
#     df['date'] = df['created_at'].dt.date  # 提取日期部分

#     # 按照日期和 event_type 计算每个类型的数量
#     event_count_per_day = df.groupby(['date', 'event_type']).size().reset_index(name='event_count')

#     # 保存为 CSV
#     event_count_per_day.to_csv(os.path.join(save_folder, 'dogecoin_event_count_per_day_2025_12_31.csv'), index=False)

#     # # 计算每天累积的 event 数量
#     # df['cumulative_event_count'] = df.groupby('date').cumcount() + 1

#     # # 保存为 CSV
#     # df[['date', 'cumulative_event_count']].drop_duplicates().to_csv(
#     #     os.path.join(save_folder, 'bitcoin_cumulative_event_count.csv'), index=False)

#     print("CSV files have been generated and saved to:", save_folder)

# except Exception as e:
#     print(f"查询过程中发生错误: {e}")


# Bips
# import pandas as pd
# import requests
# import os
# from io import StringIO

# # 数据库连接配置
# host = '172.28.1.2'
# port = 8123
# database = 'github'
# user = 'w3r'
# password = 'Web3Resear.ch'  # 如果有密码，请填写

# # 构造 SQL 查询
# query = """
# SELECT * 
# FROM events
# WHERE repository_id = '14531737'
# ORDER BY created_at
# FORMAT TabSeparatedWithNames
# """
# # WHERE repository_url = 'https://api.github.com/repos/aleph-zero-foundation/aleph-node'

# # ClickHouse HTTP 接口 URL
# url = f"http://{host}:{port}"

# # 查询参数
# params = {
#     'query': query,
#     'user': user,
#     'password': password,
#     'database': database
# }

# try:
#     # 发送 HTTP 请求
#     response = requests.get(url, params=params)
#     response.raise_for_status()  # 检查请求是否成功

#     # 将返回的 TSV 数据转换为 pandas DataFrame
#     data = response.text
#     df = pd.read_csv(StringIO(data), sep='\t')

#     # 确保字段名与预期一致（可选：如果字段名不匹配，可以手动指定）
#     expected_columns = ['id', 'event_type', 'actor_id', 'actor_login', 'actor_display_login', 'actor_gravatar_id', 
#                         'actor_url', 'actor_avatar_url', 'repository_id', 'repository_name', 'repository_url', 
#                         'org_id', 'org_login', 'org_gravatar_id', 'org_url', 'org_avatar_url', 'created_at', 
#                         'public', 'payload', 'other']
#     if list(df.columns) != expected_columns:
#         print("警告：返回的字段名与预期不一致，实际字段名：", list(df.columns))
#         df.columns = expected_columns  # 强制设置字段名（如果需要）

#     # 确定保存路径
#     save_folder = '/home/lab0/survival_diffusion_github/Bitcoin'

#     # 确保文件夹存在
#     os.makedirs(save_folder, exist_ok=True)

#     # 生成并保存第一个 CSV 文件：所有记录
#     df.to_csv(os.path.join(save_folder, 'bips_events_all_2025_12_31.csv'), index=False)

#     # 计算每天所有类型 event 的数量
#     df['created_at'] = pd.to_datetime(df['created_at'])  # 确保 created_at 字段是日期类型
#     df['date'] = df['created_at'].dt.date  # 提取日期部分

#     # 按照日期和 event_type 计算每个类型的数量
#     event_count_per_day = df.groupby(['date', 'event_type']).size().reset_index(name='event_count')

#     # 保存为 CSV
#     event_count_per_day.to_csv(os.path.join(save_folder, 'bips_event_count_per_day_2025_12_31.csv'), index=False)

#     # # 计算每天累积的 event 数量
#     # df['cumulative_event_count'] = df.groupby('date').cumcount() + 1

#     # # 保存为 CSV
#     # df[['date', 'cumulative_event_count']].drop_duplicates().to_csv(
#     #     os.path.join(save_folder, 'bitcoin_cumulative_event_count.csv'), index=False)

#     print("CSV files have been generated and saved to:", save_folder)

# except Exception as e:
#     print(f"查询过程中发生错误: {e}")



import pandas as pd
import requests
import os
from io import StringIO

# 数据库连接配置
host = '172.28.1.2'
port = 8123
database = 'github'
user = 'w3r'
password = 'Web3Resear.ch'  # 如果有密码，请填写

# 构造 SQL 查询
query = """
SELECT * 
FROM events
WHERE repository_id = '241285883'
ORDER BY created_at
FORMAT TabSeparatedWithNames
"""
# WHERE repository_url = 'https://api.github.com/repos/aleph-zero-foundation/aleph-node'

# ClickHouse HTTP 接口 URL
url = f"http://{host}:{port}"

# 查询参数
params = {
    'query': query,
    'user': user,
    'password': password,
    'database': database
}

try:
    # 发送 HTTP 请求
    response = requests.get(url, params=params)
    response.raise_for_status()  # 检查请求是否成功

    # 将返回的 TSV 数据转换为 pandas DataFrame
    data = response.text
    df = pd.read_csv(StringIO(data), sep='\t')

    # 确保字段名与预期一致（可选：如果字段名不匹配，可以手动指定）
    expected_columns = ['id', 'event_type', 'actor_id', 'actor_login', 'actor_display_login', 'actor_gravatar_id', 
                        'actor_url', 'actor_avatar_url', 'repository_id', 'repository_name', 'repository_url', 
                        'org_id', 'org_login', 'org_gravatar_id', 'org_url', 'org_avatar_url', 'created_at', 
                        'public', 'payload', 'other']
    if list(df.columns) != expected_columns:
        print("警告：返回的字段名与预期不一致，实际字段名：", list(df.columns))
        df.columns = expected_columns  # 强制设置字段名（如果需要）

    # 确定保存路径
    save_folder = '/home/lab0/survival_diffusion_github/Bitcoin'

    # 确保文件夹存在
    os.makedirs(save_folder, exist_ok=True)

    # 生成并保存第一个 CSV 文件：所有记录
    df.to_csv(os.path.join(save_folder, 'bitcoincashnode_events_all_2025_12_31.csv'), index=False)

    # 计算每天所有类型 event 的数量
    df['created_at'] = pd.to_datetime(df['created_at'])  # 确保 created_at 字段是日期类型
    df['date'] = df['created_at'].dt.date  # 提取日期部分

    # 按照日期和 event_type 计算每个类型的数量
    event_count_per_day = df.groupby(['date', 'event_type']).size().reset_index(name='event_count')

    # 保存为 CSV
    event_count_per_day.to_csv(os.path.join(save_folder, 'bitcoincashnode_event_count_per_day_2025_12_31.csv'), index=False)

    # # 计算每天累积的 event 数量
    # df['cumulative_event_count'] = df.groupby('date').cumcount() + 1

    # # 保存为 CSV
    # df[['date', 'cumulative_event_count']].drop_duplicates().to_csv(
    #     os.path.join(save_folder, 'bitcoin_cumulative_event_count.csv'), index=False)

    print("CSV files have been generated and saved to:", save_folder)

except Exception as e:
    print(f"查询过程中发生错误: {e}")