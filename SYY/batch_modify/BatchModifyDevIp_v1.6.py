#!/bin/python3
# update time : 20250526
# Description: Customized version v1.5（交互式输入 + CSV 路径参数）

import requests
import urllib3
import time
import sys
import logging
import logging.handlers
import getpass
import concurrent.futures
import argparse
import os
import re
import base64
import traceback
urllib3.disable_warnings()


'''
使用须知：
1、批量修改资产ip，需要提供文件为“dev_NewIPinfo.csv”，需要和脚本同目录，格式为：devName,devIp
2、输出运行日志，在脚本同目录
3、20240731支持修改BS资产url中的ip。url是域名则不修改
已测试版本：XCA 5.1.6
'''

# 初始化 logger
def init_logger():
    global logger
    LOG_DIR = './'
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    current_timestamp = int(time.time())
    current_time = time.strftime("%Y%m%d%H%M%S", time.localtime(current_timestamp))
    log_file = f"{LOG_DIR}{current_time}_BatchModify.log"
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
        print(msg)
    elif level == "error":
        logger.error(msg)
        print(msg)
        sys.exit()
    else:
        print(f"Error: An unsupported log level: {level}")
        sys.exit()

# 获取堡垒机 token
def get_token(ip, name, passwd):
    url = f"https://{ip}/shterm/api/authenticate"
    data = {"username": name, "password": passwd}
    try:
        response = requests.post(url, data=data, verify=False, timeout=10)
        response.raise_for_status()
        token = response.json()
        return token.get("ST_AUTH_TOKEN")
    except requests.Timeout:
        log("error", "获取 token 超时，请检查网络连接或稍后重试。")
        return None
    except requests.RequestException as e:
        log("error", f"获取 token 失败: {e}")
        return None

def decode_base64(encoded_str):
    encoded_str = encoded_str.replace('\n', '').replace('\r', '').strip()
    missing_padding = len(encoded_str) % 4
    if missing_padding:
        encoded_str += '=' * (4 - missing_padding)
    return base64.b64decode(encoded_str).decode('utf-8')

# 获取资产信息
def get_dev(ip, token, dev_name):
    url = f"https://{ip}/shterm/api/dev?deleted=false&name={dev_name}"
    headers = {'Content-Type': 'application/json;charset=UTF-8', "st-auth-token": token}
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        return response.json().get("content")
    except requests.Timeout:
        log("error", "获取资产信息超时，请检查网络连接或稍后重试。")
    except requests.RequestException as e:
        log("error", f"获取资产信息失败: {e}")
    return None

# 获取资产扩展属性

# 修改资产信息
def update_dev_ip(ip, token, dev_id, dev_info):
    url = f"https://{ip}/shterm/api/dev/{dev_id}"
    headers = {'Content-Type': 'application/json;charset=UTF-8', "st-auth-token": token}
    try:
        requests.put(url, headers=headers, verify=False, json=dev_info, timeout=10).raise_for_status()
    except requests.Timeout:
        log("error", "更新资产信息超时，请检查网络连接或稍后重试。")
    except requests.RequestException as e:
        log("warn", f"更新失败，错误码：{e.response.status_code} 错误信息：{e}")

def replace_ip_in_url(original_url, new_ip):
    return re.sub(r"(http[s]?://)([\d\.]+)(:\d+)?",
                  lambda m: f"{m.group(1)}{new_ip}{m.group(3) if m.group(3) else ''}",
                  original_url)

def is_ip_address(url):
    return re.match(r"http[s]?://([a-zA-Z0-9.-]+|\d{1,3}\.){1,3}\d{1,3}(:\d+)?(/.*)?", url) is not None

def is_ip(ip):
    return re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip) is not None

def process_line(ip, token, line, url=False, dev_evt_info=None, attribute_name=None):
    device_new_info = line.strip().split(',')
    if len(device_new_info) < 2:
        log("warn", f"行格式错误: {line.strip()}")
        return
    device_name, new_ip = device_new_info[0].strip(), device_new_info[1].strip()
    if not device_name or not new_ip or device_name == 'devName':
        return

    device_list = get_dev(ip, token, device_name)
    if not device_list:
        log("warn", f"资产 {device_name} 不存在")
        return

    device_info = device_list[0]
    device_id = device_info.get("id")
    device_old_ip = device_info.get("ip")
    owner_id = device_info.get("owner", {}).get("id")
    services_info = device_info.get('services', {})
    extinfo = device_info.get('extInfo', {}) if dev_evt_info else {}
    extra = device_info.get('extra', {}) if dev_evt_info else {}

    final_ip = new_ip if is_ip(device_old_ip) else device_old_ip
    if final_ip == device_old_ip and not is_ip(device_old_ip):
        log("info", f"资产{device_name}的ip为'{device_old_ip}'，非正常ip，不进行修改")
        return

    postdata = {'ip': str(final_ip)}
    if owner_id is not None:
        postdata['owner'] = {'id': owner_id}

    # URL 更新
    if url:
        b_s_service = services_info.get('services', {}).get('B/S', {})
        url_to_update = b_s_service.get('url', '')
        if url_to_update:
            if is_ip_address(url_to_update):
                updated_url = replace_ip_in_url(url_to_update, new_ip)
                b_s_service['url'] = updated_url
                postdata['services'] = {'services': {'B/S': b_s_service}}
                log("info", f"URL 即将更新成功，新 URL: {updated_url}")
            else:
                log("info", f"资产名|新ip|旧ip：{device_name}|{new_ip}|{device_old_ip} | URL: {url_to_update} | 说明: 该 URL 使用的是域名")

    # 备份IP扩展属性
    if dev_evt_info is not None:
        if attribute_name is None:
            attribute_name = {"备份IP地址"}
        attribute_id = None
        for attr_value in dev_evt_info:
            if isinstance(attr_value, dict) and attr_value.get("name") in attribute_name:
                attribute_id = str(attr_value.get('id'))
                break
        if attribute_id and attribute_id in extinfo:
            extinfo[attribute_id] = device_old_ip
            extra.setdefault("extInfo", {})[attribute_id] = device_old_ip
            extra.pop("devUpdateTime", None)
            extra.pop("source", None)
            postdata.update({'extinfo': extinfo, 'extra': extra})
        else:
            log("warn", f"未找到扩展属性 '{attribute_name}' 或属性ID不在 extInfo 中，资产名：{device_name}")

    log("info", f"资产{device_name},更新的数据为：{postdata}")
    update_dev_ip(ip, token, device_id, postdata)
    log("info", f"更新成功，资产名|新ip|旧ip：{device_name}|{final_ip}|{device_old_ip}")

def modify_ip(ip, token, url=False, dev_ext_oldipName=None, csv_path='dev_NewIPinfo.csv'):
    try:
        log("info", f"当前工作目录: {os.getcwd()}")
        with open(csv_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()[1:]  # 跳过表头
        for line in lines:
            process_line(ip, token, line, url, dev_ext_oldipName)
    except FileNotFoundError:
        log("error", f"文件未找到：{os.path.abspath(csv_path)}")
    except Exception as e:
        log("error", f"发生错误: {e}")

def main():
    try:
        init_logger()
        log("info", "Task started!!!")

        parser = argparse.ArgumentParser(description="Batch Modify Tool")
        parser.add_argument("-url", action="store_true", help="更新 B/S URL 中的 IP")
        parser.add_argument("-f", "--file", default="dev_NewIPinfo.csv", help="CSV 文件路径，默认当前目录")
        args = parser.parse_args()
        args.url = True

        # === 交互式输入堡垒机信息 ===
        ip = input("请输入堡垒机地址：").strip()
        username = input("请输入用户名：").strip()
        password = getpass.getpass("请输入密码：").strip()
        url_update = args.url
        csv_path = os.path.abspath(args.file)

        token = get_token(ip, username, password)

        dev_ext_names = {"业务分类", "备份IP地址", "业务系统"}
        dev_ext_aboutip = "备份IP地址"

        if token:
            modify_ip(ip, token, url_update,
                      dev_ext_oldipName=dev_ext_aboutip, csv_path=csv_path)
            log("info", "Task finished!!!")
        else:
            log("error", "获取 token 失败，任务终止")
    except Exception as e:
        log("error", f"exception: {e}")
        log("error", traceback.format_exc())

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log("error", f"exception: {e}")
        log("error", traceback.format_exc())


