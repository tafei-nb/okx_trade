import asyncio
import base64
import hmac
import json
import time
import uuid


import websockets

import get_api_key

# 假设你通过 REST API 获取并解析了数据
mapping_dict = {
    "BTC": 10459,
    'ETH': 10461,
    'BZ': 254585,
    'CL': 251851
}

name, api_key, secret_key, passphrase = get_api_key.save_to_json()

Trading_Pair = {'BTC': 'ETH', 'BZ': 'CL', 'CL': 'BZ', 'ETH': 'BTC'}
Other_Pair = {
    "long": 'short',
    "short": 'long',
    "buy": "sell",
    "sell": 'buy'
}
sz_mix = {
    'BTC': 0.0001,
    'ETH': 0.001,
    'BZ': 0.01,
    'CL': 0.1

}
price_dir_change = {
    "BTC": "btc_price",
    "ETH": "eth_price",
    "BZ": "BZ_price",
    "CL": "CL_price"
}
price_rate_change = {
    "BTC": "btc_eth_rate",
    "ETH": "eth_btc_rate",
    "BZ": "BZ_CL_rate",
    "CL": "CL_BZ_rate"
}
dir_order = {}

price_rate=10
ws = None


# async def balance_Postion_CL( inst_id_string, price_dir, Postion):
#     #                         CL              CL.price                    BZ.price
#     global ws
#     await asyncio.sleep(5)
#     inst_id_string = Trading_Pair.get(inst_id_string)
#     await order_only_one_buy(ws, inst_id_string, price_dir, Postion)
#     await order_only_one_sell(ws, inst_id_string, price_dir, Postion)
async def balance_Postion_CL(inst_id_string, price_dir, position):
    global ws
    await asyncio.sleep(5)

    # 比如传入 "CL"，这里会映射成需要调平的主体目标 "BZ"
    target_coin = Trading_Pair.get(inst_id_string)
    reverse_coin = inst_id_string

    # 放入一个无限循环，确保平衡任务永远在后台监控
    while True:
        await auto_balance_order(ws, target_coin, reverse_coin, price_dir, position)
        await asyncio.sleep(5)  # 每次检查间隔 5 秒，避免请求过于频繁


async def auto_balance_order(ws, target_coin, reverse_coin, price_dir, position):
    """
    智能动态调平函数 (已修复 USDT 价值计算的面值缺失问题)
    """
    target_code = mapping_dict.get(target_coin)

    # 1. 动态获取当前持仓量 (张数)
    pos_target = position.get(target_coin, 0.0)
    pos_reverse = position.get(reverse_coin, 0.0)

    # 2. 动态获取最新价格
    price_target = price_dir.get(price_dir_change.get(target_coin))
    price_reverse = price_dir.get(price_dir_change.get(reverse_coin))

    if not price_target or not price_reverse:
        return

    # 【核心修复】：推算 OKX 合约面值 (Multiplier)
    # 根据你的 sz_mix 推算，面值正好等于 sz_mix * 100
    # (例如 CL: 10 * 100 = 1000, BZ: 0.01 * 100 = 1)
    target_multiplier = sz_mix.get(target_coin) * 100
    reverse_multiplier = sz_mix.get(reverse_coin) * 100

    # 3. 计算真实的 USDT 价值 = 价格 * 持仓张数 * 合约面值
    target_usdt = price_target * pos_target * target_multiplier
    reverse_usdt = price_reverse * pos_reverse * reverse_multiplier

    # 4. 计算绝对值偏差
    diff = abs(target_usdt) - abs(reverse_usdt)

    # 获取单次下单阈值 (以真实的 USDT 计价)
    # 你设定的单次下单量是 0.01 张，这里将阈值设为 0.01 张价值的 1.5 倍，防止微小波动引起无限发单
    threshold_usdt = price_target * 0.01 * target_multiplier * 1.5

    print(
        f"\n[WS-平衡机器人] {target_coin} 真实价值: {abs(target_usdt):.2f} USDT | {reverse_coin} 真实价值: {abs(reverse_usdt):.2f} USDT")
    print(f"[WS-平衡机器人] 价值差距: {diff:+.2f} USDT | 调平阈值: {threshold_usdt:.2f} USDT")

    if abs(diff) <= threshold_usdt:
        return

    request_id = uuid.uuid4().hex
    side = ""

    # 5. 动态判断开单方向 (这次算对了数值，方向就会绝对精准)
    if diff < 0:
        # 目标币种价值偏小，需要【增加】持仓绝对值
        if pos_target >= 0:
            side = "buy"  # 本身是多头 -> 继续买入做多
        else:
            side = "sell"  # 本身是空头 -> 继续卖出做空
    else:
        # 目标币种价值偏大，需要【减少】持仓绝对值
        if pos_target > 0:
            side = "sell"  # 本身是多头 -> 卖出平多
        else:
            side = "buy"  # 本身是空头 -> 买入平空

    # 6. 发送调平订单
    batch_orders = {
        "id": request_id,
        "op": "batch-orders",
        "args": [{
            "side": side,
            "instIdCode": target_code,
            "tdMode": "cross",
            "ordType": "market",
            "sz": "0.01",  # 张数
            'posSide': 'net',
            # 'px': price_dir.get(price_dir_change.get(target_coin)),
            "clOrdId": request_id
        }]
    }
    await ws.send(json.dumps(batch_orders))
    print(f"[WS-平衡机器人] 已为 {target_coin} 发送 [{side}] 订单以调整仓位平衡")


async def order_main(price_rate, price_dir, USDT_count, Postion):
    # 交易必须连接私有频道 (Private Channel)
    global ws
    ws_url = "wss://ws.okx.com:8443/ws/v5/private"

    # 在最外层包裹一个 While True 无限循环用于重连
    while True:
        try:
            print("\n[WS] 尝试建立连接...")

            # 使用 async with 可以确保连接出现问题时自动执行清理工作
            async with websockets.connect(ws_url, ping_interval=None) as websocket:
                ws = websocket
                is_logged_in = False

                print("[WS] 连接已建立，准备鉴权...")
                timestamp = str(time.time()).split('.')[0]
                sign = _sign(timestamp)

                login_payload = {
                    "op": "login",
                    "args": [{
                        "apiKey": api_key,
                        "passphrase": passphrase,
                        "timestamp": timestamp,
                        "sign": sign
                    }]
                }

                await ws.send(json.dumps(login_payload))

                # 等待鉴权结果
                response = await ws.recv()
                res_data = json.loads(response)

                if res_data.get("event") == "login" and res_data.get("code") == "0":
                    is_logged_in = True
                    print("[WS] 鉴权成功！启动后台监控与策略任务...")

                    # 将任务存入变量，以便在掉线时可以取消它们
                    task_ping = asyncio.create_task(_ping(is_logged_in, ws))
                    task_recv = asyncio.create_task(_recv(is_logged_in, ws))
                    task_strategy = asyncio.create_task(
                        strategy_CL_BZ(ws, price_rate, price_dir, USDT_count, Postion))

                    # 这里的关键操作：让主流程在这里等待 _recv 任务
                    # 只要网络正常，_recv 就会一直在跑。如果断网，_recv 结束，这行 await 就会放行。
                    await task_recv

                    # 如果代码执行到这里，说明 _recv 任务已经结束（掉线了）
                    print("[WS] 接收循环已退出，准备清理旧任务...")

                    # 取消其他相关的子任务，防止重新连接后开启双份任务导致重复开单！
                    task_ping.cancel()
                    task_strategy.cancel()

                else:
                    print(f"[WS] 鉴权失败: {res_data.get('msg')}，等待重试...")

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[WS] 检测到 WebSocket 连接已关闭 (代码: {e.code}, 原因: {e.reason})")
        except Exception as e:
            print(f"[WS] 发生未预期的网络或程序异常: {e}")

        # 无论是因为鉴权失败、被服务器踢出，还是网络报错
        # 统一休息 5 秒后，重新进入下一次 While 循环发起连接
        print("[WS] 等待 5 秒后发起重连...\n")
        await asyncio.sleep(5)





async def strategy_CL_BZ(ws, price_rate, price_dir, USDT_count, Postion):
    print("strategy_CL_BZ")
    from 交易策略 import LocalNeutralGrid
    grid_front = LocalNeutralGrid(lower_price=0.8, upper_price=1.25, grid_num=40, qty_per_grid=0.5)  # 等比
    grid_reverse = LocalNeutralGrid(lower_price=1, upper_price=2, grid_num=100, qty_per_grid=0.5)
    while True:
        await asyncio.sleep(1)
        grid = None
        price = None
        name = None

        # if price_rate.get("CL_BZ_rate") >= 1:
        #     grid = grid_front
        #     name = "CL"
        # elif price_rate.get("CL_BZ_rate") < 1:
        #     grid = grid_reverse
        #     name = "BZ"
        # else:
        #     continue

        grid = grid_front
        name = "CL"

        frist_for = True
        while True:
            await asyncio.sleep(1)

            price = price_rate.get(price_rate_change.get(name))

            if frist_for:
                frist_for = False
                price = 0.95
            print(f"\n>>> 最新市价: {price}")

            await grid.update_price(price, ws, name, USDT_count, price_dir)

            # if price < 1:
            #     break

        print(f"\n💰 最终总盈亏: {grid.get_pnl():.2f}")



pending_responses = {}


async def place_contract_order(ws, inst_id_string, USDT, side, price_dir_real_front, price_dir_real_reverse):
    global pending_responses
    try:
        request_id = uuid.uuid4().hex

        if inst_id_string not in ['BTC', 'BZ', 'CL', 'ETH']:
            return

        if price_dir_real_front is None or price_dir_real_reverse is None:
            return

        # 计算双边张数
        mix_USDT_front = price_dir_real_front * sz_mix[inst_id_string] / price_rate
        mix_USDT_reverse = price_dir_real_reverse * sz_mix[Trading_Pair.get(inst_id_string)] / price_rate

        # 恢复保留两位小数的计算方式
        sz_front = round(((USDT / 2) / (mix_USDT_front * 100)), 2)
        sz_reverse = round(((USDT / 2) / (mix_USDT_reverse * 100)), 2)

        print(f"计算张数成功 -> 前向: {sz_front}, 反向: {sz_reverse}")

        # 拦截过小的异常单，防止 sz = 0 被拒
        if sz_front < 0.01 or sz_reverse < 0.01:
            print(f"❌ 资金不足以买入 0.01 张，前向:{sz_front}, 反向:{sz_reverse}，放弃下单")
            return

        target_instId1 = mapping_dict.get(inst_id_string)
        target_instId2 = mapping_dict.get(Trading_Pair[inst_id_string])

        # ⚠️ 【绝不能有下划线】：直接拼接纯字母和数字，控制长度在 32 位内
        clordid1 = f"{inst_id_string}{uuid.uuid4().hex[:8]}"
        clordid2 = f"{Trading_Pair.get(inst_id_string)}{uuid.uuid4().hex[:8]}"

        batch_orders = {
            "id": request_id,
            "op": "batch-orders",
            "args": [
                {"side": side, "instIdCode": target_instId1, "tdMode": "cross", "ordType": "market",
                 "sz": str(sz_front), 'posSide': 'net', "clOrdId": clordid1},
                {"side": Other_Pair[side], "instIdCode": target_instId2, "tdMode": "cross", "ordType": "market",
                 "sz": str(sz_reverse), 'posSide': 'net',  "clOrdId": clordid2}
            ]
        }

        await ws.send(json.dumps(batch_orders))
    except Exception as e:
        import traceback
        traceback.print_exc()

"""下面是上一版_recv"""



async def _recv(is_logged_in, ws):
    global pending_responses
    while is_logged_in:
        try:
            message = await ws.recv()
            if message == "pong":
                continue

            data = json.loads(message)
            msg_id = data.get("id")

            # ⚠️ 核心逻辑：如果这个消息的 ID 是我们在 place_contract_order 里登记过的
            if msg_id in pending_responses:
                # 激活那个正在挂起等待的 future，把数据直接传给它！
                if not pending_responses[msg_id].done():
                    pending_responses[msg_id].set_result(data)
                continue

            print(f"\n[收到常规服务器消息] {json.dumps(data, indent=2, ensure_ascii=False)}")

        except websockets.ConnectionClosed:
            break
        except Exception as e:
            print(f"[WS] 接收消息异常: {e}")


async def _ping(is_logged_in, ws):
    """异步心跳任务：每 20 秒发送一次 ping 以保持连接"""
    while is_logged_in:
        try:
            print("ping")
            await ws.send("ping")
            await asyncio.sleep(20)
        except websockets.ConnectionClosed:
            print("[WS] 连接已关闭，停止心跳。")
            break


def _sign(timestamp):
    """生成 WebSocket 签名"""
    message = timestamp + 'GET' + '/users/self/verify'
    mac = hmac.new(
        bytes(secret_key, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    d = mac.digest()
    return base64.b64encode(d).decode('utf-8')


def get_rate(filename="AAA交易倍率.json"):
    """
    将数据保存为 JSON 文件，格式化输出方便手工修改。
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            # indent=4 让代码缩进整齐
            # ensure_ascii=False 确保中文不乱码，方便你手工阅读和编辑
            json_load = json.load(f)
        rate = json_load.get('rate')
        return rate

    except Exception as e:
        print(f"❌ 保存失败: {e}")


# 形参依次为
# 服务器连接 币种名称 购买用的usdt 买卖 多空方向
# 下单，策略判断后自动下单


if __name__ == "__main__":
    asyncio.run(order_main())
