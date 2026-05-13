import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# ================= CONFIG =================

LOGIN_URL = "http://168.119.13.175/ints/login"
DASHBOARD_URL = "http://168.119.13.175/ints/client/SMSDashboard"
SMS_REPORT_URL = "http://168.119.13.175/ints/client/SMSCDRStats"

USERNAME = "smartmethod4k"
PASSWORD = "smartmethod"

BOT_TOKEN = "8762087022:AAF9hjOokbaUBLJkUOBaUfjWVK7gn9xQFus"
CHAT_ID = "-1003820143618"

CHECK_INTERVAL = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": LOGIN_URL
}

# ==========================================

session = requests.Session()
session.headers.update(HEADERS)

sent_messages = set()


def solve_captcha(text):
    """
    Example:
    What is 5 + 7 = ?
    """

    try:
        text = text.replace("What is", "").replace("=", "").replace("?", "").strip()

        if "+" in text:
            a, b = text.split("+")
            return str(int(a.strip()) + int(b.strip()))

    except Exception as e:
        print("Captcha Error:", e)

    return "0"


def login():
    global session

    print("🔐 Opening login page...")

    try:
        r = session.get(LOGIN_URL, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        # captcha বের করা
        captcha_text = soup.find(string=lambda t: t and "What is" in str(t))

        if not captcha_text:
            print("❌ Captcha not found")
            return False

        captcha_answer = solve_captcha(str(captcha_text))

        print("✅ Captcha Solved:", captcha_answer)

        # সব hidden input collect
        payload = {}

        hidden_inputs = soup.find_all("input", type="hidden")

        for hidden in hidden_inputs:
            name = hidden.get("name")
            value = hidden.get("value", "")

            if name:
                payload[name] = value

        # form input names
        payload.update({
            "username": USERNAME,
            "password": PASSWORD,
            "captcha": captcha_answer
        })

        print("🚀 Sending Login Request...")

        response = session.post(
            LOGIN_URL,
            data=payload,
            timeout=20,
            allow_redirects=True
        )

        print("Status:", response.status_code)
        print("Final URL:", response.url)

        # dashboard page check
        dashboard = session.get(DASHBOARD_URL, timeout=20)

        if "SMSDashboard" in dashboard.text or dashboard.status_code == 200:
            print("✅ LOGIN SUCCESSFUL")
            return True

        print("❌ Login Failed")

        # debug html save
        with open("failed_login.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        return False

    except Exception as e:
        print("LOGIN ERROR:", e)
        return False


def send_to_telegram(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=data, timeout=15)
    except Exception as e:
        print("Telegram Error:", e)


def check_sms():

    print("📨 Opening SMS Report Page...")

    try:
        r = session.get(SMS_REPORT_URL, timeout=20)

        # login expire হলে
        if "login" in r.url.lower():
            print("⚠ Session Expired")
            return False

        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table")

        if not table:
            print("❌ SMS Table Not Found")

            with open("sms_page.html", "w", encoding="utf-8") as f:
                f.write(r.text)

            return True

        rows = table.find_all("tr")[1:20]

        for row in rows:

            cols = row.find_all("td")

            if len(cols) < 5:
                continue

            try:
                date_text = cols[0].text.strip()
                number = cols[2].text.strip()
                message = cols[4].text.strip()

                unique_id = f"{date_text}-{number}-{message}"

                if unique_id in sent_messages:
                    continue

                sent_messages.add(unique_id)

                telegram_message = f"""
🔔 <b>NEW SMS RECEIVED</b>

📱 <b>Number:</b> {number}

⏰ <b>Time:</b>
{date_text}

📩 <b>Message:</b>
{message}
"""

                print("📤 Sending To Telegram...")
                print(telegram_message)

                send_to_telegram(telegram_message)

                time.sleep(1)

            except Exception as e:
                print("Row Error:", e)

        return True

    except Exception as e:
        print("SMS CHECK ERROR:", e)
        return True


# ================= MAIN =================

if __name__ == "__main__":

    print("🚀 SMS FORWARDER STARTED")

    while True:

        if login():
            break

        print("🔄 Retrying login after 30 seconds...")
        time.sleep(30)

    print("✅ BOT IS NOW MONITORING SMS")

    while True:

        ok = check_sms()

        # session expire হলে আবার login
        if not ok:

            print("🔑 Re-Logging...")

            while True:

                if login():
                    break

                time.sleep(20)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked")

        time.sleep(CHECK_INTERVAL)
