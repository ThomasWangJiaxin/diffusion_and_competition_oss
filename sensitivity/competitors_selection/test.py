import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 目录列表
directories = [
    "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection/100",
    "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection/200",
    "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection/300",
    "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection/400",
    "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection/500",
    "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection/600",
    "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection/1000",
]

# 创建日志文件夹
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 收集所有 Python 文件
py_files = []
for dir_path in directories:
    for root, _, files in os.walk(dir_path):
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

print(f"找到 {len(py_files)} 个 Python 文件，开始并行运行...\n")

# 并行运行函数
def run_script(py_file):
    rel_path = os.path.relpath(py_file, "/home/lab0/survival_diffusion_github/sensitivity/competitors_selection")
    log_file = os.path.join(LOG_DIR, rel_path.replace("/", "_") + ".log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    start_time = time.time()
    try:
        result = subprocess.run(
            ["python3", py_file],
            capture_output=True,
            text=True,
            check=False
        )
        elapsed = time.time() - start_time
        
        # 写入日志
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== STDOUT ===\n{result.stdout}\n\n")
            f.write(f"=== STDERR ===\n{result.stderr}\n")
        
        status = "成功" if result.returncode == 0 else "失败"
        return (py_file, status, elapsed)
    except Exception as e:
        elapsed = time.time() - start_time
        return (py_file, f"异常: {e}", elapsed)

# 设置并行线程数（根据机器核数调整）
MAX_WORKERS = min(8, os.cpu_count() or 4)

summary = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(run_script, py_file): py_file for py_file in py_files}
    for future in as_completed(futures):
        py_file, status, t_sec = future.result()
        summary.append((py_file, status, t_sec))
        print(f"{py_file} -> {status}, 耗时 {t_sec:.2f}s")

# 打印最终汇总
print("\n批量运行完成，汇总报告:\n")
for file, status, t_sec in summary:
    print(f"{file} -> {status}, 耗时 {t_sec:.2f}s")