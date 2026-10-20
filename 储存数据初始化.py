
import pymysql
from datetime import datetime


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

def insert_crypto_record(raw_data):
    # 2. 建立数据库连接
    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor() as cursor:
            # 3. 准备你要存入的数据
            symbol, quantity, price, record_time = extract_for_db_frist(raw_data)
              # 支持小数
            # 获取当前时间，并精确到分钟（去掉秒，方便按分钟统计）
            record_time = datetime.now().strftime('%Y-%m-%d %H:%M:00')

            # 4. 编写 SQL 语句 (核心重点 ⬇️)
            # 使用 ON DUPLICATE KEY UPDATE：
            # 如果同一分钟内还没有 BTC 的数据，就正常插入；
            # 如果同一分钟内已经有 BTC 的数据了，就更新数量和价格，坚决不报错！
            sql = """
                INSERT INTO item_records (symbol, quantity, price, record_time)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    quantity = VALUES(quantity),
                    price = VALUES(price)
            """

            # 5. 执行 SQL 语句（千万不要用字符串拼接 SQL，%s 能防止 SQL 注入）
            cursor.execute(sql, (symbol, quantity, price, record_time))

        # 6. 提交事务（不执行 commit 的话，数据只在内存里，不会真正存入表）
        connection.commit()
        print(f"✅ 成功存入数据: {symbol} | 价格: {price} | 时间: {record_time}")

    except Exception as e:
        print(f"❌ 存入数据失败，错误信息: {e}")
        # 发生错误时回滚
        connection.rollback()

    finally:
        # 7. 无论成功失败，最后一定要关闭连接释放资源
        connection.close()




def extract_for_db_frist(raw_data):
    """
    只提取用于存入数据库的 4 个核心变量：
    symbol (名称), quantity (数量), price (价格), record_time (时间)
    """
    # 获取 data 列表中的第一个元素
    get_data = raw_data.get("data", [{}])
    for data in get_data:
        data_item = data[0]
        # 1. 提取并转换时间 (毫秒时间戳 -> MySQL DATETIME 格式)
        p_time_ms = int(data_item.get("pTime", 0))
        record_time = datetime.fromtimestamp(p_time_ms / 1000.0).strftime('%Y-%m-%d %H:%M:%S')

        # 2. 提取仓位信息中的 名称、数量、价格
        pos_data = data_item.get("posData", [{}])[0]
        symbol = pos_data.get("instId", "")  # 名称 (例如: ETH-USDT-SWAP)
        quantity = pos_data.get("pos", "0")  # 数量(余额)
        price = pos_data.get("avgPx", "0")  # 价格

        return symbol, quantity, price, record_time


data_list = {
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
			"cashBal": "1.4616831279525037",
			"ccy": "USDT",
			"uTime": "1777405012044"
		}],
		"eventType": "snapshot",
		"pTime": "1777457411327",
		"posData": [],
		"trades": []
	}]
}



if __name__ =='__main__':
    insert_crypto_record(data_list)