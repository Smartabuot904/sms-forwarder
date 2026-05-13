import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# ================== CONFIG ==================
PANEL_URL = "http://168.119.13.175"
LOGIN_URL = f"{PANEL_URL}/ints/login"
DASHBOARD_URL = f"{PANEL_URL}/ints/client/SMSCDRStats"

USERNAME = "smartmethod4k"
PASSWORD = "smartmethod"

BOT_TOKEN = "8762087022:AAF9hjOokbaUBLJkUOBaUfjWVK7gn9xQFus"
CHAT_ID = "-1003820143618"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

session = requests.Session()

def solve_captcha(text):
    print(f"Raw Captcha: {text}")
    try:
        if "What is" in text and "=" in text:
            part = text.split("What is")[1].split("=")[0].strip()
            if '+' in part:
                a, b = part.split('+')
                result = int(a.strip()) + int(b.strip())
                print(f"Captcha Solved: {result}")
                return str(result)
    except:
        pass
    return "0"

def login():
    global session
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for attempt in range(5):
        try:
            # Get Login Page
            r = session.get(LOGIN_URL, timeout=20)
            print(f"Login Page Status: {r.status_code}")
            
            soup = BeautifulSoup(r.text, 'html.parser')
            captcha_text = soup.find(string=lambda t: t and "What is" in t)
            captcha_answer = solve_captcha(captcha_text if captcha_text else "")
            
            payload = {
                "username": USERNAME,
                "password": PASSWORD,
                "captcha": captcha_answer
            }
            
            print(f"Attempt {attempt+1} | Captcha: {captcha_answer}")
            response = session.post(LOGIN_URL, data=payload, headers=HEADERS, timeout=20)
            
            print(f"Login Response Code: {response.status_code}")
            
            if response.status_code == 200 and ("SMSCDRStats" in response.text or "Dashboard" in response.text):
                print("✅ Login Successful!")
                return True
            else:
                print("❌ Login Failed")
                
        except Exception as e:
            print("Error:", str(e))
        
        time.sleep(4)
    
    return False

# ============= MAIN LOOP =============
if __name__ == "__main__":
    print("🚀 SMS Forwarder Started...")
    
    if not login():
        print("❌ Login failed after retries.")
        while True:
            time.sleep(60)
            if login():
                break
    
    print("✅ Monitoring Started (2s interval)")
    while True:
        try:
            r = session.get(DASHBOARD_URL, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find("table")
            
            if table:
                rows = table.find_all("tr")[1:12]
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 5:
                        date = cols[0].text.strip()
                        number = cols[2].text.strip()
                        msg = cols[4].text.strip()[:500]
                        
                        text = f"🔔 <b>New WhatsApp Code</b>\n\n" \
                               f"📱 <b>Number:</b> {number}\n" \
                               f"⏰ <b>Time:</b> {date}\n\n" \
                               f"📨 <b>Message:</b>\n{msg}"
                        
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
                        )
                        time.sleep(0.7)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked")
            time.sleep(2)
            
        except Exception as e:
            print("Loop Error:", e)
            time.sleep(10)
