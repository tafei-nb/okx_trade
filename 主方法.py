import asyncio
import time

# 导入上面写好的异步生成器
from websocket_获取实时价格 import get_live_prices
from websocket_查看当前持仓与账户 import __login
from 交易 import order_main, balance_Postion_CL

from 价差自动交易系统 import config, constants

status = config.status

# 单次交易最大数量
USDT_count =config.USDT_count
# 声明全局变量
# 当前价格
price_dir = {
    f"{config.B_Boin_NAME}_price": 0,
    f"{config.A_Boin_NAME}_price": 0
}
# 比率
price_rate = {
    f"{config.A_Boin_NAME}_{config.B_Boin_NAME}_rate": -1,
    f"{config.B_Boin_NAME}_{config.A_Boin_NAME}_rate": -1
}
# 当前持仓
Position = {
    config.B_Boin_NAME: 0.0,
    config.A_Boin_NAME: 0.0,
    constants.ORDER_USDT: 0.0
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
            f"💰 {config.B_Boin_NAME}: {price_dir.get(f"{config.B_Boin_NAME}_price")} | {config.A_Boin_NAME}: {price_dir.get(f"{config.A_Boin_NAME}_price")}")
        print(
            f"{config.B_Boin_NAME} 持仓: {Position[config.B_Boin_NAME]*constants.sz_mix[config.B_Boin_NAME]} "
            f"||{config.A_Boin_NAME} 持仓: {Position[config.A_Boin_NAME]*constants.sz_mix[config.A_Boin_NAME]} ")
        print(f"USDT价值{Position[constants.ORDER_USDT]}")
        if  price_dir.get(f"{config.B_Boin_NAME}_price") > 0 and price_dir.get(f"{config.A_Boin_NAME}_price") > 0:
            price_rate[f"{config.A_Boin_NAME}_{config.B_Boin_NAME}_rate"] = (price_dir.get(f"{config.A_Boin_NAME}_price")) / price_dir.get(f"{config.B_Boin_NAME}_price")
            print(f"{config.A_Boin_NAME}_{config.B_Boin_NAME}_rate:{price_rate[f"{config.A_Boin_NAME}_{config.B_Boin_NAME}_rate"]}")


async def process_live_prices():
    """专门负责接收 WebSocket 数据并更新全局变量的异步任务"""
    global price_dir

    print("▶️ 数据处理协程已启动...")

    # ⚠️ 关键：接收异步生成器的数据，必须用 async for
    async for latest_price_dict in get_live_prices():

        # 实时更新全局变量
        if f"{config.B_Boin_NAME}{config.B_Boin_SWAP}" in latest_price_dict:
            price_dir[f"{config.B_Boin_NAME}_price"] = float(latest_price_dict.get(f"{config.B_Boin_NAME}{config.B_Boin_SWAP}"))
        elif f"{config.A_Boin_NAME}{config.A_Boin_SWAP}" in latest_price_dict:
            price_dir[f"{config.A_Boin_NAME}_price"] = float(latest_price_dict.get(f"{config.A_Boin_NAME}{config.A_Boin_SWAP}"))


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
    await balance_Postion_CL(config.A_Boin_NAME, price_dir, Position)


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
            # 调平机器人
            if status:
                task5=asyncio.create_task(balance_Postion())
                await asyncio.gather(task1, task2, task3, task4, task5)
            else:
                await asyncio.gather(task1, task2, task3, task4)

        except:
            time.sleep(3)
            pass



if __name__ == '__main__':
    # 整个程序的唯一入口：启动 asyncio 事件循环
    asyncio.run(main())
