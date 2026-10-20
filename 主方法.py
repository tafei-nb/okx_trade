import asyncio

# 导入上面写好的异步生成器
from websocket_获取实时价格 import get_live_prices
from websocket_查看当前持仓与账户 import __login
from 交易 import order_main, balance_Postion_doge

# 单次交易最大数量
USDT_count = 0.6
# 声明全局变量
price_dir = {
    "btc_price": 0,
    "eth_price": 0,
    "sol_price": 0,
    "doge_price": 0,
    "ltc_price":0
}
price_rate = {
    "btc_eth_rate": -1,
    "eth_btc_rate": -1,
    "doge_sol_rate": -1,
    "sol_doge_rate": -1,
    "ltc-btc-rate": -1,
    "btc-ltc-rate": -1
}

Position = {
    "BTC": 0.0,
    "ETH": 0.0,
    "SOL": 0.0,
    "DOGE": 0.0,
    "LTC": 0.0,
    "USDT": 0.0
}


async def print_price():
    """专门负责打印的异步任务"""
    """并计算出特定比率"""
    global price_dir
    global Position
    global price_rate
    while True:
        # ⚠️ 关键：在异步中必须用 asyncio.sleep，不能用 time.sleep
        await asyncio.sleep(1)
        print(
            f"💰 BTC: {price_dir.get("btc_price")} | ETH: {price_dir.get("eth_price")} | SOL: {price_dir.get("sol_price")} | DOGE: {price_dir.get("doge_price")}")
        print(
            f"BTC 持仓: {Position['BTC']} 张|ETH 持仓: {Position['ETH']} 张|SOL 持仓: {Position['SOL']} 张|DOGE 持仓: {Position['DOGE']} 张")
        if price_dir.get("btc_price") > 0 and price_dir.get("eth_price") > 0 and price_dir.get(
                "sol_price") > 0 and price_dir.get("doge_price") > 0:
            price_rate["btc_eth_rate"] = (price_dir.get("btc_price") / 32.629) / price_dir.get("eth_price")
            price_rate["doge_sol_rate"] = (price_dir.get("doge_price") * 900.94) / price_dir.get("sol_price")
            # price_rate["eth_btc_rate"] = price_dir.get("eth_price") / (price_dir.get("btc_price") / 32.629)
            price_rate["sol_doge_rate"] = price_dir.get("sol_price") / (price_dir.get("doge_price") * 900.94)
            # price_rate["ltc-btc-rate"]=price_dir.get("ltc_price") / (price_dir.get("btc_price"))
            print(f"btc_eth_rate:{price_rate["btc_eth_rate"]}||doge_sol_rate:{price_rate["doge_sol_rate"]}")


async def process_live_prices():
    """专门负责接收 WebSocket 数据并更新全局变量的异步任务"""
    global price_dir

    print("▶️ 数据处理协程已启动...")

    # ⚠️ 关键：接收异步生成器的数据，必须用 async for
    async for latest_price_dict in get_live_prices():

        # 实时更新全局变量
        if "BTC-USDT-SWAP" in latest_price_dict:
            price_dir["btc_price"] = float(latest_price_dict.get("BTC-USDT-SWAP"))
        elif "ETH-USDT-SWAP" in latest_price_dict:
            price_dir["eth_price"] = float(latest_price_dict.get("ETH-USDT-SWAP"))
        elif "SOL-USDT-SWAP" in latest_price_dict:
            price_dir["sol_price"] = float(latest_price_dict.get("SOL-USDT-SWAP"))
        elif "DOGE-USDT-SWAP" in latest_price_dict:
            price_dir["doge_price"] = float(latest_price_dict.get("DOGE-USDT-SWAP"))

# 获取持仓
async def get_new_position():
    global Position, price_dir

    async for new_positon in __login(Position, price_dir):
        Position = new_positon

# 交易
async def order_():
    global price_rate, price_dir, USDT_count, Position
    await asyncio.sleep(5)
    while True:
        await order_main(price_rate, price_dir, USDT_count, Position)


async def balance_Postion():
    await asyncio.sleep(150)
    global Position, price_dir
    await balance_Postion_doge("DOGE", price_dir, Position)


async def main():
    """主函数，负责把所有任务并发跑起来"""
    # 创建两个并发任务，相当于开了两个"线程"（协程）
    while True:
        try:
            task1 = asyncio.create_task(print_price())  # 打印价格
            task2 = asyncio.create_task(process_live_prices())  # 实时获取价格
            task3 = asyncio.create_task(get_new_position())  # 实时获取持仓数据

            # 等待任务执行（因为它们是死循环，所以会一直挂起运行）
            task4 = asyncio.create_task(order_())  # 执行交易系统 包含交易策略
            task5 = asyncio.create_task(balance_Postion())

            await asyncio.gather(task1, task2, task3, task4, task5)
        except:
            pass


if __name__ == '__main__':
    # 整个程序的唯一入口：启动 asyncio 事件循环
    asyncio.run(main())
