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
    """開啟 Google Search 聯網搜尋功能以獲取最新市場資訊"""
    return client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
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
    
    # 精簡且高價值的 Prompt，避免產生過多 Token 導致觸發配額限制
    prompt = """
    你是一位專業的台股與國際市場分析師。請透過 Google 搜尋最新市場資訊，撰寫一份條列式的重點分析報告：

    1. 【國際經濟情勢】摘要美股與全球宏觀經濟最新發展。
    2. 【台股熱錢領域】列出近期市場熱錢聚焦的 3-5 個產業/族群（例如：CPO、水冷散熱、探針卡等）。
    3. 【焦點個股與位階】針對重點族群，列出代表性指標股票、最新參考股價及近期支撐/壓力區間。
    4. 【專業投資建議】給予投資人的操作看法與風險提示。
    """

    model_name = 'gemini-3.8-flash'
    report_content = None

    print(f"正在請求 Google Gemini API ({model_name})...")
    try:
        # 單次請求設定 45 秒超時
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call_gemini_api, client, model_name, prompt)
            response = future.result(timeout=45)
        
        if response and response.text:
            report_content = response.text
            print(f"🎉 成功生成市場分析報告！")
    except TimeoutError:
        print(f"⚠️ API 連線超時 (45秒無回應)")
    except Exception as e:
        print(f"⚠️ API 調用失敗: {e}")

    if not report_content:
        print("錯誤：未能成功生成報告，請檢查 API Key 配額或網路連線。")
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
