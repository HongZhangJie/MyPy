import sys
import requests
import json

url = "https://120.24.4.223:9000/pam/account"

access_key_id = sys.argv[1]
access_key_secret = sys.argv[2]

payload = {
    "objectName": "root",
    "resourceName": "192.168.17.131",
    "appId": "APPID1",
    "requestReason": "connect",
    "accessKeyId": access_key_id,
    "accessKeySecret": access_key_secret
}

headers = {
    "Content-Type": "application/json;charset=utf-8",
    "st-auth-token": "23f90c89-c380-40c9-9442-5a94a3cdf9f1"
}

print("======= PAM API 调试 =======")
print(f"URL: {url}")
print(f"HEADERS: {json.dumps(headers, indent=2)}")
print(f"PAYLOAD: {json.dumps(payload, indent=2)}")
print("============================")

response = requests.post(url, headers=headers, json=payload, verify=False)

print("======= PAM API 响应 =======")
print(response.text)
