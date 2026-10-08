import os
import sys
import time
import smtplib
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from google.genai import types

def call_gemini_api(client, model_name, prompt):
    """將 API 呼叫包裝成獨立函數，並開啟 Google 聯網搜尋功能"""
    return client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            # 開啟 Google 搜尋，讓 API 快速抓取最新即時股市資訊
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    print("--- 開始檢查設定值 ---")
    print(f"GEMINI_API_KEY 存在: {bool(api_key)}")
    print(f"SENDER_EMAIL 存在: {bool(sender_email)}")
    print(f"SENDER_PASSWORD 存在: {bool(sender_password)}")

    if not api_key:
        print("錯誤：未找到 GEMINI_API_KEY，請檢查 GitHub Secrets 設定！")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    
    prompt = """
    你是一位專業的台股與國際市場分析師。請搜尋最新台股與全球股市資訊，撰寫一份簡明扼要的重點分析報告：

    1. 【國際經濟情勢】摘要美股與全球宏觀經濟最新動態。
    2. 【台股熱錢焦點】列出近期市場熱錢聚焦的 3-5 個關鍵產業/族群（例如：CPO、水冷散熱、探針卡等）。
    3. 【焦點個股與參考價】針對上述熱門族群，列出代表性指標股票與近期參考股價。
    4. 【技術面與關鍵位階】摘要說明重點股票的近期支撐點與壓力點區間。
    5. 【專業投資建議】給予投資人的具體操作看法與風險提示。
    """

    model_name = 'gemini-3.8-flash'
    report_content = None

    print(f"正在嘗試使用官方推薦模型: {model_name}")
    for attempt in range(1, 5):  # 最多重試 4 次
        print(f"[{model_name}] 第 {attempt} 次嘗試連線...")
        try:
            # 單次請求限時 40 秒
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(call_gemini_api, client, model_name, prompt)
                response = future.result(timeout=40)
            
            if response and response.text:
                report_content = response.text
                print(f"🎉 成功使用 {model_name} 生成分析報告！")
                break
        except TimeoutError:
            print(f"⚠️ [{model_name}] 第 {attempt} 次連線超時，準備重試...")
        except Exception as e:
            err_msg = str(e)
            print(f"⚠️ [{model_name}] 第 {attempt} 次失敗: {err_msg}")
            
            # 如果遇到 429 配額不足或 503 伺服器忙碌，適當冷卻等待再試
            if "429" in err_msg or "503" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                wait_time = attempt * 15  # 依序等待 15s, 30s, 45s 等待 API 冷卻恢復配額
                print(f"檢測到 API 頻率限制 (429/503)，冷卻等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
                continue

    if not report_content:
        print("錯誤：模型連線超時或每日配額已滿，請稍後再試。")
        sys.exit(1)

    print("準備發送 Email 至 enjoy9091@gmail.com...")
    receiver_email = "enjoy9091@gmail.com"

    msg = MIMEMultipart()
    msg["From"] = f"台股 AI 分析師 <{sender_email}>"
    msg["To"] = receiver_email
    msg["Subject"] = "【每日台股與國際市場重點分析報告】"
    msg.attach(MIMEText(report_content, "plain", "utf-8"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.close()
        print("🎉 每日市場報告已成功寄出！")
    except Exception as e:
        print(f"Email 發送失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
