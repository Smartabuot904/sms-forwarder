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

# ===========================================

session = requests.Session()

def solve_captcha(text):
    print(f"Raw Captcha Text: {text}")   # Debugging
    try:
        # আরও শক্তিশালী captcha solver
        if "What is" in text:
            part = text.split("What is")[1].split("=")[0].strip()
            # + চিহ্নের জন্য split
            if '+' in part:
                nums = part.split('+')
                result = int(nums[0].strip()) + int(nums[1].strip())
                print(f"Captcha Solved: {result}")
                return str(result)
    except Exception as e:
        print("Captcha solve error:", e)
    return "0"

def login():
    global session
    session = requests.Session()
    
    for attempt in range(3):   # ৩ বার চেষ্টা
        try:
            r = session.get(LOGIN_URL, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Captcha খুঁজে বের করা
            captcha_element = soup.find(string=lambda t: t and "What is" in t)
            captcha_text = captcha_element.strip() if captcha_element else ""
            
            captcha_answer = solve_captcha(captcha_text)
            
            payload = {
                "username": USERNAME,
                "password": PASSWORD,
                "captcha": captcha_answer
            }
            
            print(f"Attempt {attempt+1}: Trying login with captcha {captcha_answer}")
            response = session.post(LOGIN_URL, data=payload, timeout=15)
            
            if "SMSCDRStats" in response.text or response.url.endswith("SMSCDRStats"):
                print("✅ Login Successful!")
                return True
            else:
                print("❌ Login Failed on attempt", attempt+1)
                print("Response snippet:", response.text[:300])
                
        except Exception as e:
            print("Login error:", e)
        
        time.sleep(3)
    
    return False

def get_latest_sms():
    try:
        r = session.get(DASHBOARD_URL, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find("table")
        
        if not table:
            print("No table found")
            return []
        
        rows = table.find_all("tr")[1:10]
        sms_list = []
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                date = cols[0].text.strip()
                number = cols[2].text.strip()
                message = cols[4].text.strip()
                sms_list.append({"date": date, "number": number, "message": message[:500]})
        return sms_list
    except Exception as e:
        print("Get SMS Error:", e)
        return []

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

# ============= MAIN =============
if __name__ == "__main__":
    print("🚀 SMS Forwarder Started (2s Interval)...")
    
    if not login():
        print("❌ Could not login after multiple attempts.")
        # একবার লগইন ফেল করলে বারবার চেষ্টা করবে
        while True:
            print("Retrying login in 30 seconds...")
            time.sleep(30)
            if login():
                break
    
    print("✅ Starting monitoring...")
    while True:
        try:
            sms_list = get_latest_sms()
            for sms in sms_list:
                msg_text = f"🔔 <b>New Message</b>\n\n" \
                           f"📱 <b>Number:</b> {sms['number']}\n" \
                           f"⏰ <b>Time:</b> {sms['date']}\n\n" \
                           f"📩 <b>Message:</b>\n{sms['message']}"
                
                send_to_telegram(msg_text)
                time.sleep(0.8)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked successfully")
            time.sleep(2)
            
        except Exception as e:
            print("Main Loop Error:", e)
            time.sleep(5)
