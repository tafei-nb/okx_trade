import asyncio

Trading_Pair = {'BTC': 'ETH', 'BZ': 'CL', 'CL': 'BZ', 'ETH': 'BTC'}
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
class LocalNeutralGrid:
    def __init__(self, lower_price, upper_price, grid_num, qty_per_grid):
        # 【核心改动 1】计算等比网格的公比 (Ratio)
        # 对应公式: ratio = (上限 / 下限) ^ (1 / 网格数量)
        self.ratio = (upper_price / lower_price) ** (1 / grid_num)

        # 提前生成所有等比网格线，保存在数组中
        self.grid_lines = [lower_price * (self.ratio ** i) for i in range(grid_num + 1)]
        self.qty_per_grid = qty_per_grid
        self.grid_num = grid_num  # 记录总网格数，用于防止索引越界
        self.grid_count = 0

        # 【核心改动 2】弃用具体的 price，改用“数组索引 (Index)”来精确跟踪
        # 这样可以完全杜绝浮点数乘除法带来的累计误差
        self.next_buy_idx = None
        self.next_sell_idx = None

        self.position = 0.0
        self.cash = 0.0
        self.current_price = None

    # 为了方便你直接运行测试，给 OKX 相关的参数加上了默认值 None
    async def update_price(self, new_price, ws=None, inst_id_string=None, USDT=None, price_dir=None):
        # 捕获导入错误，确保在没有“交易”模块时也能本地跑通回测逻辑
        try:
            from 交易 import place_contract_order
        except ImportError:
            async def place_contract_order(*args):
                pass

        self.current_price = new_price

        # 首次启动：根据初始价格，定位身边的第一个买点和卖点索引
        if self.next_buy_idx is None and self.next_sell_idx is None:
            # 找到所有小于当前市价的网格索引
            buy_indices = [i for i, p in enumerate(self.grid_lines) if p < new_price]
            # 找到所有大于当前市价的网格索引
            sell_indices = [i for i, p in enumerate(self.grid_lines) if p > new_price]

            self.next_buy_idx = buy_indices[-1] if buy_indices else None
            self.next_sell_idx = sell_indices[0] if sell_indices else None

            buy_p = round(self.grid_lines[self.next_buy_idx], 4) if self.next_buy_idx is not None else None
            sell_p = round(self.grid_lines[self.next_sell_idx], 4) if self.next_sell_idx is not None else None
            print(
                f"🚀 等比网格启动 | 每格涨跌幅: {(self.ratio - 1) * 100:.2f}% | 首个买点: {buy_p} | 首个卖点: {sell_p}")
            return

        # ---------------- 场景 1：价格下跌，触发买入 ----------------
        while self.next_buy_idx is not None and new_price <= self.grid_lines[self.next_buy_idx]:

            execute_price = self.grid_lines[self.next_buy_idx]
            # 执行买入
            await place_contract_order(ws, inst_id_string, USDT, "buy", price_dir.get(price_dir_change.get(inst_id_string)), price_dir.get(price_dir_change.get(Trading_Pair.get(inst_id_string))))

            self.position += self.qty_per_grid
            self.cash -= self.qty_per_grid * execute_price
            self.grid_count += 0.01

            print(
                f"📉 [下穿 {execute_price:.4f}] 买入 | 仓位: {self.position:+.2f} | 现金流: {self.cash:.2f} | 网格：{self.grid_count:.2f}")



            # 【基于索引的完美跨网格】：买入后，下一个卖点就是当前买点索引 + 1
            self.next_sell_idx = self.next_buy_idx + 1

            # 下一个买点继续往下移一格 (如果触底了就设为 None)
            self.next_buy_idx = self.next_buy_idx - 1 if self.next_buy_idx > 0 else None

        # ---------------- 场景 2：价格上涨，触发卖出 ----------------
        while self.next_sell_idx is not None and new_price >= self.grid_lines[self.next_sell_idx]:

            execute_price = self.grid_lines[self.next_sell_idx]

            # 执行卖出

            await place_contract_order(ws, inst_id_string, USDT, "sell", price_dir.get(price_dir_change.get(inst_id_string)), price_dir.get(price_dir_change.get(Trading_Pair.get(inst_id_string))))

            self.position -= self.qty_per_grid
            self.cash += self.qty_per_grid * execute_price
            self.grid_count -= 0.01

            print(
                f"📈 [上穿 {execute_price:.4f}] 卖出 | 仓位: {self.position:+.2f} | 现金流: {self.cash:.2f} | 网格：{self.grid_count:.2f}")



            # 【基于索引的完美跨网格】：卖出后，下一个买点就是当前卖点索引 - 1
            self.next_buy_idx = self.next_sell_idx - 1

            # 下一个卖点继续往上移一格 (如果到顶了就设为 None)
            self.next_sell_idx = self.next_sell_idx + 1 if self.next_sell_idx < self.grid_num else None

    def get_pnl(self):
        return self.cash + (self.position * self.current_price) if self.current_price else 0.0


# ================= 对比测试 =================
async def main():
    # 假设 CL 的区间 1 到 1.5，50格
    grid = LocalNeutralGrid(lower_price=0.66, upper_price=1.5, grid_num=120, qty_per_grid=0.5)

    prices = [1.25, 1.1, 1, 0.9, 1.3, 1.1, 1.2, 1.1, 1.1, 1.1, 1, 1.1, 1.2, 1.2500001]

    for price in prices:
        print(f"\n>>> 最新市价: {price}")
        await grid.update_price(price)

    print(f"\n💰 最终总盈亏: {grid.get_pnl():.2f}")


if __name__ == "__main__":
    asyncio.run(main())