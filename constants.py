from 价差自动交易系统 import config

mapping_dict = {                                                    # OKX交易序号
    "BTC": 10459,
    'ETH': 10461,
    'BZ': 254585,
    'CL': 251851
}
Trading_Pair = {                                                    # 映射对
    config.A_Boin_NAME: config.B_Boin_NAME,
    config.B_Boin_NAME: config.A_Boin_NAME}
sz_mix = {                                                          # 币种一张代表的交易量
    'BTC': 0.0001,
    'ETH': 0.001,
    'BZ': 0.01,
    'CL': 0.1
}
Other_Pair = {                                                      # 映射对
    "long": 'short',
    "short": 'long',
    "buy": "sell",
    "sell": 'buy'
}
ORDER_BUY="buy"
ORDER_SELL="sell"
ORDER_SHORT="short"
ORDER_LONG="long"
ORDER_PING="ping"
ORDER_PONG="pong"
ORDER_USDT="USDT"
