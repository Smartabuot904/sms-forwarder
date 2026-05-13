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
    
    for attempt in range(6):
        try:
            r = session.get(LOGIN_URL, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            captcha_text = soup.find(string=lambda t: t and "What is" in str(t))
            captcha_answer = solve_captcha(str(captcha_text))
            
            payload = {
                "username": USERNAME,
                "password": PASSWORD,
                "captcha": captcha_answer
            }
            
            print(f"Attempt {attempt+1} | Captcha: {captcha_answer}")
            response = session.post(LOGIN_URL, data=payload, timeout=20, allow_redirects=True)
            
            print(f"Status Code: {response.status_code} | Final URL: {response.url}")
            
            # আরও ভালো চেকিং
            if any(keyword in response.text for keyword in ["SMSCDRStats", "SMS CDR Reports", "Range", "Number", "CLI", "My Payout"]):
                print("✅ Login Successful! (Detected Dashboard)")
                return True
            else:
                print("❌ Login Failed - Dashboard not detected")
                print("Response snippet:", response.text[:400])
                
        except Exception as e:
            print("Error:", e)
        
        time.sleep(5)
    
    return False

# ============= MAIN =============
if __name__ == "__main__":
    print("🚀 SMS Forwarder Started...")
    
    if not login():
        print("❌ Login failed after multiple attempts.")
        while True:
            print("Waiting 40 seconds before retry...")
            time.sleep(40)
            if login():
                break
    
    print("✅ Monitoring Started (2s interval)")
    
    while True:
        try:
            r = session.get(DASHBOARD_URL, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find("table")
            
            if table:
                rows = table.find_all("tr")[1:15]
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 5:
                        date = cols[0].text.strip()
                        number = cols[2].text.strip()
                        message = cols[4].text.strip()[:600]
                        
                        text = f"""🔔 <b>New WhatsApp Code Received</b>

📱 <b>Number:</b> {number}
⏰ <b>Time:</b> {date}

📩 <b>Message:</b>
{message}"""
                        
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
                        )
                        time.sleep(0.6)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checked")
            time.sleep(2)
            
        except Exception as e:
            print("Error in loop:", e)
            time.sleep(8)
