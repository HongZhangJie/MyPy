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

API_HOST = "10.2.172.69:18081"
USERNAME = "gongdan"
TOKEN = "shterm1234*"
LOG_DIR = "./"

ASSET_COUNTS = {
    "linux": 20,
    "windows": 20,
    "network": 10,
    "cs": 10,
    "bs": 10
}
TEST_SIZES = [5, 20, 50, 100, 200, 300, 500, 1000]

def init_logger(suffix):
    global logger
    logger = logging.getLogger(f"BatchLogger_{suffix}")
    logger.setLevel(logging.INFO)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_file = f"{LOG_DIR}{timestamp}_BatchCreate_{suffix}.log"
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

def generate_assets(asset_type, count, start_index=1):
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
    for i in range(start_index, start_index + count):
        name = f"{sys_types[asset_type]}_device{i:05d}"
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
            asset["url"] = "https://xxx.com/"
            asset["clients"] = "postgres-dbeaver"
        assets.append({"devs": [asset]} if asset_type != "bs" else asset)
    return assets

def create_devs(ip, token, dev_list, account):
    url = f"https://{ip}/shterm/api/dev"
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

def create_worksheet(ip, token, assets, account):
    url = f"https://{ip}/shterm/api/worksheet"
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
        "endTime": "2025-04-25 20:00",
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

def execute_batch(total_count):
    init_logger(f"{total_count}")
    log("info", f"开始推送总计 {total_count} 台资产")

    all_assets_raw = []
    all_assets_flat = []

    total_weight = sum(ASSET_COUNTS.values())
    temp_count = 0
    per_type_count = {}

    for asset_type, weight in ASSET_COUNTS.items():
        count = round(weight / total_weight * total_count)
        per_type_count[asset_type] = count
        temp_count += count

    diff = total_count - temp_count
    if diff != 0:
        sorted_types = sorted(ASSET_COUNTS.items(), key=lambda x: -x[1])
        for i in range(abs(diff)):
            t = sorted_types[i % len(sorted_types)][0]
            per_type_count[t] += 1 if diff > 0 else -1

    for asset_type, count in per_type_count.items():
        assets = generate_assets(asset_type, count)
        all_assets_raw += assets
        if asset_type != "bs":
            all_assets_flat += [item["devs"][0] for item in assets]
        else:
            all_assets_flat += assets

    flat_assets = [item for sublist in all_assets_raw for item in (sublist["devs"] if "devs" in sublist else [sublist])]

    log("info", f"准备推送资产和工单，共计资产：{len(flat_assets)}")

    # 推送资产
    start_time = time.time()
    create_devs(API_HOST, TOKEN, flat_assets, USERNAME)
    log("info", f"送资产完成，用时 {time.time() - start_time:.2f} 秒")

    # 推送工单
    start_time = time.time()
    create_worksheet(API_HOST, TOKEN, all_assets_flat, USERNAME)
    log("info", f"推送工单完成，用时 {time.time() - start_time:.2f} 秒")

    log("info", f"{total_count} 台资产推送完成\n")

if __name__ == '__main__':
    try:
        for size in TEST_SIZES:
            execute_batch(size)
    except Exception as e:
        log("error", f"程序异常: {e}")
