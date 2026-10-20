from datetime import datetime


def extract_for_db(raw_data):
    """
    提取存入数据库的 4 个核心变量：
    symbol (币种名称), quantity (数量), price (价格), record_time (时间)
    带有完整的容错处理，防止空数据导致程序崩溃。
    """
    try:
        # 1. 安全获取 data 列表
        data_list = raw_data.get("data", [])
        if not data_list:
            return None, None, None, None

        data_item = data_list[0]

        # 2. 提取并转换时间 (毫秒时间戳 -> MySQL DATETIME 格式)
        p_time_ms = int(data_item.get("pTime", 0))
        if p_time_ms > 0:
            record_time = datetime.fromtimestamp(p_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
        else:
            record_time = None

        # 3. 安全获取 posData (防止列表为空)
        pos_data_list = data_item.get("posData", [])
        if not pos_data_list:
            # 如果这条推送没有持仓变化数据，返回 None 忽略即可
            return None, None, None, None

        pos_data = pos_data_list[0]

        # 4. 提取核心字段
        inst_id = pos_data.get("instId", "")
        # 将 "ETH-USDT-SWAP" 切割为干净的 "ETH"
        symbol = inst_id.split("-")[0] if "-" in inst_id else inst_id

        # 转为浮点数，更适合存入数据库的 DECIMAL/FLOAT 字段
        quantity = float(pos_data.get("pos", 0))
        price = float(pos_data.get("avgPx", 0))

        return symbol, quantity, price, record_time

    except Exception as e:
        print(f"❌ 解析数据出错: {e}")
        return None, None, None, None


# ----------------- 测试运行 -----------------
raw_data2 = {"arg":{"channel":"balance_and_position","uid":"611775072042571853"},"data":[{"balData":[{"cashBal":"0.4425256349525037","ccy":"USDT","uTime":"1778079558654"}],"eventType":"filled","pTime":"1778079558655","posData":[{"avgPx":"2358.99","baseBal":"","ccy":"USDT","instId":"ETH-USDT-SWAP","instType":"SWAP","mgnMode":"isolated","nonSettleAvgPx":"","pos":"0.01","posCcy":"","posId":"3519604495194988550","posSide":"long","quoteBal":"","settledPnl":"","tradeId":"3828724950","uTime":"1778079558654"}],"trades":[{"instId":"ETH-USDT-SWAP","tradeId":"3828724950"}]}]}
raw_data1 = {
    # ... (你的空单平仓数据) ...
    "data": [{"pTime": "1778076838346", "posData": [{"instId": "ETH-USDT-SWAP", "pos": "0", "avgPx": "0"}]}]
}

raw_data = {
    # ... (你的多单平仓数据) ...
    "data": [{"pTime": "1777396609026", "posData": [{"instId": "ETH-USDT-SWAP", "pos": "0", "avgPx": "0"}]}]
}

if __name__ == "__main__":
    # 我们测试一下两组数据
    datasets = [("测试数据1 (空单平仓)", raw_data2), ("测试数据2 (多单平仓)", raw_data)]

    for name, data in datasets:
        symbol, quantity, price, record_time = extract_for_db(data)

        if symbol is not None:
            print(f"--- {name} 提取结果 ---")
            print(f"名称 (symbol)      : {symbol}")
            print(f"数量 (quantity)    : {quantity}")
            print(f"价格 (price)       : {price}")
            print(f"时间 (record_time) : {record_time}")
        else:
            print(f"--- {name} 提取失败或无持仓数据 ---")