import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI

# 1. 初始化 OpenAI 客戶端
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_report():
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
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

def send_email(report_content):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
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
        print("每日市場報告寄送成功！")
    except Exception as e:
        print(f"發送失敗: {e}")

if __name__ == "__main__":
    report = generate_report()
    send_email(report)
