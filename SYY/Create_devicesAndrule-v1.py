import requests
import urllib3
import time
import sys
import logging
import logging.handlers
import json
import traceback
from datetime import datetime

urllib3.disable_warnings()

# =========================== 配置区域 ===========================
API_HOST = "10.2.172.69:18081"
USERNAME = "gongdan"
TOKEN = "shterm1234*"
LOG_DIR = "./"
ASSET_COUNTS = [
    {
        "linux": 2,
        "windows": 1,
        "network": 1,
        "cs": 1,
        "bs": 1
    },
    {
        "linux": 16,
        "windows": 2,
        "network": 1,
        "cs": 1,
        "bs": 1
    },
    {
        "linux": 40,
        "windows": 5,
        "network": 2,
        "cs": 2,
        "bs": 1
    },
    {
        "linux": 80,
        "windows": 10,
        "network": 5,
        "cs": 3,
        "bs": 2
    },
    {
        "linux": 160,
        "windows": 20,
        "network": 10,
        "cs": 5,
        "bs": 5
    },
    {
        "linux": 240,
        "windows": 30,
        "network": 15,
        "cs": 10,
        "bs": 5
    },
    {
        "linux": 400,
        "windows": 50,
        "network": 25,
        "cs": 15,
        "bs": 10
    },
    {
        "linux": 550,
        "windows": 50,
        "network": 25,
        "cs": 15,
        "bs": 10
    },
    {
        "linux": 650,
        "windows": 50,
        "network": 25,
        "cs": 15,
        "bs": 10
    },
    {
        "linux": 1000,
        "windows": 100,
        "network": 50,
        "cs": 30,
        "bs": 20
    },
    {
        "linux": 1200,
        "windows": 100,
        "network": 50,
        "cs": 30,
        "bs": 20
    },
    {
        "linux": 1500,
        "windows": 100,
        "network": 50,
        "cs": 30,
        "bs": 20
    },
    {
        "linux": 1800,
        "windows": 100,
        "network": 50,
        "cs": 30,
        "bs": 20
    }
]

# ======================== 日志初始化 ===========================
def init_logger():
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file = f"{LOG_DIR}{timestamp}_BatchCreate.log"
    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=200 * 1024 * 1024, backupCount=4)
    formatter = logging.Formatter("[%(asctime)s %(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log(level, msg):
    getattr(logger, level)(msg)
    print(msg)
    if level in ["warn", "error"]:
        logger.error(traceback.format_exc())
    if level == "error":
        sys.exit()

# ======================== 数据构造函数 ===========================
def generate_assets(asset_type, count):
    base_ip = {
        "linux": "10.0.0.",
        "windows": "10.0.1.",
        "network": "10.0.2.",
        "cs": "10.0.3.",
        "bs": "10.0.4."
    }
    sys_types = {
        "linux": "Linux",
        "windows": "Windows",
        "network": "General Network",
        "cs": "C/S",
        "bs": "B/S"
    }
    services = {
        "linux": {"protocol": "ssh", "port": 10022},
        "windows": {"protocol": "rdp", "port": 13389},
        "network": {"protocol": "ssh", "port": 10022},
    }

    assets = []
    for i in range(1, count + 1):
        name = f"{sys_types[asset_type]}_devicea{i:05d}"
        ip = f"{base_ip[asset_type]}{i % 255}"
        asset = {
            "name": name,
            "ip": ip,
            "type": 3 if asset_type in ["cs", "bs"] else 0 if asset_type in ["linux", "windows"] else 1,
            "sysType": sys_types[asset_type]
        }
        if asset_type in ["linux", "windows", "network"]:
            asset["services"] = [services[asset_type]]
        if asset_type == "cs":
            asset["clients"] = "mysql-dbeaver"
        if asset_type == "bs":
            asset["url"] = "https://10.2.173.77/shterm"
            asset["clients"] = "chrome"
        assets.append({"devs": [asset]} if asset_type != "bs" else asset)
    return assets

# ======================== 推送资产 ===========================
def create_devs(ip, token, dev_list, account):
    url = f"https://{ip}/api/devBatch"
    headers = {
        "account": account,
        "api_token": token,
        "Content-Type": "application/json"
    }
    body = {
        "orgcode": "00",
        "devs": dev_list
    }
    try:
        resp = requests.post(url, json=body, headers=headers, verify=False)
        if resp.status_code == 200:
            log("info", f"资产推送成功: {resp.text}")
        else:
            log("warn", f"资产推送失败: {resp.status_code} - {resp.text}")
    except Exception as e:
        log("error", f"资产推送异常: {e}")

# ======================== 构造工单并推送 ===========================
def create_worksheet(ip, token, assets, account):
    url = f"https://{ip}/api/worksheet"
    headers = {
        "account": account,
        "api_token": token,
        "Content-Type": "application/json"
    }
    targets = []
    for asset in assets:
        asset_name = asset["name"]
        asset_ip = asset["ip"]
        sys_type = asset.get("sysType", "")
        service = "ssh" if sys_type in ["Linux", "General Network"] else "rdp"
        targets.append({"id": asset_name, "ip": asset_ip, "account": "any", "service": service})
    body = {
        "userlist": "henry",
        "iosuser": "peizhi",
        "orderid": "temp001",
        "title": "gongdan001",
        "orgcode": "00",
        "beginTime": "2023-03-31 00:00",
        "endTime": "2025-06-15 20:00",
        "targets": targets
    }
    try:
        resp = requests.post(url, json=body, headers=headers, verify=False)
        if resp.status_code == 200:
            log("info", f"工单推送成功: {resp.text}")
        else:
            log("warn", f"工单推送失败: {resp.status_code} - {resp.text}")
    except Exception as e:
        log("error", f"工单请求异常: {e}")


# ============================ 主程序 ============================
def main():
    init_logger()
    log("info", "开始批量推送资产与工单...")

    for scenario_index, asset_counts in enumerate(ASSET_COUNTS, 1):
        log("info", f"\n{'='*40}")
        log("info", f"开始处理场景 {scenario_index} (总数: {sum(asset_counts.values())})")
        log("info", f"资产配置: {asset_counts}")
        log("info", f"{'='*40}")

        all_assets_raw = []
        all_assets_flat = []
        for asset_type, count in asset_counts.items():
            assets = generate_assets(asset_type, count)
            all_assets_raw += assets
            if asset_type != "bs":
                all_assets_flat += [item["devs"][0] for item in assets]
            else:
                all_assets_flat += assets

        # 推送资产
        log("info", "开始推送资产...")
        start_time = time.time()
        create_devs(API_HOST, TOKEN, 
                   [item for sublist in all_assets_raw 
                    for item in (sublist["devs"] if "devs" in sublist else [sublist])], 
                   USERNAME)
        end_time = time.time()
        log("info", f"场景 {scenario_index} 资产提交完成，用时 {end_time - start_time:.2f} 秒")

        # 推送工单
        log("info", "开始推送工单...")
        start_time = time.time()
        create_worksheet(API_HOST, TOKEN, all_assets_flat, USERNAME)
        end_time = time.time()
        log("info", f"场景 {scenario_index} 工单提交完成，用时 {end_time - start_time:.2f} 秒")

        # 场景间延迟，避免压力过大
        if scenario_index < len(ASSET_COUNTS):
            delay_seconds = 5
            log("info", f"等待 {delay_seconds} 秒后处理下一个场景...")
            time.sleep(delay_seconds)

    log("info", "全部场景处理完成")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log("error", f"程序异常: {e}")
