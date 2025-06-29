

#!/bin/python3
# update time : 20250421
# just update user state where user state in 2

import requests
import urllib3
import time
import sys
import logging
import logging.handlers
import json
import traceback
import base64
import random
from datetime import datetime, timedelta
from itertools import islice

urllib3.disable_warnings()

'''
目的：
创建指定数量的资产，2万，5万，10万
'''

# 初始化logger
def init_logger():
    global logger
    # 日志路径
    LOG_DIR = './'
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    current_timestamp = int(time.time())
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime(current_timestamp))
    log_file = f"{LOG_DIR}{current_time}_BatchCreate.log"
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=200 * 1024 * 1024, backupCount=4)
    formatter = logging.Formatter("[%(asctime)s %(levelname)s]: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def log(level, msg):
    if level == "info":
        logger.info(msg)
        print(msg)
    elif level == "warn":
        logger.warning(msg)
        # 记录警告的堆栈跟踪
        logger.warning(traceback.format_exc())
    elif level == "error":
        logger.error(msg)
        # 记录错误的堆栈跟踪
        logger.error(traceback.format_exc())
        sys.exit()
    else:
        print(f"Error: An unsupported log level: {level}")
        sys.exit()


# 获取堡垒机token
def get_token(ip, name, passwd):
    url = f"https://{ip}/shterm/api/authenticate"
    data = {"username": name, "password": passwd}
    try:
        response = requests.post(url, data=data, verify=False, timeout=10)  # 设置超时时间为10秒
        response.raise_for_status()
        token = response.json()
        return token.get("ST_AUTH_TOKEN")
    except requests.Timeout:
        log("error", "获取 token 超时，请检查网络连接或稍后重试。")
        return None
    except requests.RequestException as e:
        log("error", f"获取 token 失败: {e}")
        return None

#API认证退出
def token_del(ip, token):
    service_url = "https://" + ip + "/shterm/api/authenticate"
    requests.DEFAULT_RETRIES = 5  # 增加重试连接次数
    s = requests.session()
    s.keep_alive = False  # 关闭多余连接
    http_headers = {"Content-Type": "application/json;charset=UTF-8", "st-auth-token": token}
    r = requests.delete(service_url, headers=http_headers, verify=False)
    return r.status_code

def decode_base64(encoded_str):

    encoded_str = encoded_str.replace('\n', '').replace('\r', '').strip()
    # 计算需要填充的等号数量，Base64 字符串长度必须是4的倍数
    missing_padding = len(encoded_str) % 4
    if missing_padding:
        encoded_str += '=' * (4 - missing_padding)
    
    decoded_bytes = base64.b64decode(encoded_str)
    decoded_str = decoded_bytes.decode('utf-8')
    return decoded_str

# 构造单个资产的 JSON 数据体
def Create_host(index, sys_type_id):
    asset = {
        "name": f"{'Linux' if sys_type_id == 1 else 'Windows'}_device{index:05d}",
        "ip": f"10.{random.randint(1, 254)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "type": 0,
        "sysType": {"id": sys_type_id},
        "department": {"id": 1},
        "charset": "UTF-8"
    }
    return asset

# 构造单个资产的 JSON 数据体
def Create_network(index, sys_type_id):
    asset = {
        "name": f"{'Network'}_device{index:05d}",
        "ip": f"10.{random.randint(1, 254)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "type": 1,
        "sysType": {"id": sys_type_id},
        "department": {"id": 1},
        "charset": "UTF-8"
    }
    return asset


# 构造单个 B/S 资产数据
def Create_BS(index):
    asset = {
        "name": f"BS_device{index:05d}",
        "ip": f"10.{random.randint(1, 254)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "type": 3,
        "sysType": {"id": 13},
        "department": {"id": 1},
        "services": {
            "services": {
                "B/S": {
                    "appclient": [13],
                    "restrictaccess": False,
                    "scriptType": "default",
                    "url": "http://address/shterm/#/resources/app/service/list;page=0"
                }
            }
        }
    }
    return asset

# 构造单个 C/S 资产数据
def Create_CS(index):
    asset = {
        "name": f"CS_device{index:05d}",
        "ip": f"10.{random.randint(1, 254)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "type": 3,
        "sysType": {"id": 13},
        "department": {"id": 1},
        "services": {
            "services": {
                "C/S": {
                    "appclient": [13]
                }
            }
        }
    }
    return asset

# 生成 x万 Linux 和 x万 Windows 的资产数据
# 修改 generate_host_asset_data，增加 start_index 参数
def generate_host_asset_data(linux_count=90000, windows_count=10000, start_index=1):
    assets = []
    for i in range(start_index, start_index + linux_count):
        assets.append(Create_host(i, 1))  # Linux
    for i in range(start_index + linux_count, start_index + linux_count + windows_count):
        assets.append(Create_host(i, 2))  # Windows
    return assets

# 其他函数也加上 start_index，方式相同：
def generate_network_asset_data(count=5000, start_index=1):
    return [Create_network(i, 9) for i in range(start_index, start_index + count)]

def generate_bs_assets(count=5000, start_index=1):
    return [Create_BS(i) for i in range(start_index, start_index + count)]

def generate_cs_assets(count=5000, start_index=1):
    return [Create_CS(i) for i in range(start_index, start_index + count)]



def batch_create_assets(ip, token, assets, batch_size=1000):
    total = len(assets)
    for i in range(0, total, batch_size):
        batch = assets[i:i + batch_size]
        batch_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log("info", f"开始提交第 {i // batch_size + 1} 批（{i + 1} ~ {i + len(batch)}），时间：{batch_start_time}")
        
        create_dev(ip, token, batch)

        batch_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log("info", f"第 {i // batch_size + 1} 批提交完成，时间：{batch_end_time}，累计提交：{i + len(batch)} / {total}")



# 创建资产
def create_dev(ip, token, post_body_list):
    url = "/shterm/api/dev"
    post_url = f"https://{ip}{url}"
    header = {'Content-Type': 'application/json;charset=UTF-8', "st-auth-token": token}
    for item in post_body_list:
        try:
            post_data = json.dumps(item)
            response = requests.post(post_url, data=post_data, headers=header, verify=False)
            if response.status_code == 201:

                log("info", f"dev created successfully: Name: {item.get('name')}, Returned ID: {response.text}" )
            else:
                log("warn", f"dev creation failed: Name: {item.get('name')}, Response: {response.text}")

        except Exception as e:
            log("error", f"Request exception: {e}")


def main():
    try:
        init_logger()
        log("info", "Task started!!!")

        ip = "10.2.173.38"
        username = "admin"
        token = 'shterm123123123123123'

        if token:
            log("info", "开始构建资产数据...")

            all_assets = []

            # 设置起始序号
            start_linux = 1
            start_windows = start_linux + 10000
            start_network = start_windows + 5000
            start_bs = start_network + 5000
            start_cs = start_bs + 5000

            all_assets.extend(generate_host_asset_data(linux_count=10000, windows_count=5000, start_index=start_linux))  # Linux + Windows
            all_assets.extend(generate_network_asset_data(count=5000, start_index=start_network))                         # Network
            all_assets.extend(generate_bs_assets(count=5000, start_index=start_bs))                                       # B/S
            all_assets.extend(generate_cs_assets(count=5000, start_index=start_cs))                                       # C/S

            log("info", f"共生成 {len(all_assets)} 条资产，开始分批提交...")

            batch_create_assets(ip, token, all_assets, batch_size=1000)

            log("info", "全部资产提交完成")
        else:
            log("error", "get token failed")

    except Exception as e:
        log("error", f"Exception: {e}")



if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log("error", f"exception: {e}")
