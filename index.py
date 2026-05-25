import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import requests
from datetime import datetime

app = Flask(__name__)

# === API SETUP ===
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '')
WA_TOKEN = os.environ.get('WHATSAPP_TOKEN', '')
PHONE_ID = os.environ.get('PHONE_NUMBER_ID', '')
VERIFY_TOKEN = "bigil2024"

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

chats = {}
leads = []

BUSINESS = {
    "name": "Demo Restaurant",
    "type": "Restaurant",
    "timings": "10 AM - 11 PM",
    "location": "Jaipur",
    "menu": "\n    🍛 Dal Tadka - ₹120\n    🍗 Chicken Curry - ₹200  \n    🫓 Butter Naan - ₹40\n    🥗 Paneer Tikka - ₹160\n    🥤 Lassi - ₹60\n    ",
    "phone": "9999999999"
}

BIGIL_PROMPT = f"Aap BIGIL AI ke through {BUSINESS['name']} ke WhatsApp assistant ho. Friendly raho, Hindi+English mix karo, short answers do aur end mein ek question pucho."

@app.route('/', methods=['GET'])
def home():
    return f"<h1>🚀 BIGIL AI Dashboard</h1><p>Status: 🟢 LIVE ON VERCEL</p>"

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge')
    return "Error", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json or {}
    try:
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' not in value:
            return "OK", 200
            
        msg = value['messages'][0]
        phone = msg['from']
        name = value.get('contacts', [{}])[0].get('profile', {}).get('name', 'Customer')
        
        if msg.get('type') != 'text':
            send_msg(phone, "Namaste! 😊 Text message bhejiye.")
            return "OK", 200
            
        user_text = msg['text']['body']
        reply = ai_response(phone, name, user_text)
        send_msg(phone, reply)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return "OK", 200

def ai_response(phone, name, message):
    if phone not in chats:
        chats[phone] = []
    try:
        chat = model.start_chat(history=chats[phone])
        response = chat.send_message(f"{BIGIL_PROMPT}\n\nCustomer: {message}")
        reply = response.text
        chats[phone].extend([{"role": "user", "parts": [message]}, {"role": "model", "parts": [reply]}])
        return reply
    except Exception as e:
        return "Namaste! 🙏 Thodi dikkat hai, 2 min baad try karein."

def send_msg(phone, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": phone, "type": "text", "text": {"body": text[:4000]}}
    r = requests.post(url, json=data, headers=headers)
    return r.status_code
