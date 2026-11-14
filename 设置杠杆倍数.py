import base64
from datetime import datetime, timezone
import hmac
import json
import requests

from 价差自动交易系统 import config

name, api_key, secret_key, passphrase= config.save_to_env()
OKX_rate=config.OKX_rate
url_set_leverage=config.url_set_leverage
# 修改币种的名称
Coin_name="CL"

def main():
    # 1. 每次发请求前实时生成时间戳，防止过期
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    body = {
        "instId": f"{Coin_name}-USDT-SWAP",
        "lever": str(OKX_rate),
        "mgnMode": "cross"
    }

    # 2. 提前将字典转化为严格的 JSON 字符串（消除多余空格）
    body_str = json.dumps(body, separators=(',', ':'))

    # 3. 传入严格的字符串进行签名
    sign = _sign(timestamp, body_str)

    login_payload = {
        "Content-Type": "application/json",
        "OK-ACCESS-KEY": api_key,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-SIGN": sign
    }

    # 4. 【最关键的修复】直接使用 data=body_str 发送，绝对不要再用 json=body
    post = requests.post(url_set_leverage, data=body_str, headers=login_payload)

    result = post.json()
    if result.get("code") == "0":
        print("✅ 杠杆设置成功！")
        print("当前参数:", result.get("data")[0])
    else:
        print("❌ 请求失败:", result)


def _sign(timestamp, body_str):
    """生成 REST API POST 签名"""
    message = timestamp + 'POST' + '/api/v5/account/set-leverage' + body_str
    mac = hmac.new(
        bytes(secret_key, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    d = mac.digest()
    return base64.b64encode(d).decode('utf-8')


if __name__ == "__main__":
    main()