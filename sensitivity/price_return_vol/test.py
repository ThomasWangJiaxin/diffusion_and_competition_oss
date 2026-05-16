import subprocess
import sys
import time
from datetime import datetime

scripts = [
    "/home/lab0/survival_diffusion_github/sensitivity/price_return_vol/btc_20172019.py",
    "/home/lab0/survival_diffusion_github/sensitivity/price_return_vol/btc_20202022.py",
    "/home/lab0/survival_diffusion_github/sensitivity/price_return_vol/eth_20172019.py",
    "/home/lab0/survival_diffusion_github/sensitivity/price_return_vol/eth_20202023.py",
]

def run_script(script_path):
    print(f"\n{'='*70}")
    print(f"▶ 开始运行: {script_path}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=False,   # 直接输出到终端
        text=True
    )
    elapsed = time.time() - start
    if result.returncode == 0:
        print(f"\n✅ 完成: {script_path}  ({elapsed:.1f}s)")
    else:
        print(f"\n❌ 失败: {script_path}  (returncode={result.returncode}, {elapsed:.1f}s)")
    return result.returncode

def main():
    print(f"📋 共 {len(scripts)} 个脚本，依次运行...")
    total_start = time.time()
    results = {}
    for script in scripts:
        rc = run_script(script)
        results[script] = rc

    print(f"\n{'='*70}")
    print("📊 运行汇总")
    print(f"{'='*70}")
    for script, rc in results.items():
        name   = script.split('/')[-1]
        status = "✅ 成功" if rc == 0 else f"❌ 失败 (code={rc})"
        print(f"  {name:<30} {status}")
    total_elapsed = time.time() - total_start
    n_ok  = sum(1 for rc in results.values() if rc == 0)
    n_fail= len(results) - n_ok
    print(f"\n  总耗时: {total_elapsed:.1f}s  |  成功: {n_ok}  |  失败: {n_fail}")

if __name__ == "__main__":
    main()