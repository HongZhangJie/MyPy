import os
import requests
import json

url = "https://120.24.4.223:9000/pam/account"

payload = {
    "objectName": "root",
    "resourceName": "192.168.17.131",
    "appId": "APPID1",
    "requestReason": "connect",
    "accessKeyId": os.environ.get("ACCESS_KEY_ID"),
    "accessKeySecret": os.environ.get("ACCESS_KEY_SECRET")
}

headers = {
    "Content-Type": "application/json;charset=utf-8",
    "st-auth-token": "23f90c89-c380-40c9-9442-5a94a3cdf9f1"
}

# 打印调试信息
print("======= PAM API 调试 =======")
print(f"URL: {url}")
print("HEADERS:")
print(json.dumps(headers, indent=2))
print("PAYLOAD:")
print(json.dumps(payload, indent=2))
print("============================")

response = requests.post(url, headers=headers, json=payload, verify=False)

print("======= PAM API 响应 =======")
print(response.text)
