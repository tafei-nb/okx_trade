import json
import os
from dotenv import load_dotenv

OKX_rate= 10                                                        # 杠杆倍数
url_set_leverage = 'https://www.okx.com/api/v5/account/set-leverage'# 设置杠杆的网址
url_ws_private = "wss://ws.okx.com/ws/v5/private"                  # ws连接账户网址
url_ws_public = 'wss://ws.okx.com/ws/v5/public'                      # ws公共数据网址
status=False                                                        # 下单状态 true用主方法count数量交易 false用Boin_count数量交易（关闭调平机器人）
Boin_count=0.1                                                      # 交易数量status为false时生效
def save_to_env(filename=".env"):
    try:
        load_dotenv(filename)
        name = os.getenv("OKX_API_NAME")                                    # api名字
        api_key = os.getenv("OKX_API_KEY")                                  # api
        secret_key = os.getenv("OKX_SECRET_KEY")                            # 密钥
        passphrase = os.getenv("OKX_PASSPHRASE")                            # 密码


        return name, api_key, secret_key, passphrase
    except Exception as e:
        print(f"保存失败,错误{e}")
