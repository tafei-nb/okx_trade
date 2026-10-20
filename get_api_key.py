import json


def save_to_json(filename="AAA密钥.json"):
    """
    将数据保存为 JSON 文件，格式化输出方便手工修改。
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            # indent=4 让代码缩进整齐
            # ensure_ascii=False 确保中文不乱码，方便你手工阅读和编辑
            json_load = json.load(f)
        name = json_load.get('name')
        api_key = json_load.get('api_key')
        secret_key = json_load.get('secret_key')
        passphrase = json_load.get('passphrase')
        return name, api_key, secret_key, passphrase

    except Exception as e:
        print(f"❌ 保存失败: {e}")

if __name__ == "__main__":
    save_to_json()