import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re

# ================= CONFIG =================

LOGIN_URL = "http://168.119.13.175/ints/login"
DASHBOARD_URL = "http://168.119.13.175/ints/client/SMSDashboard"
SMS_URL = "http://168.119.13.175/ints/client/SMSCDRStats"

USERNAME = "smartmethod4k"
PASSWORD = "smartmethod"

BOT_TOKEN = "8762087022:AAF9hjOokbaUBLJkUOBaUfjWVK7gn9xFus"
CHAT_ID = "-1003820143618"

CHECK_INTERVAL = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": LOGIN_URL
}

session = requests.Session()
session.headers.update(HEADERS)

sent = set()

# ================= CAPTCHA =================

def solve_captcha(text):
    print("CAPTCHA RAW:", text)

    nums = re.findall(r'\d+', text)

    if len(nums) >= 2:
        a = int(nums[0])
        b = int(nums[1])

        result = a + b
        print("CAPTCHA SOLVED:", result)

        return str(result)

    print("CAPTCHA FAILED -> 0")
    return "0"

# ================= LOGIN =================

def login():
    global session

    print("🔐 Login page open...")

    r = session.get(LOGIN_URL, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    # INPUT DEBUG
    print("📌 INPUT FIELDS:")
    for i in soup.find_all("input"):
        print(i)

    # CAPTCHA PART (FIXED INDENTATION)
    captcha_text = soup.find(string=lambda t: t and "What is" in str(t))

    print("CAPTCHA TEXT:", captcha_text)

    if captcha_text:
        captcha = solve_captcha(captcha_text)
    else:
        print("❌ CAPTCHA NOT FOUND")
        captcha = "0"

    print("CAPTCHA FINAL:", captcha)

    # PAYLOAD
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "capt": captcha
    }

    print("PAYLOAD:", payload)

    # LOGIN REQUEST
    res = session.post(
        LOGIN_URL,
        data=payload,
        timeout=20,
        allow_redirects=True
    )

    dash = session.get(DASHBOARD_URL, timeout=20)

    if "login" not in dash.url.lower():
        print("✅ LOGIN SUCCESS")
        return True

    print("❌ LOGIN FAILED")

    with open("login_fail.html", "w", encoding="utf-8") as f:
        f.write(res.text)

    return False

# ================= TELEGRAM =================

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        })
    except Exception as e:
        print("Telegram error:", e)

# ================= SMS CHECK =================

def check_sms():
    print("📨 Checking SMS...")

    r = session.get(SMS_URL, timeout=20)

    if "login" in r.url.lower():
        print("⚠ SESSION EXPIRED")
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table")

    if not table:
        print("❌ TABLE NOT FOUND")
        return True

    rows = table.find_all("tr")[1:20]

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 5:
            continue

        date = cols[0].text.strip()
        number = cols[2].text.strip()
        msg = cols[4].text.strip()

        uid = f"{date}-{number}-{msg}"

        if uid in sent:
            continue

        sent.add(uid)

        text = f"""🔔 NEW SMS

📱 Number: {number}
⏰ Time: {date}

📩 Message:
{msg}"""

        print("📤 Sending Telegram...")
        send_telegram(text)

        time.sleep(1)

    return True

# ================= MAIN =================

if __name__ == "__main__":

    print("🚀 BOT STARTED")

    while True:
        if login():
            break
        time.sleep(30)

    print("✅ MONITORING SMS...")

    while True:

        ok = check_sms()

        if not ok:
            print("🔄 RELOGIN...")
            while not login():
                time.sleep(20)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked")

        time.sleep(CHECK_INTERVAL)
