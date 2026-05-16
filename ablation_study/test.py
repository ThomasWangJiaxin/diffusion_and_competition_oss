# #!/usr/bin/env python3
# """
# 第一步：自动运行 /home/lab0/survival_diffusion_github/ablation_study/ 下所有 .py 文件
# - 按文件名排序依次执行
# - 每个脚本独立进程运行，互不干扰
# - 记录每个脚本的运行状态、耗时和输出
# - 最终汇总成功/失败数量
# """
# import subprocess
# import sys
# import os
# import time
# from pathlib import Path

# ABLATION_DIR = Path("/home/lab0/survival_diffusion_github/ablation_study")
# LOG_DIR      = ABLATION_DIR / "run_logs"
# LOG_DIR.mkdir(exist_ok=True)

# PYTHON_BIN   = sys.executable   # 使用当前 Python 环境
# TIMEOUT_SEC  = 3600             # 每个脚本最长运行 1 小时

# def run_all():
#     # 收集所有 .py 文件，排除自身
#     this_file = Path(__file__).resolve()
#     py_files  = sorted([
#         f for f in ABLATION_DIR.glob("*.py")
#         if f.resolve() != this_file
#     ])

#     if not py_files:
#         print("⚠️  未找到任何 .py 文件，退出。")
#         return

#     print(f"📂 目录: {ABLATION_DIR}")
#     print(f"📋 共找到 {len(py_files)} 个脚本，按文件名顺序执行：")
#     for f in py_files:
#         print(f"   {f.name}")
#     print("=" * 70)

#     results = []

#     for idx, script in enumerate(py_files, 1):
#         log_path = LOG_DIR / (script.stem + ".log")
#         print(f"\n[{idx}/{len(py_files)}] 运行: {script.name}")
#         print(f"  日志: {log_path}")

#         t_start = time.time()
#         try:
#             with open(log_path, "w", encoding="utf-8") as log_f:
#                 proc = subprocess.run(
#                     [PYTHON_BIN, str(script)],
#                     stdout=log_f,
#                     stderr=subprocess.STDOUT,
#                     timeout=TIMEOUT_SEC,
#                     cwd=str(ABLATION_DIR),   # 工作目录设为 ablation_study
#                 )
#             elapsed = time.time() - t_start
#             if proc.returncode == 0:
#                 status = "✅ 成功"
#             else:
#                 status = f"❌ 失败 (returncode={proc.returncode})"
#         except subprocess.TimeoutExpired:
#             elapsed = time.time() - t_start
#             status  = f"⏰ 超时 (>{TIMEOUT_SEC}s)"
#         except Exception as e:
#             elapsed = time.time() - t_start
#             status  = f"💥 异常: {e}"

#         print(f"  {status}  耗时: {elapsed:.1f}s")

#         # 如果失败，打印最后 20 行日志帮助定位
#         if "成功" not in status:
#             try:
#                 lines = log_path.read_text(encoding="utf-8").splitlines()
#                 tail  = lines[-20:] if len(lines) >= 20 else lines
#                 print("  --- 日志末尾 ---")
#                 for line in tail:
#                     print(f"  {line}")
#                 print("  ----------------")
#             except Exception:
#                 pass

#         results.append({
#             "script":  script.name,
#             "status":  status,
#             "elapsed": elapsed,
#         })

#     # 汇总
#     print("\n" + "=" * 70)
#     print("📊 运行汇总：")
#     n_ok   = sum(1 for r in results if "成功" in r["status"])
#     n_fail = len(results) - n_ok
#     for r in results:
#         print(f"  {r['status']:30s}  {r['elapsed']:6.1f}s  {r['script']}")
#     print(f"\n  共 {len(results)} 个脚本：✅ {n_ok} 成功  ❌ {n_fail} 失败/超时")
#     print(f"  日志保存在: {LOG_DIR}")

# if __name__ == "__main__":
#     run_all()


# !/usr/bin/env python3
"""
第二步：将 /home/lab0/survival_diffusion_github/ablation_study/ 下的 CSV 文件
按文件名分成四类并合并：
  - btc_20172019  (含 btc 且含 2017 或 20172019)
  - btc_20202022  (含 btc 且含 2020 或 20202022)
  - eth_20172019  (含 eth 且含 2017 或 20172019)
  - eth_20202023  (含 eth 且含 2020 或 20202023)
同一类内各 CSV 列名可能不同，合并时保留所有列（outer join），缺失填 NaN。
"""
from pathlib import Path
import pandas as pd
import re

ABLATION_DIR = Path("/home/lab0/survival_diffusion_github/ablation_study")

# 四类的匹配规则：(输出文件名, 判断函数)
def make_classifier():
    rules = [
        ("btc_20172019", lambda s: "btc" in s and ("20172019" in s or ("2017" in s and "2019" in s))),
        ("btc_20202022", lambda s: "btc" in s and ("20202022" in s or ("2020" in s and "2022" in s))),
        ("eth_20172019", lambda s: "eth" in s and ("20172019" in s or ("2017" in s and "2019" in s))),
        ("eth_20202023", lambda s: "eth" in s and ("20202023" in s or ("2020" in s and "2023" in s))),
    ]
    return rules

def classify(filename: str, rules):
    s = filename.lower()
    for group_name, match_fn in rules:
        if match_fn(s):
            return group_name
    return None

def merge_group(csv_files: list[Path]) -> pd.DataFrame:
    """
    合并同一组内所有 CSV，列不同时取并集（outer），缺失填 NaN。
    新增 source_file 列记录来源。
    """
    dfs = []
    for f in sorted(csv_files):
        try:
            df = pd.read_csv(f)
            df.insert(0, "source_file", f.name)
            dfs.append(df)
            print(f"    ✅ 读取 {f.name}  ({len(df)} 行, {len(df.columns)} 列)")
        except Exception as e:
            print(f"    ⚠️  读取失败 {f.name}: {e}")

    if not dfs:
        return pd.DataFrame()

    # 取所有列的并集，缺失填 NaN
    merged = pd.concat(dfs, axis=0, ignore_index=True, sort=False)
    return merged

def main():
    rules = make_classifier()

    # 收集所有 CSV（排除输出文件本身）
    output_names = {f"merged_{r[0]}.csv" for r in rules}
    csv_files = [
        f for f in ABLATION_DIR.glob("*.csv")
        if f.name not in output_names
    ]

    if not csv_files:
        print("⚠️  未找到任何 CSV 文件。")
        return

    print(f"📂 目录: {ABLATION_DIR}")
    print(f"📋 共找到 {len(csv_files)} 个 CSV 文件\n")

    # 分组
    groups: dict[str, list[Path]] = {r[0]: [] for r in rules}
    unclassified = []

    for f in csv_files:
        group = classify(f.name, rules)
        if group:
            groups[group].append(f)
        else:
            unclassified.append(f.name)

    # 逐组合并并保存
    for group_name, files in groups.items():
        print(f"\n{'='*60}")
        print(f"📁 组: {group_name}  ({len(files)} 个文件)")
        if not files:
            print("    （无文件，跳过）")
            continue

        merged = merge_group(files)
        if merged.empty:
            print("    （合并结果为空，跳过）")
            continue

        out_path = ABLATION_DIR / f"merged_{group_name}.csv"
        merged.to_csv(out_path, index=False)
        print(f"  → 已保存: {out_path.name}  "
              f"({len(merged)} 行, {len(merged.columns)} 列)")

    # 未分类文件提示
    if unclassified:
        print(f"\n⚠️  以下文件未匹配任何分类，已跳过:")
        for name in unclassified:
            print(f"    {name}")

    print("\n✅ 全部完成。")

if __name__ == "__main__":
    main()

