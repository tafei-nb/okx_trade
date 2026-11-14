import json
from 价差自动交易系统 import config, constants


# 修复了标点符号和格式的 JSON 原文数据



def get_asset_quantities(json_str):
    # 1. 初始化结果，如果没有找到默认就是 0
    result = {
        config.B_Boin_NAME: 0.0,
        config.A_Boin_NAME: 0.0,
        constants.ORDER_USDT: 0.0
    }
    try:
        # 将 JSON 字符串转为 Python 字典
        data_dict = json.loads(json_str)

        # 安全获取 data 列表中的第一个元素
        data_list = data_dict.get("data", [])
        if not data_list:
            return result

        core_data = data_list[0]

        # 2. 从 balData 提取 USDT 余额
        for bal in core_data.get("balData", []):
            if bal.get("ccy") == constants.ORDER_USDT:
                result[constants.ORDER_USDT] += float(bal.get("cashBal", 0))

        # 3. 从 posData 提取各个币种的持仓量
        for pos in core_data.get("posData", []):
            inst_id = pos.get("instId", "")
            pos_qty = float(pos.get("pos", 0))
            pos_side = pos.get("posSide", "")  # 🌟 关键点 1：获取多空方向

            # 🌟 关键点 2：如果是做空 (short)，就把张数变成负数
            if pos_side == constants.ORDER_SHORT:
                pos_qty = -pos_qty

            # 匹配并累加持仓张数
            if f"{config.B_Boin_NAME}{config.B_Boin_SWAP}" in inst_id:
                result[config.B_Boin_NAME] += pos_qty
            elif f"{config.A_Boin_NAME}{config.A_Boin_SWAP}" in inst_id:
                result[config.A_Boin_NAME] += pos_qty

        return result

    except Exception as e:
        print(f"解析 JSON 出错: {e}")
        return result


raw_data = """
{"arg":{"channel":"balance_and_position","uid":"611775072042571853"},"data":[{"balData":[{"cashBal":"0.5134869079525037","ccy":"USDT","uTime":"1777472199534"}],"eventType":"snapshot","pTime":"1777993061020","posData":[{"avgPx":"83.76","baseBal":"","ccy":"USDT","instId":"BZ-USDT-SWAP","instType":"SWAP","mgnMode":"iBZated","nonSettleAvgPx":"","pos":"0.01","posCcy":"","posId":"3522201831268098048","posSide":"long","quoteBal":"","settledPnl":"","tradeId":"1489961604","uTime":"1777968001639"},{"avgPx":"0.10574","baseBal":"","ccy":"USDT","instId":"CL-USDT-SWAP","instType":"SWAP","mgnMode":"iBZated","nonSettleAvgPx":"","pos":"0.01","posCcy":"","posId":"3522202000550207488","posSide":"short","quoteBal":"","settledPnl":"","tradeId":"1251695406","uTime":"1777968000637"}],"trades":[]}]}
"""
# 测试运行
if __name__ == "__main__":
    quantities = get_asset_quantities(raw_data)

    print(f"💰 USDT 余额: {quantities['USDT']}")
    print(f"📈 BZ 持仓: {quantities[config.B_Boin_NAME]} 张")
    print(f"📉 CL 持仓: {quantities[config.A_Boin_NAME]} 张")  # CL 应该是负数