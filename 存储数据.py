import pymysql
from datetime import datetime
from 从持仓账户返回值获取有用数据 import extract_for_db


# 1. 数据库连接配置 (请替换为你自己的信息)
DB_CONFIG = {
    'host': '127.0.0.1',  # 数据库地址，本地通常是 127.0.0.1 或 localhost
    'port': 3306,  # 默认端口
    'user': 'root',  # 数据库用户名
    'password': '123456',  # 数据库密码
    'database': 'quant_data',  # 你创建表所在的数据库名
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def insert_crypto_record(raw_data,price_dir,Position):
    # 2. 建立数据库连接
    connection = pymysql.connect(**DB_CONFIG)
    quantity=None
    try:
        with connection.cursor() as cursor:
            # 3. 准备你要存入的数据
            symbol, quantity, price, record_time = extract_for_db(raw_data)
            # 支持小数
            # 获取当前时间，并精确到分钟（去掉秒，方便按分钟统计）
            price_real=None
            quantity_change=None
            if symbol=='BTC':
                price_real = price_dir.get('btc_price')
                quantity_change=quantity-Position.get('BTC')
            elif symbol=='ETH':
                price_real= price_dir.get('eth_price')
                quantity_change=quantity-Position.get('ETH')
            elif symbol=='BZ':
                price_real=price_dir.get('BZ_price')
                quantity_change=quantity-Position.get('BZ')
            elif symbol=='CL':
                price_real=price_dir.get('CL_price')
                quantity_change=quantity-Position.get('CL')


            record_time = datetime.now().strftime('%Y-%m-%d %H:%M:00')

            # 4. 编写 SQL 语句 (核心重点 ⬇️)
            # 使用 ON DUPLICATE KEY UPDATE：
            # 如果同一分钟内还没有 BTC 的数据，就正常插入；
            # 如果同一分钟内已经有 BTC 的数据了，就更新数量和价格，坚决不报错！
            sql = """
                INSERT INTO item_records (symbol, quantity,quantity_change, price, record_time)
                VALUES (%s, %s,%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    quantity = VALUES(quantity),
                    price = VALUES(price)
            """

            # 5. 执行 SQL 语句（千万不要用字符串拼接 SQL，%s 能防止 SQL 注入）
            symbol=symbol+'-USDT-SWAP'
            cursor.execute(sql, (symbol, quantity,quantity_change, price_real, record_time))

        # 6. 提交事务（不执行 commit 的话，数据只在内存里，不会真正存入表）
        connection.commit()
        print(f"✅ 成功存入数据: {symbol} | 价格: {price_real} | 时间: {record_time}")

    except Exception as e:
        print(f"❌ 存入数据失败，错误信息: {e}")
        # 发生错误时回滚
        connection.rollback()

    finally:
        # 7. 无论成功失败，最后一定要关闭连接释放资源
        connection.close()

    return quantity



# 运行函数
if __name__ == '__main__':
    insert_crypto_record(raw_data={
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
            "eventType": "filled",
            "pTime": "1777396609026",
            "posData": [{
                "avgPx": "0",
                "baseBal": "",
                "ccy": "USDT",
                "instId": "ETH-USDT-SWAP",
                "instType": "SWAP",
                "mgnMode": "iBZated",
                "nonSettleAvgPx": "",
                "pos": "0",
                "posCcy": "",
                "posId": "3519604495194988550",
                "posSide": "long",
                "quoteBal": "",
                "settledPnl": "",
                "tradeId": "3803318883",
                "uTime": "1777396609026"
            }],
            "trades": [{
                "instId": "ETH-USDT-SWAP",
                "tradeId": "3803318883"
            }]
        }]})
