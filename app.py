import streamlit as st
import pandas as pd
from datetime import date
import re
from PIL import Image
import pytesseract
import os
import smtplib
from email.message import EmailMessage

--- EMAIL SETTINGS ---
Update these with your real info
MY_EMAIL = "smiles4j41@gmail.com"
MY_PASSWORD = "kpnq ccpd ekrf stpo"
RECEIVER_EMAIL = "smiles4j41@gmail.com"

--- CONFIGURATION ---
USER_DB = {"admin": "admin123", "staff": "staff123"}
st.set_page_config(page_title="Bookkeeping Ledger", layout="wide")
DATA_FILE = "accounting_data.csv"

--- DATA FUNCTIONS ---
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

--- LOGIN SCREEN ---
if "auth" not in st.session_state:
st.title("🔒 Accounting Login")
u = st.text_input("Username")
p = st.text_input("Password", type="password")
if st.button("Login"):
if u in USER_DB and USER_DB[u] == p:
st.session_state.update({"auth": True, "user": u})
st.rerun()
st.stop()

--- MAIN APP ---
st.title("📚 Corporate Bookkeeping & Tracker")

t1, t2, t3 = st.tabs(["📝 Journal Entry", "📈 P&L Dashboard", "🗃️ General Ledger"])

--- TAB 1: DATA ENTRY ---
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
    amount = c5.number_input("Amount ($)", value=st.session_state['scan_amt'], min_value=0.0)
    pay_m = c6.selectbox("Method", ["Business Card", "Cash", "Check", "EFT/Wire", "Credit"])
    
    if pay_m == "Business Card":
        l4_digits = c7.text_input("Last 4 Digits", value=st.session_state['scan_l4'])
    else:
        l4_digits = "N/A"
    
    # Dynamic Categories
    if "Expense" in txn_type:
        cat_list = ["Operational", "COGS", "Payroll", "Marketing", "Utilities", "Travel", "Maintenance", "Tax", "Other"]
    else:
        cat_list = ["Sales Revenue", "Service Income", "Refund/Credit", "Interest", "Other"]
        
    category = st.selectbox("Chart of Accounts (Category)", cat_list)
    details = st.text_area("Memo / Description")
    
    if st.form_submit_button("Post to Ledger"):
        final_type = "Expense" if "Expense" in txn_type else "Income"
        
        df = load_data()
        new_row = pd.DataFrame([[
            v_date, final_type, doc_type, status, acc_num, 
            st.session_state['user'], entity, amount, pay_m, 
            l4_digits, category, details
        ]], columns=df.columns)
        
        # Save locally
        if os.path.exists(DATA_FILE):
            new_row.to_csv(DATA_FILE, mode='a', header=False, index=False)
        else:
            new_row.to_csv(DATA_FILE, index=False)
        
        st.success("✅ Transaction Posted Successfully!")
        
        # Email Alert Logic (Only for Unpaid Invoices)
        if doc_type == "Invoice" and status == "Unpaid / Pending":
            try:
                msg = EmailMessage()
                msg.set_content(f"New Unpaid Invoice Logged:\n\nEntity: {entity}\nAmount: ${amount}\nDue Date: {v_date}")
                msg['Subject'] = "Action Required: Unpaid Invoice"
                msg['From'] = MY_EMAIL
                msg['To'] = RECEIVER_EMAIL
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                    s.login(MY_EMAIL, MY_PASSWORD)
                    s.send_message(msg)
            except: pass
--- TAB 2: FINANCIAL DASHBOARD ---
with t2:
st.header("Financial Snapshot")
df = load_data()

if not df.empty:
    # Calculate Totals
    income_df = df[df['Txn_Type'] == 'Income']
    expense_df = df[df['Txn_Type'] == 'Expense']
    
    total_income = income_df['Amount'].sum()
    total_expense = expense_df['Amount'].sum()
    net_profit = total_income - total_expense
    
    # Display Metrics
    colA, colB, colC = st.columns(3)
    colA.metric("Total Revenue", f"${total_income:,.2f}")
    colB.metric("Total Expenses", f"${total_expense:,.2f}")
    colC.metric("Net Profit", f"${net_profit:,.2f}")
    
    st.markdown("---")
    
    # Outstanding Bills
    st.subheader("⚠️ Unpaid Bills")
    unpaid = df[(df['Status'] == 'Unpaid / Pending') & (df['Txn_Type'] == 'Expense')]
    if not unpaid.empty:
        st.dataframe(unpaid[['Date', 'Entity', 'Amount', 'Account_Num']], use_container_width=True)
    else:
        st.info("No outstanding bills.")

else:
    st.info("No transactions found.")
--- TAB 3: GENERAL LEDGER ---
with t3:
st.header("General Ledger")
df = load_data()
if not df.empty:
st.dataframe(df, use_container_width=True)
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Ledger", data=csv, file_name="accounting_ledger.csv", mime="text/csv")
else:
st.info("Ledger is empty.")
