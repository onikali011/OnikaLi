"""
ÖNIKA LI Webhook 设置脚本
"""

import os
import requests

TOKEN = os.getenv('TELEGRAM_TOKEN')
VERCEL_URL = os.getenv('VERCEL_URL', 'https://onikali.vercel.app')

if not TOKEN:
    print("❌ 错误: 请设置 TELEGRAM_TOKEN 环境变量")
    exit(1)

WEBHOOK_URL = f"{VERCEL_URL}/"

def set_webhook():
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            json={
                "url": WEBHOOK_URL,
                "allowed_updates": ["message", "callback_query"]
            }
        )
        data = response.json()

        if data.get('ok'):
            print(f"✅ Webhook 设置成功!")
            print(f"🌐 URL: {WEBHOOK_URL}")

            # 获取信息
            info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo").json()
            if info.get('ok'):
                print(f"📊 挂起更新数: {info['result'].get('pending_update_count', 0)}")
        else:
            print(f"❌ 设置失败: {data.get('description', '未知错误')}")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    set_webhook()
