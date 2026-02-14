    import streamlit as st
import pandas as pd
from datetime import date
import re
from PIL import Image
import pytesseract
import os
import smtplib
from email.message import EmailMessage
import streamlit.components.v1 as components

# --- EMAIL SETTINGS ---
# Update these with your real info
MY_EMAIL = "smiles4j41@gmail.com"
MY_PASSWORD = "kpnq ccpd ekrf stpo"
RECEIVER_EMAIL = "smiles4j41@gmail.com"

# --- CONFIGURATION ---
USER_DB = {"admin": "admin123", "staff": "staff123"}
st.set_page_config(page_title="Bookkeeping Ledger", layout="wide")
DATA_FILE = "accounting_data.csv"

# --- DATA FUNCTIONS ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "Date", "Txn_Type", "Doc_Type", "Status", "Account_Num", 
        "Employee", "Entity", "Sub_Total", "Tax", "Fees", "Amount", 
        "Payment_Method", "Last4", "Category", "Details"
    ])

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
    st.title("🔒 Accounting Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state.update({"auth": True, "user": u})
            st.rerun()
    st.stop()

# --- MAIN APP ---
st.title("📚 Corporate Bookkeeping & Tracker")

t1, t2, t3 = st.tabs(["📝 Journal Entry", "📈 P&L Dashboard", "🗃️ General Ledger & Reports"])

# --- TAB 1: DATA ENTRY ---
with t1:
    if 'scan_amt' not in st.session_state:
        st.session_state.update({'scan_amt': 0.0, 'scan_l4': "", 'scan_acc': ""})

    # --- UPLOAD SECTION WITH CAMERA OPTION ---
    st.subheader("1. Document Upload")
    
    # 1. File Uploader
    files = st.file_uploader("Upload Files", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    # 2. Camera Input (Optional)
    enable_cam = st.checkbox("📸 Use Camera to Scan")
    cam_image = None
    if enable_cam:
        cam_image = st.camera_input("Take a Picture")

    # Combine images for scanning
    images_to_scan = []
    if files:
        images_to_scan.extend(files)
    if cam_image:
        images_to_scan.append(cam_image)

    if images_to_scan and st.button("🔍 Scan Documents"):
        amt, l4, acc = scan_images(images_to_scan)
        st.session_state.update({'scan_amt': amt, 'scan_l4': l4, 'scan_acc': acc})
        st.success("Scan Complete")

    st.markdown("---")
    
    with st.form("entry_form"):
        st.subheader("2. Transaction Details")
        
        # Money In or Money Out?
        txn_type = st.radio("Nature of Transaction", ["Expense (Money Out)", "Income (Money In)"], horizontal=True)
        
        c1, c2 = st.columns(2)
        # CHANGED: Dropdown to Oval Buttons (Radio horizontal)
        doc_type = c1.radio("Document Type", ["Receipt", "Invoice", "Statement"], horizontal=True)
        status = c2.selectbox("Payment Status", ["Paid", "Unpaid / Pending", "Overdue"])
        
        c3, c4 = st.columns(2)
        # CHANGED: Date format to MM/DD/YYYY in display
        v_date = c3.date_input("Transaction Date", date.today(), format="MM/DD/YYYY")
        
        # Label changes based on context
        if "Expense" in txn_type:
            entity_label = "Vendor (Who did we pay?)"
        else:
            entity_label = "Customer (Who paid us?)"
        entity = c4.text_input(entity_label)
        
        acc_num = st.text_input("Invoice/Account #", value=st.session_state['scan_acc'])

        st.markdown("### 3. Financial Breakdown")
        # CHANGED: Added Sub-Total, Tax, Fees fields
        fc1, fc2, fc3 = st.columns(3)
        sub_total = fc1.number_input("Sub-Total ($)", value=st.session_state['scan_amt'], min_value=0.0)
        tax = fc2.number_input("Taxes Total ($)", min_value=0.0)
        fees = fc3.number_input("Fees Total ($)", min_value=0.0)
        
        # Auto-calculate Total
        total_amount = sub_total + tax + fees
        st.metric("Total Transaction Amount", f"${total_amount:,.2f}")

        c_pay, c_last4 = st.columns(2)
        pay_m = c_pay.selectbox("Method", ["Business Card", "Cash", "Check", "EFT/Wire", "Credit"])
        
        if pay_m == "Business Card":
            l4_digits = c_last4.text_input("Last 4 Digits", value=st.session_state['scan_l4'])
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
            # CHANGED: Date saved as string MM/DD/YYYY
            date_str = v_date.strftime('%m/%d/%Y')
            
            new_row = pd.DataFrame([[
                date_str, final_type, doc_type, status, acc_num, 
                st.session_state['user'], entity, sub_total, tax, fees, total_amount, pay_m, 
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
                    msg.set_content(f"New Unpaid Invoice Logged:\n\nEntity: {entity}\nTotal Amount: ${total_amount}\nDue Date: {date_str}")
                    msg['Subject'] = "Action Required: Unpaid Invoice"
                    msg['From'] = MY_EMAIL
                    msg['To'] = RECEIVER_EMAIL
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                        s.login(MY_EMAIL, MY_PASSWORD)
                        s.send_message(msg)
                except: pass

# --- TAB 2: FINANCIAL DASHBOARD ---
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

# --- TAB 3: GENERAL LEDGER & REPORTS ---
with t3:
    st.header("General Ledger & Reports")
    df = load_data()
    
    if not df.empty:
        # --- FILTERS ---
        with st.expander("🔎 Filter Reports", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            
            # Date Filter (Requires converting string dates back to datetime for filtering)
            df['Date_Obj'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
            
            start_d = f_col1.date_input("Start Date", value=date(2025, 1, 1), format="MM/DD/YYYY")
            end_d = f_col2.date_input("End Date", value=date.today(), format="MM/DD/YYYY")
            
            search_cat = f_col3.multiselect("Filter by Category", df['Category'].unique())
            
            # Apply Filters
            mask = (df['Date_Obj'].dt.date >= start_d) & (df['Date_Obj'].dt.date <= end_d)
            if search_cat:
                mask = mask & (df['Category'].isin(search_cat))
            
            filtered_df = df.loc[mask].drop(columns=['Date_Obj']) # Hide helper column
            
        st.markdown(f"### Report: {start_d.strftime('%m/%d/%Y')} to {end_d.strftime('%m/%d/%Y')}")
        st.dataframe(filtered_df, use_container_width=True)
        
        # --- EXPORT & PRINT ---
        c_exp, c_print = st.columns(2)
        
        # Export CSV
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        c_exp.download_button("📥 Download Report (CSV)", data=csv, file_name="ledger_report.csv", mime="text/csv")
        
        # Print Button (Generates a printable HTML page)
        if c_print.button("🖨️ Print View"):
            # Create a simple HTML table for printing
            html_table = filtered_df.to_html(index=False, classes='table table-striped', border=1)
            print_view = f"""
            <html>
            <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                @media print {{ .no-print {{ display: none; }} }}
            </style>
            </head>
            <body onload="window.print()">
                <h1>Bookkeeping Report</h1>
                <p>Generated on: {date.today().strftime('%m/%d/%Y')}</p>
                {html_table}
                <br>
                <button class="no-print" onclick="window.print()">Print Report</button>
            </body>
            </html>
            """
            # Inject HTML in a new window/iframe style or just render it
            components.html(print_view, height=600, scrolling=True)

    else:
        st.info("Ledger is empty.")
