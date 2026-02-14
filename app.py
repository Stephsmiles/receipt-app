import streamlit as st
import pandas as pd
from datetime import date
import re
from PIL import Image
import pytesseract
import os
import smtplib
from email.message import EmailMessage



MY_EMAIL = "smiles4j41@gmail.com"
MY_PASSWORD = "kpnq ccpd ekrf stpo"
RECEIVER_EMAIL = "smiles4j41@gmail.com"


USER_DB = {"admin": "admin123", "staff": "staff123"}
st.set_page_config(page_title="Bookkeeping Ledger", layout="wide")
DATA_FILE = "accounting_data.csv"


def load_data():
if os.path.exists(DATA_FILE):
return pd.read_csv(DATA_FILE)
return pd.DataFrame(columns=[
"Date", "Txn_Type", "Doc_Type", "Status", "Account_Num",
"Employee", "Entity", "Amount", "Payment_Method",
"Last4", "Category", "Details"
])

def scan_images(files):
amt, last4, acct = 0.0, "", ""
for f in files:
try:
img = Image.open(f)
text = pytesseract.image_to_string(img)
# Find Amount
found_amts = re.findall(r"\d+.\d{2}", text)
if found_amts:
high = float(max(found_amts))
if high > amt: amt = high
# Find Card
c = re.search(r"(?:*{4}|Ending in|#)\s*(\d{4})", text, re.IGNORECASE)
if c: last4 = c.group(1)
# Find Account
a = re.search(r"(?:Acct|Account)[:#\s]+(\d{5,15})", text, re.IGNORECASE)
if a: acct = a.group(1)
except: pass
return amt, last4, acct


if "auth" not in st.session_state:
st.title("🔒 Accounting Login")
u = st.text_input("Username")
p = st.text_input("Password", type="password")
if st.button("Login"):
if u in USER_DB and USER_DB[u] == p:
st.session_state.update({"auth": True, "user": u})
st.rerun()
st.stop()

st.title("📚 Corporate Bookkeeping & Tracker")

t1, t2, t3 = st.tabs(["📝 Journal Entry", "📈 P&L Dashboard", "🗃️ General Ledger"])


with t1:
if 'scan_amt' not in st.session_state:
st.session_state.update({'scan_amt': 0.0, 'scan_l4': "", 'scan_acc': ""})

files = st.file_uploader("Upload Documents", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
if files and st.button("🔍 Scan Documents"):
    amt, l4, acc = scan_images(files)
    st.session_state.update({'scan_amt': amt, 'scan_l4': l4, 'scan_acc': acc})
    st.success("Scan Complete")

st.markdown("---")

with st.form("entry_form"):
    st.subheader("Transaction Details")
    
    # Money In or Money Out?
    txn_type = st.radio("Nature of Transaction", ["Expense (Money Out)", "Income (Money In)"], horizontal=True)
    
    c1, c2 = st.columns(2)
    doc_type = c1.selectbox("Document Type", ["Receipt", "Invoice", "Statement"])
    status = c2.selectbox("Payment Status", ["Paid", "Unpaid / Pending", "Overdue"])
    
    c3, c4 = st.columns(2)
    v_date = c3.date_input("Transaction Date", date.today())
    
    # Label changes based on context
    if "Expense" in txn_type:
        entity_label = "Vendor (Who did we pay?)"
    else:
        entity_label = "Customer (Who paid us?)"
    entity = c4.text_input(entity_label)
    
    acc_num = st.text_input("Invoice/Account #", value=st.session_state['scan_acc'])

    st.markdown("### Financials")
    c5, c6, c7 = st.columns(3)
    amount = c5.number_
