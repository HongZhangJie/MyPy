import os
import requests

url = "https://120.24.4.223:9000/pam/account"

payload = {
    "objectName": "root",
    "resourceName": "192.168.17.131",
    "appId": "APPID1",
    "requestReason": "connect",
    "accessKeyId": "1a200vAAeQUfM6ZE3DSiKy1FW",
    "accessKeySecret": "aa0ad8CQXMu7Y3xdk3Aj5y1DFf4ydW"
}

headers = {
    "Content-Type": "application/json;charset=utf-8",
    "st-auth-token": "23f90c89-c380-40c9-9442-5a94a3cdf9f1"
}

response = requests.post(url, headers=headers, json=payload, verify=False)

print(response.text)
