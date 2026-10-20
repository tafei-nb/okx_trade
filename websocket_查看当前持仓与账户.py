import base64
import hashlib
import hmac
import json
import time
from 持仓初始化 import get_asset_quantities
import asyncio
import websockets
import get_api_key

from 存储数据 import insert_crypto_record




def sign_(secret_key, message):
    h = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    base64_bytes = base64.b64encode(h.digest())
    result = base64_bytes.decode()
    return result

async def __login(Position=None,price_dir=None):
    name,apikey,secret_key,passphrase = get_api_key.save_to_json()
    while True:
        try:
            async with websockets.connect("wss://ws.okx.com:8443/ws/v5/private") as ws:
                timestamp = str(int(time.time()))
                message = {
                    "op": "login",
                    "args":
                        [
                            {
                                "apiKey": apikey,
                                "passphrase": passphrase,
                                "timestamp": timestamp,
                                "sign": sign_(secret_key, timestamp + "GET" + '/users/self/verify')
                            }
                        ]
                }

                await ws.send(json.dumps(message))
                recv_ = await ws.recv()
                print(recv_)
                # 登录成功
                message = {
                    "id": '123321',
                    "op": "subscribe",
                    "args": [{
                        "channel": "balance_and_position"
                    }]
                }
                await ws.send(json.dumps(message))
                count = 0
                while True:

                    count += 1
                    recv_ = await ws.recv()
                    print(recv_)
                    if count > 3:
                        recv_ = json.loads(recv_)
                        data_list = recv_.get("data", [])

                        if not data_list:
                            continue

                        data_content = data_list[0]

                        # 1. 检查是否是持仓/成交推送
                        if "posData" in data_content and len(data_content["posData"]) > 0:
                            pos_data = data_content["posData"][0]

                            # 提取合约名称，例如 "ETH-USDT-SWAP"
                            inst_id = pos_data.get("instId", "")

                            # 通过 "-" 切分字符串，拿到前面的 "ETH"
                            # split("-")[0] 会把 "ETH-USDT-SWAP" 变成 "ETH"
                            data_item = inst_id.split("-")[0] if "-" in inst_id else ""

                            # 提取最新持仓量（可选：如果你不想再调一次 API，可以直接从这里拿）
                            new_pos = pos_data.get("pos", "0")

                            if data_item == 'ETH':
                                Position_temp = insert_crypto_record(recv_, price_dir, Position)
                                if Position_temp is not None:
                                    Position['ETH'] = Position_temp
                            elif data_item == 'BTC':
                                Position_temp = insert_crypto_record(recv_, price_dir, Position)
                                if Position_temp is not None:
                                    Position['BTC'] = Position_temp
                            elif data_item == 'DOGE':
                                Position_temp = insert_crypto_record(recv_, price_dir, Position)
                                if Position_temp is not None:
                                    Position['DOGE'] = Position_temp
                            elif data_item == 'SOL':
                                Position_temp = insert_crypto_record(recv_, price_dir, Position)
                                if Position_temp is not None:
                                    Position['SOL'] = Position_temp
                            elif data_item == 'USDT':
                                Position_temp = insert_crypto_record(recv_, 1, Position)
                                if Position_temp is not None:
                                    Position['USDT'] = Position_temp

                            # ... 其他币种以此类推 ...

                        # 2. 如果你需要同步更新 USDT 余额
                        if "balData" in data_content and len(data_content["balData"]) > 0:
                            bal_data = data_content["balData"][0]
                            if bal_data.get("ccy") == "USDT":
                                # 你甚至可以直接在这里更新余额，不需要调用 insert_crypto_record
                                Position['USDT'] = float(bal_data.get("cashBal", 0))

                        yield Position


                    elif count == 3:
                        Position = get_asset_quantities(recv_)
                        print(f"💰 USDT 余额: {Position['USDT']}")
                        print(f"📈 BTC 持仓: {Position['BTC']} 张")
                        print(f"📈 ETH 持仓: {Position['ETH']} 张")
                        print(f"📈 SOL 持仓: {Position['SOL']} 张")
                        print(f"📉 DOGE 持仓: {Position['DOGE']} 张")
                        yield Position

            """
                    {
            "id": "1512",
            "op": "subscribe",
            "args": [{
                "channel": "balance_and_position"
            }]
        }
        """



        except websockets.exceptions.ConnectionClosedError:
            print("网络链接异常断开")
        except websockets.exceptions.ConnectionClosedOK:
            print("已关闭网络连接")


async def main():
    Position = {
        "BTC": 0.0,
        "ETH": 0.0,
        "SOL": 0.0,
        "DOGE": 0.0,
        "USDT": 0.0
    }

    # 使用 async for 消费异步生成器产出的数据
    async for current_position in __login(Position=Position):
        # 每次 yield 这里就会触发，你可以在这里处理最新的持仓信息
        pass
        # print("🔄 持仓已更新:", current_position)


if __name__ == '__main__':
    # 运行主协程
    asyncio.run(main())








"""
{
	"arg": {
		"channel": "balance_and_position",
		"uid": "611775072042571853"
	},
	"data": [{
		"balData": [{
			"cashBal": "0.0000000000000001",
			"ccy": "ADA",
			"uTime": "1741177296343"
		}, {
			"cashBal": "1.4645470729525037",
			"ccy": "USDT",
			"uTime": "1777398714197"
		}],
		"eventType": "snapshot",
		"pTime": "1777398777271",
		"posData": [],
		"trades": []
	}]
}

"""


"""

data_item = recv_.get("data", [{}])[0].get("ccy")
{
	"arg": {
		"channel": "balance_and_position",
		"uid": "611775072042571853"
	},
	"data": [{
		"balData": [{
			"cashBal": "1.4634982328603103",
			"ccy": "USDT",
			"uTime": "1777396609026"
		}],
		"eventType": "filled",      成交
		"pTime": "1777396609026",   时间戳
		"posData": [{
			"avgPx": "0",           开仓均价
			"baseBal": "",
			"ccy": "USDT",
			"instId": "ETH-USDT-SWAP",
			"instType": "SWAP",
			"mgnMode": "isolated",  逐仓
			"nonSettleAvgPx": "",
			"pos": "0",             完全平仓
			"posCcy": "",           
			"posId": "3519604495194988550",
			"posSide": "long",      多头
			"quoteBal": "",
			"settledPnl": "",
			"tradeId": "3803318883",
			"uTime": "1777396609026"
		}],
		"trades": [{
			"instId": "ETH-USDT-SWAP",
			"tradeId": "3803318883"
		}]
	}]
}
"""
