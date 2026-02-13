import streamlit as st
import pandas as pd
from datetime import date
import re
from PIL import Image
import pytesseract
import os
import smtplib
from email.message import EmailMessage

# --- EMAIL SETTINGS ---
# Enter your email and 16-digit App Password here
MY_EMAIL = "smiles4j41@gmail.com"
MY_PASSWORD = "kpnq ccpd ekrf stpo"
RECEIVER_EMAIL = "smiles4j41@gmail.com"

# --- LOGIN SETTINGS ---
USER_DB = {"admin": "admin123", "staff": "staff123"}
st.set_page_config(page_title="Expense Tracker", layout="wide")
DATA_FILE = "company_data.csv"

# --- DATA FUNCTIONS ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Date", "Type", "Account_Num", "Employee", "Vendor", "Amount", "Payment", "Last4", "Category", "Details"])

def scan_images(files):
    amt, last4, acct = 0.0, "", ""
    for f in files:
        try:
            img = Image.open(f)
            text = pytesseract.image_to_string(img)
            # Find Amount
            found_amts = re.findall(r"\d+\.\d{2}", text)
            if found_amts:
                high = float(max(found_amts))
                if high > amt: amt = high
            # Find Card
            c = re.search(r"(?:\*{4}|Ending in|#)\s*(\d{4})", text, re.IGNORECASE)
            if c: last4 = c.group(1)
            # Find Account
            a = re.search(r"(?:Acct|Account)[:#\s]+(\d{5,15})", text, re.IGNORECASE)
            if a: acct = a.group(1)
        except: pass
    return amt, last4, acct

# --- LOGIN SCREEN ---
if "auth" not in st.session_state:
    st.title("🔒 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state.update({"auth": True, "user": u})
            st.rerun()
    st.stop()

# --- MAIN APP ---
st.title("🧾 Expense Manager")
t1, t2 = st.tabs(["📝 Add Entry", "📊 Reports"])

with t1:
    if 'scan_amt' not in st.session_state:
        st.session_state.update({'scan_amt': 0.0, 'scan_l4': "", 'scan_acc': ""})

    files = st.file_uploader("Upload Photos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if files and st.button("🔍 Scan Photos"):
        amt, l4, acc = scan_images(files)
        st.session_state.update({'scan_amt': amt, 'scan_l4': l4, 'scan_acc': acc})
        st.success("Scan Finished")

    with st.form("entry_form"):
        doc_type = st.selectbox("Type", ["Receipt", "Invoice"])
        acc_num = st.text_input("Account #", value=st.session_state['scan_acc']) if doc_type == "Invoice" else "N/A"
        
        c1, c2 = st.columns(2)
        v_date = c1.date_input("Date", date.today())
        vendor = c2.text_input("Vendor")
        
        c3, c4, c5 = st.columns(3)
        amount = c3.number_input("Amount", value=st.session_state['scan_amt'])
        pay_m = c4.selectbox("Payment", ["Card", "Cash", "Check", "EFT"])
        l4_digits = c5.text_input("Last 4", value=st.session_state['scan_l4']) if pay_m == "Card" else "N/A"
        
        cat = st.selectbox("Category", ["Admin", "Travel", "Marketing", "Vendor", "Other"])
        details = st.text_area("Details")
        
        if st.form_submit_button("Save"):
            df = load_data()
            new_row = pd.DataFrame([[v_date, doc_type, acc_num, st.session_state['user'], vendor, amount, pay_m, l4_digits, cat, details]], columns=df.columns)
            
            # Save to CSV
            if os.path.exists(DATA_FILE):
                new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
            else:
                new_row.to_csv(DATA_FILE, index=False)
            
            st.success("Saved!")
            
            # Send Email
            if doc_type == "Invoice":
                try:
                    msg = EmailMessage()
                    msg.set_content(f"New Invoice: {vendor} - ${amount}")
                    msg['Subject'] = "Invoice Alert"
                    msg['From'] = MY_EMAIL
                    msg['To'] = RECEIVER_EMAIL
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                        s.login(MY_EMAIL, MY_PASSWORD)
                        s.send_message(msg)
                except: pass

with t2:
    st.header("Records")
    df = load_data()
    if not df.empty:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Excel", data=csv, file_name="expenses.csv", mime="text/csv")
    else:
        st.info("No records found.")
