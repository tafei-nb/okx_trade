import json


import websockets
import asyncio

url = 'wss://ws.okx.com:8443/ws/v5/public'


# 把函数名改得更有意义，不要用 __main__
async def get_live_prices():
    while True:
        try:
            async with websockets.connect(url) as ws:
                data = {
                    'op': 'subscribe',
                    'args': [
                        {"channel": "tickers", "instId": "BTC-USDT-SWAP"},
                        {"channel": "tickers", "instId": "ETH-USDT-SWAP"},
                        {"channel": "tickers", "instId": "BZ-USDT-SWAP"},
                        {"channel": "tickers", "instId": "CL-USDT-SWAP"}
                    ]
                }
                await ws.send(json.dumps(data))
                resp = await ws.recv()
                print("🔗 订阅请求发送:", json.loads(resp))

                while True:
                    response = await ws.recv()

                    if response == "pong":
                        print("⬇️ 收到心跳回复: pong")
                        continue

                    data = json.loads(response)

                    if "event" in data and data["event"] == "subscribe":
                        print(f"✅ 订阅成功: {data}")
                    elif "data" in data:
                        data_dict = data["data"][0]
                        # 每次收到价格，将其打包成字典抛出 (yield)
                        yield {data_dict["instId"]: data_dict["last"]}

        except websockets.exceptions.ConnectionClosedError:
            print("❌ 网络链接异常断开")
        except Exception as e:
            print(f"❌ 发生异常: {e}")
        finally:
            await asyncio.sleep(3)

# 这个文件现在只是一个工具模块，不需要在最下面写运行逻辑了
