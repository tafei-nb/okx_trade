import os
from dotenv import load_dotenv
from sympy import false

OKX_rate= 10                                                        # 杠杆倍数
url_set_leverage = 'https://www.okx.com/api/v5/account/set-leverage'# 设置杠杆的网址
url_ws_private = "wss://ws.okx.com/ws/v5/private"                  # ws连接账户网址
url_ws_public = 'wss://ws.okx.com/ws/v5/public'                      # ws公共数据网址
status=False                                                        # 下单状态 true用主方法USDT_count数量交易 false用Boin_count数量交易（关闭调平机器人）
Boin_count=0.1                                                      # 交易数量status为false时生效
USDT_count = 3                                                      # 单次交易最大数量
A_Boin_NAME="CL"                                                         # 一币种
B_Boin_NAME="BZ"                                                         # 二币种
A_Boin_SWAP="-USDT-SWAP"                                                 # 一币种 合约或币交易（合约以-SWAP结尾 币没有SWAP）
B_Boin_SWAP="-USDT-SWAP"                                                 # 二币种 合约或币交易（合约以-SWAP结尾 币没有SWAP）
Low_Rate_price=0.85                                                  # 网格比值区间最低值
High_Rate_price=1.05                                                # 网格比值区间最高值
Grid_Num=40                                                         # 网格格数
Set_Frist_Rate=False                                                # 是否设置初始价格
Frist_Rate=0.95                                                     # 初始价格（Set_Frist_Rate=True时生效）

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
