import os
import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

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
    你是一位專業的台股與國際市場分析師。請針對最新市場行情，撰寫一份條列式的重點分析報告。
    報告內容必須嚴格包含以下 7 大項目：
    1. 目前的國際經濟情勢以及未來趨勢發展的重點摘要。
    2. 目前股市熱錢在哪些領域的股票中（領域請細化至做項，例如：探針卡、功率元件、CPO、水冷散熱等）。
    3. 分別列出這些領域的所有股票並標示哪些是指標股票，同時附上這些股票目前的參考股價。
    4. 分別列出這些股票股價的壓力點以及近期的交易量大低點（支撐點）。
    5. 列出目前股價處於三角收斂而即將要上升的股票。
    6. 對上述股票的專業投資看法以及建議。
    7. 對未來的投資看法及建議，若有建議投資的股票請同步列出。
    """

    # 優先嘗試的模型與備援模型列表
    models_to_try = ['gemini-3.8-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    report_content = None

    for model_name in models_to_try:
        print(f"正在嘗試使用模型 {model_name} 生成市場報告...")
        for attempt in range(3):  # 每個模型最多重試 3 次（因應 503 伺服器忙碌）
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                report_content = response.text
                print(f"🎉 成功使用 {model_name} 生成分析報告！")
                break
            except Exception as e:
                print(f"使用 {model_name} 第 {attempt + 1} 次嘗試失敗: {e}")
                time.sleep(3)  # 等待 3 秒後重試
        
        if report_content:
            break

    if not report_content:
        print("錯誤：所有模型與重試均失敗，請稍後再試。")
        sys.exit(1)

    print(f"準備發送 Email 至 enjoy9091@gmail.com...")
    receiver_email = "enjoy9091@gmail.com"

    msg = MIMEMultipart()
    msg["From"] = f"台股 AI 分析師 <{sender_email}>"
    msg["To"] = receiver_email
    msg["Subject"] = "【每日台股與國際市場重點分析報告】"
    msg.attach(MIMEText(report_content, "plain", "utf-8"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.close()
        print("🎉 每日市場報告已成功寄出！")
    except Exception as e:
        print(f"Email 發送失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
