import requests
from bs4 import BeautifulSoup
import time
import os
from datetime import datetime

# ================== CONFIG ==================
PANEL_URL = "http://168.119.13.175"
LOGIN_URL = f"{PANEL_URL}/ints/login"
DASHBOARD_URL = f"{PANEL_URL}/ints/client/SMSCDRStats"

USERNAME = "smartmethod4k"
PASSWORD = "smartmethod"

BOT_TOKEN = "8762087022:AAF9hjOokbaUBLJkUOBaUfjWVK7gn9xQFus"
CHAT_ID = "-1003820143618"

# ===========================================

session = requests.Session()

def solve_captcha(text):
    try:
        part = text.split("What is")[1].split("=")[0].strip()
        nums = part.split("+")
        return str(int(nums[0].strip()) + int(nums[1].strip()))
    except:
        return "0"

def login():
    global session
    session = requests.Session()
    
    r = session.get(LOGIN_URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    captcha_text = soup.find(string=lambda text: text and "What is" in text)
    captcha_answer = solve_captcha(captcha_text) if captcha_text else "0"
    
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "captcha": captcha_answer
    }
    
    response = session.post(LOGIN_URL, data=payload)
    
    if "SMSCDRStats" in response.text or response.url == DASHBOARD_URL:
        print("✅ Login Successful")
        return True
    else:
        print("❌ Login Failed")
        return False

def get_latest_sms():
    try:
        r = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        table = soup.find("table")
        if not table:
            return []
        
        rows = table.find_all("tr")[1:15]   # আরও কিছু রো নেওয়া হলো
        sms_list = []
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                date = cols[0].text.strip()
                number = cols[2].text.strip()
                message = cols[4].text.strip()
                
                sms_list.append({
                    "date": date,
                    "number": number,
                    "message": message[:500]
                })
        return sms_list
    except:
        return []

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=8)
    except:
        pass

# ============= MAIN LOOP =============
if __name__ == "__main__":
    print("🚀 SMS Forwarder Started (2 Second Interval)...")
    
    if not login():
        print("❌ Login failed!")
        exit()
    
    while True:
        try:
            sms_list = get_latest_sms()
            
            for sms in sms_list:
                msg_text = f"🔔 <b>New Message Received</b>\n\n" \
                           f"📱 <b>Number:</b> {sms['number']}\n" \
                           f"⏰ <b>Time:</b> {sms['date']}\n\n" \
                           f"📩 <b>Message:</b>\n{sms['message']}"
                
                send_to_telegram(msg_text)
                time.sleep(0.5)   # টেলিগ্রামে একটু গ্যাপ
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked")
            time.sleep(2)   # ← এখানে ২ সেকেন্ড
            
        except Exception as e:
            print("Error:", e)
            time.sleep(5)
