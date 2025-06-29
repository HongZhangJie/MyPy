import subprocess
import sys
import os

# 获取当前脚本所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))
target_script = os.path.join(base_dir, "BatchModifyDevIp_v1.6.py")

# 执行命令：python3 BatchModifyDevIp_v1.5.py -url
subprocess.run([sys.executable, target_script, "-url"])
