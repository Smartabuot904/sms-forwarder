import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# ================== CONFIG ==================
PANEL_BASE = "http://168.119.13.175"
LOGIN_URL = "http://168.119.13.175/ints/login"
DASHBOARD_URL = "http://168.119.13.175/ints/client/SMSDashboard"
SMS_URL = "http://168.119.13.175/ints/client/SMSCDRStats"   # যেখানে মেসেজ দেখা যায়

USERNAME = "smartmethod4k"
PASSWORD = "smartmethod"

BOT_TOKEN = "8762087022:AAF9hjOokbaUBLJkUOBaUfjWVK7gn9xQFus"
CHAT_ID = "-1003820143618"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

session = requests.Session()

def solve_captcha(text):
    print(f"Raw Captcha: {text}")
    try:
        if "What is" in text and "+" in text and "=" in text:
            part = text.split("What is")[1].split("=")[0].strip()
            a, b = [x.strip() for x in part.split('+')]
            result = int(a) + int(b)
            print(f"Captcha Solved: {result}")
            return str(result)
    except:
        pass
    return "0"

def login():
    global session
    session = requests.Session()
    session.headers.update(HEADERS)
    
    print("🔑 Trying to login...")
    for attempt in range(5):
        try:
            # লগইন পেজ খুলি
            r = session.get(LOGIN_URL, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            captcha_text = soup.find(string=lambda t: t and "What is" in str(t))
            captcha_answer = solve_captcha(str(captcha_text))
            
            payload = {
                "username": USERNAME,
                "password": PASSWORD,
                "captcha": captcha_answer
            }
            
            response = session.post(LOGIN_URL, data=payload, timeout=20, allow_redirects=True)
            
            print(f"Attempt {attempt+1} | Status: {response.status_code} | URL: {response.url}")
            
            # সফল লগইন চেক (একাধিক সম্ভাব্য শব্দ)
            if any(word in response.text for word in ["SMSDashboard", "SMSCDRStats", "SMS CDR", "My Payout", "Recent Ranges"]):
                print("✅ Login Successful!")
                return True
                
        except Exception as e:
            print("Login Error:", e)
        
        time.sleep(4)
    
    print("❌ Login Failed after all attempts")
    return False

# ============= MAIN LOOP =============
if __name__ == "__main__":
    print("🚀 SMS Forwarder Started (2 Second Interval)...")
    
    if not login():
        print("Could not login. Retrying every 30 seconds...")
        while True:
            time.sleep(30)
            if login():
                break
    
    print("✅ Successfully Logged In - Now Monitoring SMS...")
    
    while True:
        try:
            # SMS Report পেজে যাও
            r = session.get(SMS_URL, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            table = soup.find("table")
            if table:
                rows = table.find_all("tr")[1:15]   # সর্বশেষ ১৪টা মেসেজ
                
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 5:
                        date_str = cols[0].text.strip()
                        number = cols[2].text.strip()
                        message = cols[4].text.strip()
                        
                        telegram_text = f"""🔔 <b>New WhatsApp Code Received</b>

📱 <b>Number:</b> {number}
⏰ <b>Time:</b> {date_str}

📩 <b>Message:</b>
{message}"""

                        # Telegram-এ পাঠান
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": CHAT_ID,
                                "text": telegram_text,
                                "parse_mode": "HTML"
                            }
                        )
                        time.sleep(0.7)   # Telegram Rate Limit এড়ানোর জন্য
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked SMS Page")
            time.sleep(2)   # ২ সেকেন্ড পর পর চেক
            
        except Exception as e:
            print("Error:", e)
            time.sleep(8)
