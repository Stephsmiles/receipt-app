import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import re
from PIL import Image
import pytesseract
import os
import smtplib
from email.message import EmailMessage

# --- 1. EMAIL CONFIG ---
# Replace with your real info!
MY_EMAIL = "smiles4j41@gmail.com"  
MY_PASSWORD = "kpnq ccpd ekrf stpo" 
RECEIVER_EMAIL = "smiles4j41@gmail.com"

# --- 2. LOGIN & SETUP ---
USER_DB = {"admin": "admin123", "staff": "staff123"}
st.set_page_config(page_title="Smart Tracker", layout="wide")
DATA_FILE = "company_data.csv"

# --- 3. CONNECTIONS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Check your Secrets vault!")

def save_to_google(new_entry_df):
    existing_data = conn.read(spreadsheet=st.secrets["gsheet_url"])
    updated_data = pd.concat([existing_data, new_entry_df], ignore_index=True)
    conn.update(spreadsheet=st.secrets["gsheet_url"], data=updated_data)

def send_invoice_email(emp, ven, amt, acc):
    try:
        msg = EmailMessage()
        msg.set_content(f"Invoice Logged!\n\nStaff: {emp}\nVendor: {ven}\nAmt: ${amt}")
        msg['Subject'] = f"🚨 Invoice: {ven}"
        msg['From'] = MY_EMAIL
        msg['To'] = RECEIVER_EMAIL
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(MY_EMAIL, MY_PASSWORD)
        server.send_message(msg)
        server.quit()
    except: pass

    # --- 4. OCR SCANNING LOGIC ---
def scan_multiple_images(uploaded_files):
    final_amt, final_last4, final_acct = 0.0, "", ""
    for file in uploaded_files:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)
        amounts = re.findall(r"\d+\.\d{2}", text)
        if amounts:
            file_max = float(max(amounts))
            if file_max > final_amt: final_amt = file_max
        card = re.search(r"(?:\*{4}|Ending in|Account|#)\s*(\d{4})", text, re.IGNORECASE)
        if card and not final_last4: final_last4 = card.group(1)
        acct = re.search(r"(?:Acct|Account|Cust|ID)[:#\s]+(\d{5,15})", text, re.IGNORECASE)
        if acct and not final_acct: final_acct = acct.group(1)
    return final_amt, final_last4, final_acct

# --- 5. LOGIN SCREEN ---
if "authenticated" not in st.session_state:
    st.title("🔒 Business Portal Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state.update({"authenticated": True, "user": u})
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- 6. MAIN INTERFACE ---
st.sidebar.write(f"Logged in: **{st.session_state['user']}**")
if st.sidebar.button("Logout"):
    del st.session_state["authenticated"]
    st.rerun()

st.title("🧾 Company Expense Manager")
tab1, tab2, tab3 = st.tabs(["📸 Add Entry", "📊 Reports", "🛠️ Manage Records"])

with tab1:
    st.header("Step 1: Upload & Scan")
    if 'auto_amount' not in st.session_state: 
        st.session_state.update({'auto_amount': 0.0, 'auto_last4': "", 'auto_acct': ""})

    uploaded_files = st.file_uploader("Upload Receipts/Invoices", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if uploaded_files and st.button("🔍 Scan All Images"):
        with st.spinner("Reading data..."):
            amt, last4, acct = scan_multiple_images(uploaded_files)
            st.session_state.update({'auto_amount': amt, 'auto_last4': last4, 'auto_acct': acct})
            st.success(f"Scan complete!")

    st.markdown("---")
    with st.form("entry_form"):
        st.subheader("Step 2: Details")
        doc_type = st.selectbox("Is this a Receipt or an Invoice?", ["Receipt", "Invoice"])
        acc_num = st.text_input("📝 INVOICE ACCOUNT NUMBER", value=st.session_state['auto_acct']) if doc_type == "Invoice" else "N/A"

        colA, colB = st.columns(2)
        v_date = colA.date_input("Date", date.today(), format="MM/DD/YYYY")
        vendor = colB.text_input("Vendor Name")
        
        colC, colD, colE = st.columns(3)
        amt = colC.number_input("Total Amount ($)", value=st.session_state['auto_amount'])
        pay_m = colD.selectbox("Payment Method", ["Card", "Cash", "Check", "EFT", "Other"])
        c_last4 = colE.text_input("Card Last 4 Digits", value=st.session_state['auto_last4'], max_chars=4) if pay_m == "Card" else "N/A"
        
        cat = st.selectbox("Category", ["Admin", "Cleaning/Maint.", "Travel", "Catering", "Vendor", "Marketing", "Franchise", "Other"])
        details = st.text_area("Details")
        no_p = st.checkbox("NO PHOTO AVAILABLE")
        
        if st.form_submit_button("Save Entry"):
            if not uploaded_files and not no_p: st.error("Photo required")
            else:
                new_row = pd.DataFrame([[v_date.strftime('%m/%d/%Y'), doc_type, acc_num, st.session_state['user'], vendor, amt, pay_m, c_last4, cat, details, len(uploaded_files)]], 
                                     columns=["Date", "Type", "Account_Num", "Employee", "Vendor", "Amount", "Payment_Method", "Card_Last4", "Category", "Details", "Photos_Count"])
                try:
                    save_to_google(new_row)
                    st.success("✅ Saved to Google Sheets!")
                except: st.warning("Backup saved locally.")
                
                # Local Backup
                if not os.path.exists("company_data.csv"): new_row.to_csv("company_data.csv", index=False)
                else: new_row.to_csv("company_data.csv", mode='a', header=False, index=False)
                
                if doc_type == "Invoice":
                    send_invoice_email(st.session_state['user'], vendor, amt, acc_num)

with tab2:
    st.header("Reports")
    if os.path.exists("company_data.csv"):
        df = pd.read_csv("company_data.csv")
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name="expenses.csv")

with tab3:
    st.header("Modify or Delete")
    if os.path.exists("company_data.csv"):
        df = pd.read_csv("company_data.csv")
        if not df.empty:
            sel = st.selectbox("Select Record", df.index)
            if st.button("🗑️ Delete Record"):
                df.drop(sel).to_csv("company_data.csv", index=False)
                st.rerun()
