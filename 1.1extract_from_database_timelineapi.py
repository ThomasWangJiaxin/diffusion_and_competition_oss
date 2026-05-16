# 基于 Timeline API 时代（2011.2.12-2014.12.31）和 Events API 时代（2015-01-01～至今）数据的整合和清洗结果
# Timeline API中repo id url name都要么缺要么不一样：
# 2011-02-12 00:34:35～2013-03-24 20:41:13 有repo id，但url = https://api.github.dev/repos/bitcoin/bitcoin，repo name=bitcoin/bitcoin同时也无actor任何信息
# 2012-03-11 14:51:08～2012-09-21 16:02:27 无repo id，但有url= https://github.com/bitcoin/bitcoin，且repo name = bitcoin，无actor id，但有actor email，name，url等

# # =======================================================
# # Bitcoin
# import pandas as pd
# import requests
# import os
# from io import StringIO
# from datetime import datetime

# # --- 数据库连接配置 ---
# HOST = '172.28.1.2'
# PORT = 8123  # 使用 HTTP 端口
# DATABASE = 'github'
# USER = 'w3r'
# PASSWORD = 'Web3Resear.ch'

# # --- 任务配置 ---
# TARGET_REPO_ID = '1181927'  # Bitcoin
# OUTPUT_FOLDER = '/home/lab0/survival_diffusion_github/Bitcoin' # 定义一个清晰的输出文件夹
# OUTPUT_FILE = f'bitcoin_timeline_events_all.csv'

# # --- 构造 SQL 查询 (修正后的联合查询) ---
# # 目标：捕获所有已知的有效记录，包括 ID 缺失和 URL 格式不一致的记录。
# query = f"""
# SELECT * FROM github.timeline
# WHERE 
#     -- 1. 使用稳定的数字 ID (捕获 ID 正确的记录，包括 Timeline V1 和 Event API)
#     repository_id = '{TARGET_REPO_ID}'
    
#     OR
    
#     -- 2. 使用外部 HTML URL (捕获 Timeline V2 的记录)
#     repository_url = 'https://github.com/bitcoin/bitcoin'
    
#     OR
    
#     -- 3. 使用内部 API URL
#     repository_url = 'https://api.github.dev/repos/bitcoin/bitcoin' 

# ORDER BY created_at ASC
# FORMAT CSVWithNames
# """

# # ClickHouse HTTP 接口 URL
# URL = f"http://{HOST}:{PORT}"

# # 查询参数
# params = {
#     'query': query,
#     'user': USER,
#     'password': PASSWORD,
#     'database': DATABASE
# }

# def fetch_and_export():
#     """执行 ClickHouse 查询并将结果导出为 CSV。"""
    
#     print(f"✅ 正在连接 ClickHouse HTTP 接口: {URL}/{DATABASE}")
    
#     try:
#         # 1. 检查并创建保存文件夹
#         os.makedirs(OUTPUT_FOLDER, exist_ok=True)
#         save_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)

#         # 2. 发送 HTTP 请求获取数据
#         start_time = datetime.now()
#         print(f"⏳ 正在执行联合查询以获取 Bitcoin Core 所有记录...")
        
#         response = requests.get(URL, params=params, stream=True)
#         response.raise_for_status()  # 检查请求是否成功

#         # 3. 将返回的 CSV 数据流转换为 pandas DataFrame
#         # 注意：使用 response.iter_lines() 逐行读取，处理大数据更安全
#         data_io = StringIO()
        
#         # 逐行读取数据
#         for line in response.iter_lines(decode_unicode=True):
#             data_io.write(line + '\n')
        
#         data_io.seek(0)
        
#         # 4. 读取 CSV 到 DataFrame
#         # 强制sep=',' 因为我们使用了 FORMAT CSVWithNames
#         df = pd.read_csv(data_io, sep=',', header=0) 

#         # 5. 输出记录总数
#         total_records = len(df)
#         end_time = datetime.now()
#         duration = (end_time - start_time).total_seconds()
        
#         print(f"✅ 查询完成。共获取 {total_records} 条记录，耗时 {duration:.2f} 秒。")

#         # 6. 保存为 CSV
#         df.to_csv(save_path, index=False, encoding='utf-8')

#         print(f"🎉 数据已成功导出。总记录数: {total_records}")
#         print(f"文件保存路径: {save_path}")
        
#         # 额外提示：你可以对 actor_login 和 repository_id 进行清洗，解决 Period 1 的 actor 缺失问题

#     except requests.exceptions.HTTPError as http_err:
#         print(f"❌ HTTP 请求错误: {http_err}")
#         print(f"服务器返回状态码: {response.status_code}")
#         print(f"错误内容 (可能): {response.text}")
#     except Exception as e:
#         print(f"❌ 发生错误: {e}")

# if __name__ == "__main__":
#     fetch_and_export()



# =======================================================
# Ethereum
# import pandas as pd
# import requests
# import os
# from io import StringIO
# from datetime import datetime

# # --- 数据库连接配置 ---
# HOST = '172.28.1.2'
# PORT = 8123  # 使用 HTTP 端口
# DATABASE = 'github'
# USER = 'w3r'
# PASSWORD = 'Web3Resear.ch'

# # --- 任务配置 ---
# TARGET_REPO_ID = '15452919'
# OUTPUT_FOLDER = '/home/lab0/survival_diffusion_github/Ethereum' # 定义一个清晰的输出文件夹
# OUTPUT_FILE = f'eth_timeline_events_all.csv'

# # --- 构造 SQL 查询 (修正后的联合查询) ---
# # 目标：捕获所有已知的有效记录，包括 ID 缺失和 URL 格式不一致的记录。
# query = f"""
# SELECT * FROM github.timeline
# WHERE 
#     -- 1. 使用稳定的数字 ID (捕获 ID 正确的记录，包括 Timeline V1 和 Event API)
#     repository_id = '{TARGET_REPO_ID}'
#     OR
#     -- 2. 使用外部 HTML URL (捕获 Timeline V2 的记录)
#     repository_url = 'https://github.com/ethereum/go-ethereum'

# ORDER BY created_at ASC
# FORMAT CSVWithNames
# """

# # ClickHouse HTTP 接口 URL
# URL = f"http://{HOST}:{PORT}"

# # 查询参数
# params = {
#     'query': query,
#     'user': USER,
#     'password': PASSWORD,
#     'database': DATABASE
# }

# def fetch_and_export():
#     """执行 ClickHouse 查询并将结果导出为 CSV。"""
    
#     print(f"✅ 正在连接 ClickHouse HTTP 接口: {URL}/{DATABASE}")
    
#     try:
#         # 1. 检查并创建保存文件夹
#         os.makedirs(OUTPUT_FOLDER, exist_ok=True)
#         save_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)

#         # 2. 发送 HTTP 请求获取数据
#         start_time = datetime.now()
#         print(f"⏳ 正在执行联合查询以获取 Bitcoin Core 所有记录...")
        
#         response = requests.get(URL, params=params, stream=True)
#         response.raise_for_status()  # 检查请求是否成功

#         # 3. 将返回的 CSV 数据流转换为 pandas DataFrame
#         # 注意：使用 response.iter_lines() 逐行读取，处理大数据更安全
#         data_io = StringIO()
        
#         # 逐行读取数据
#         for line in response.iter_lines(decode_unicode=True):
#             data_io.write(line + '\n')
        
#         data_io.seek(0)
        
#         # 4. 读取 CSV 到 DataFrame
#         # 强制sep=',' 因为我们使用了 FORMAT CSVWithNames
#         df = pd.read_csv(data_io, sep=',', header=0) 

#         # 5. 输出记录总数
#         total_records = len(df)
#         end_time = datetime.now()
#         duration = (end_time - start_time).total_seconds()
        
#         print(f"✅ 查询完成。共获取 {total_records} 条记录，耗时 {duration:.2f} 秒。")

#         # 6. 保存为 CSV
#         df.to_csv(save_path, index=False, encoding='utf-8')

#         print(f"🎉 数据已成功导出。总记录数: {total_records}")
#         print(f"文件保存路径: {save_path}")
        
#         # 额外提示：你可以对 actor_login 和 repository_id 进行清洗，解决 Period 1 的 actor 缺失问题

#     except requests.exceptions.HTTPError as http_err:
#         print(f"❌ HTTP 请求错误: {http_err}")
#         print(f"服务器返回状态码: {response.status_code}")
#         print(f"错误内容 (可能): {response.text}")
#     except Exception as e:
#         print(f"❌ 发生错误: {e}")

# if __name__ == "__main__":
#     fetch_and_export()



# ========================================
# BIPs
# import pandas as pd
# import requests
# import os
# from io import StringIO
# from datetime import datetime

# # --- 数据库连接配置 ---
# HOST = '172.28.1.2'
# PORT = 8123  # 使用 HTTP 端口
# DATABASE = 'github'
# USER = 'w3r'
# PASSWORD = 'Web3Resear.ch'

# # --- 任务配置 ---
# TARGET_REPO_ID = '14531737'
# OUTPUT_FOLDER = '/home/lab0/survival_diffusion_github/Bitcoin' # 定义一个清晰的输出文件夹
# OUTPUT_FILE = f'bips_timeline_events_all.csv'

# # --- 构造 SQL 查询 (修正后的联合查询) ---
# # 目标：捕获所有已知的有效记录，包括 ID 缺失和 URL 格式不一致的记录。
# query = f"""
# SELECT * FROM github.timeline
# WHERE 
#     -- 1. 使用稳定的数字 ID (捕获 ID 正确的记录，包括 Timeline V1 和 Event API)
#     repository_id = '{TARGET_REPO_ID}'
#     OR
#     -- 2. 使用外部 HTML URL (捕获 Timeline V2 的记录)
#     repository_url = 'https://github.com/bitcoin/bips'

# ORDER BY created_at ASC
# FORMAT CSVWithNames
# """

# # ClickHouse HTTP 接口 URL
# URL = f"http://{HOST}:{PORT}"

# # 查询参数
# params = {
#     'query': query,
#     'user': USER,
#     'password': PASSWORD,
#     'database': DATABASE
# }

# def fetch_and_export():
#     """执行 ClickHouse 查询并将结果导出为 CSV。"""
    
#     print(f"✅ 正在连接 ClickHouse HTTP 接口: {URL}/{DATABASE}")
    
#     try:
#         # 1. 检查并创建保存文件夹
#         os.makedirs(OUTPUT_FOLDER, exist_ok=True)
#         save_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)

#         # 2. 发送 HTTP 请求获取数据
#         start_time = datetime.now()
#         print(f"⏳ 正在执行联合查询以获取 Bips 所有记录...")
        
#         response = requests.get(URL, params=params, stream=True)
#         response.raise_for_status()  # 检查请求是否成功

#         # 3. 将返回的 CSV 数据流转换为 pandas DataFrame
#         # 注意：使用 response.iter_lines() 逐行读取，处理大数据更安全
#         data_io = StringIO()
        
#         # 逐行读取数据
#         for line in response.iter_lines(decode_unicode=True):
#             data_io.write(line + '\n')
        
#         data_io.seek(0)
        
#         # 4. 读取 CSV 到 DataFrame
#         # 强制sep=',' 因为我们使用了 FORMAT CSVWithNames
#         df = pd.read_csv(data_io, sep=',', header=0) 

#         # 5. 输出记录总数
#         total_records = len(df)
#         end_time = datetime.now()
#         duration = (end_time - start_time).total_seconds()
        
#         print(f"✅ 查询完成。共获取 {total_records} 条记录，耗时 {duration:.2f} 秒。")

#         # 6. 保存为 CSV
#         df.to_csv(save_path, index=False, encoding='utf-8')

#         print(f"🎉 数据已成功导出。总记录数: {total_records}")
#         print(f"文件保存路径: {save_path}")
        
#         # 额外提示：你可以对 actor_login 和 repository_id 进行清洗，解决 Period 1 的 actor 缺失问题

#     except requests.exceptions.HTTPError as http_err:
#         print(f"❌ HTTP 请求错误: {http_err}")
#         print(f"服务器返回状态码: {response.status_code}")
#         print(f"错误内容 (可能): {response.text}")
#     except Exception as e:
#         print(f"❌ 发生错误: {e}")

# if __name__ == "__main__":
#     fetch_and_export()


# # =======================================================
# # Litecoin
# import pandas as pd
# import requests
# import os
# from io import StringIO
# from datetime import datetime

# # --- 数据库连接配置 ---
# HOST = '172.28.1.2'
# PORT = 8123  # 使用 HTTP 端口
# DATABASE = 'github'
# USER = 'w3r'
# PASSWORD = 'Web3Resear.ch'

# # --- 任务配置 ---
# TARGET_REPO_ID = '4646198'
# OUTPUT_FOLDER = '/home/lab0/survival_diffusion_github/Bitcoin_compete' # 定义一个清晰的输出文件夹
# OUTPUT_FILE = f'litecoin_timeline_events_all.csv'

# # --- 构造 SQL 查询 (修正后的联合查询) ---
# # 目标：捕获所有已知的有效记录，包括 ID 缺失和 URL 格式不一致的记录。
# query = f"""
# SELECT * FROM github.timeline
# WHERE 
#     -- 1. 使用稳定的数字 ID (捕获 ID 正确的记录，包括 Timeline V1 和 Event API)
#     repository_id = '{TARGET_REPO_ID}'
    
#     OR
    
#     -- 2. 使用外部 HTML URL (捕获 Timeline V2 的记录) LITECOIN Timeline Event没有https://api.github.dev/repos/litecoin-project/litecoin
#     repository_url = 'https://github.com/litecoin-project/litecoin'

# ORDER BY created_at ASC
# FORMAT CSVWithNames
# """

# # ClickHouse HTTP 接口 URL
# URL = f"http://{HOST}:{PORT}"

# # 查询参数
# params = {
#     'query': query,
#     'user': USER,
#     'password': PASSWORD,
#     'database': DATABASE
# }

# def fetch_and_export():
#     """执行 ClickHouse 查询并将结果导出为 CSV。"""
    
#     print(f"✅ 正在连接 ClickHouse HTTP 接口: {URL}/{DATABASE}")
    
#     try:
#         # 1. 检查并创建保存文件夹
#         os.makedirs(OUTPUT_FOLDER, exist_ok=True)
#         save_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)

#         # 2. 发送 HTTP 请求获取数据
#         start_time = datetime.now()
#         print(f"⏳ 正在执行联合查询以获取 Litecoin 所有记录...")
        
#         response = requests.get(URL, params=params, stream=True)
#         response.raise_for_status()  # 检查请求是否成功

#         # 3. 将返回的 CSV 数据流转换为 pandas DataFrame
#         # 注意：使用 response.iter_lines() 逐行读取，处理大数据更安全
#         data_io = StringIO()
        
#         # 逐行读取数据
#         for line in response.iter_lines(decode_unicode=True):
#             data_io.write(line + '\n')
        
#         data_io.seek(0)
        
#         # 4. 读取 CSV 到 DataFrame
#         # 强制sep=',' 因为我们使用了 FORMAT CSVWithNames
#         df = pd.read_csv(data_io, sep=',', header=0) 

#         # 5. 输出记录总数
#         total_records = len(df)
#         end_time = datetime.now()
#         duration = (end_time - start_time).total_seconds()
        
#         print(f"✅ 查询完成。共获取 {total_records} 条记录，耗时 {duration:.2f} 秒。")

#         # 6. 保存为 CSV
#         df.to_csv(save_path, index=False, encoding='utf-8')

#         print(f"🎉 数据已成功导出。总记录数: {total_records}")
#         print(f"文件保存路径: {save_path}")
        
#         # 额外提示：你可以对 actor_login 和 repository_id 进行清洗，解决 Period 1 的 actor 缺失问题

#     except requests.exceptions.HTTPError as http_err:
#         print(f"❌ HTTP 请求错误: {http_err}")
#         print(f"服务器返回状态码: {response.status_code}")
#         print(f"错误内容 (可能): {response.text}")
#     except Exception as e:
#         print(f"❌ 发生错误: {e}")

# if __name__ == "__main__":
#     fetch_and_export()


# =======================================================
# Dogecoin
import pandas as pd
import requests
import os
from io import StringIO
from datetime import datetime

# --- 数据库连接配置 ---
HOST = '172.28.1.2'
PORT = 8123  # 使用 HTTP 端口
DATABASE = 'github'
USER = 'w3r'
PASSWORD = 'Web3Resear.ch'

# --- 任务配置 ---
TARGET_REPO_ID = '19316619'
OUTPUT_FOLDER = '/home/lab0/survival_diffusion_github/Bitcoin_compete' # 定义一个清晰的输出文件夹
OUTPUT_FILE = f'monero_timeline_events_all.csv'

# --- 构造 SQL 查询 (修正后的联合查询) ---
# 目标：捕获所有已知的有效记录，包括 ID 缺失和 URL 格式不一致的记录。
query = f"""
SELECT * FROM github.timeline
WHERE 
    -- 1. 使用稳定的数字 ID (捕获 ID 正确的记录，包括 Timeline V1 和 Event API)
    repository_id = '{TARGET_REPO_ID}'
    
    OR
    
    -- 2. 使用外部 HTML URL (捕获 Timeline V2 的记录) DogeCOIN Timeline Event没有https://api.github.dev/repos/dogecoin/dogecoin
    repository_url = 'https://github.com/monero-project/bitmonero'

ORDER BY created_at ASC
FORMAT CSVWithNames
"""

# ClickHouse HTTP 接口 URL
URL = f"http://{HOST}:{PORT}"

# 查询参数
params = {
    'query': query,
    'user': USER,
    'password': PASSWORD,
    'database': DATABASE
}

def fetch_and_export():
    """执行 ClickHouse 查询并将结果导出为 CSV。"""
    
    print(f"✅ 正在连接 ClickHouse HTTP 接口: {URL}/{DATABASE}")
    
    try:
        # 1. 检查并创建保存文件夹
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        save_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)

        # 2. 发送 HTTP 请求获取数据
        start_time = datetime.now()
        print(f"⏳ 正在执行联合查询以获取 Dogecoin 所有记录...")
        
        response = requests.get(URL, params=params, stream=True)
        response.raise_for_status()  # 检查请求是否成功

        # 3. 将返回的 CSV 数据流转换为 pandas DataFrame
        # 注意：使用 response.iter_lines() 逐行读取，处理大数据更安全
        data_io = StringIO()
        
        # 逐行读取数据
        for line in response.iter_lines(decode_unicode=True):
            data_io.write(line + '\n')
        
        data_io.seek(0)
        
        # 4. 读取 CSV 到 DataFrame
        # 强制sep=',' 因为我们使用了 FORMAT CSVWithNames
        df = pd.read_csv(data_io, sep=',', header=0) 

        # 5. 输出记录总数
        total_records = len(df)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ 查询完成。共获取 {total_records} 条记录，耗时 {duration:.2f} 秒。")

        # 6. 保存为 CSV
        df.to_csv(save_path, index=False, encoding='utf-8')

        print(f"🎉 数据已成功导出。总记录数: {total_records}")
        print(f"文件保存路径: {save_path}")
        
        # 额外提示：你可以对 actor_login 和 repository_id 进行清洗，解决 Period 1 的 actor 缺失问题

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP 请求错误: {http_err}")
        print(f"服务器返回状态码: {response.status_code}")
        print(f"错误内容 (可能): {response.text}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    fetch_and_export()