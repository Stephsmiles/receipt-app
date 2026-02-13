import streamlit as st
import pandas as pd
from datetime import date
import re
from PIL import Image
import pytesseract
import os
import smtplib
from email.message import EmailMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials

1. EMAIL SETUP
Type your Gmail address and 16-digit App Password inside the quotes
MY_EMAIL = "smiles4j41@gmail.com"

MY_PASSWORD = "kpnq ccpd ekrf stpo"
RECEIVER_EMAIL = "smiles4j41@gmail.com"

2. LOGIN SETUP
USER_DB = {"admin": "admin123", "staff": "staff123"}
st.set_page_config(page_title="Expense Tracker", layout="wide")

3. GOOGLE SHEETS FUNCTION
def save_to_google(new_row_list):
scope = ["", ""]
creds_dict = {
"type": st.secrets["type"],
"project_id": st.secrets["project_id"],
"private_key_id": st.secrets["private_key_id"],
"private_key": st.secrets["private_key"],
"client_email": st.secrets["client_email"],
"client_id": st.secrets["client_id"],
"auth_uri": st.secrets["auth_uri"],
"token_uri": st.secrets["token_uri"],
"auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
"client_x509_cert_url": st.secrets["client_x509_cert_url"]
}
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(st.secrets["gsheet_url"]).sheet1
sheet.append_row(new_row_list)

4. SCANNING LOGIC
def scan_images(files):
amt, last4, acct = 0.0, "", ""
for f in files:
img = Image.open(f)
text = pytesseract.image_to_string(img)
found_amts = re.findall(r"\d+.\d{2}", text)
if found_amts:
high = float(max(found_amts))
if high > amt: amt = high
c = re.search(r"(?:*{4}|Ending in|#)\s*(\d{4})", text, re.IGNORECASE)
if c: last4 = c.group(1)
a = re.search(r"(?:Acct|Account)[:#\s]+(\d{5,15})", text, re.IGNORECASE)
if a: acct = a.group(1)
return amt, last4, acct

5. LOGIN SCREEN
if "auth" not in st.session_state:
st.title("🔒 Login")
u = st.text_input("Username")
p = st.text_input("Password", type="password")
if st.button("Login"):
if u in USER_DB and USER_DB[u] == p:
st.session_state.update({"auth": True, "user": u})
st.rerun()
st.stop()

6. MAIN APP
st.title("🧾 Expense Manager")
t1, t2 = st.tabs(["📝 Add Entry", "📊 Status"])

with t1:
if 'scan_amt' not in st.session_state:
st.session_state.update({'scan_amt': 0.0, 'scan_l4': "", 'scan_acc': ""})

with t2:
st.write("Records are saved to your Google Sheet.")
