import streamlit as st
import pandas as pd
from datetime import date
import re
from PIL import Image
import pytesseract

# --- LOGIN LIST ---
USER_DB = {"admin": "admin123", "staff": "staff123"}

# --- CONFIG & DATA ---
st.set_page_config(page_title="Smart Expense Tracker", layout="wide")
DATA_FILE = "company_data.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        return df
    except:
        return pd.DataFrame(columns=[
            "Date", "Type", "Account_Num", "Employee", "Vendor", 
            "Amount", "Payment_Method", "Card_Last4", "Category", 
            "Details", "Photo_Status"
        ])

# --- OCR LOGIC ---
def scan_image(image):
    text = pytesseract.image_to_string(image)
    amounts = re.findall(r"\d+\.\d{2}", text)
    found_amount = float(max(amounts)) if amounts else 0.0
    card_pattern = re.search(r"(?:\*{4}|Ending in|Account|#)\s*(\d{4})", text, re.IGNORECASE)
    found_last4 = card_pattern.group(1) if card_pattern else ""
    acct_pattern = re.search(r"(?:Acct|Account|Cust|ID)[:#\s]+(\d{5,15})", text, re.IGNORECASE)
    found_acct = acct_pattern.group(1) if acct_pattern else ""
    return found_amount, found_last4, found_acct

# --- AUTHENTICATION ---
if "authenticated" not in st.session_state:
    st.title("🔒 Login Required")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user in USER_DB and USER_DB[user] == pwd:
            st.session_state["authenticated"] = True
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# --- MAIN APP ---
st.sidebar.write(f"User: **{st.session_state['user']}**")
if st.sidebar.button("Logout"):
    del st.session_state["authenticated"]
    st.rerun()

st.title("🧾 Company Expense Manager")
tab1, tab2, tab3 = st.tabs(["📸 Add Entry", "📊 Reports", "🛠️ Manage Records"])

with tab1:
    st.header("Step 1: Scan Photo")
    if 'auto_amount' not in st.session_state: st.session_state['auto_amount'] = 0.0
    if 'auto_last4' not in st.session_state: st.session_state['auto_last4'] = ""
    if 'auto_acct' not in st.session_state: st.session_state['auto_acct'] = ""

    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    if uploaded_file and st.button("🔍 Auto-Scan"):
        amt, last4, acct = scan_image(Image.open(uploaded_file))
        st.session_state.update({'auto_amount': amt, 'auto_last4': last4, 'auto_acct': acct})
        st.success("Scan Complete!")

    st.markdown("---")
    with st.form("entry_form"):
        doc_type = st.radio("Type", ["Receipt", "Invoice"], horizontal=True)
        acc_num = st.text_input("Account #", value=st.session_state['auto_acct'])
        colA, colB = st.columns(2)
        v_date = colA.date_input("Date", date.today())
        vendor = colB.text_input("Vendor")
        colC, colD, colE = st.columns(3)
        amt = colC.number_input("Amount", value=st.session_state['auto_amount'])
        pay_m = colD.selectbox("Payment", ["Card", "Cash", "Check", "EFT"])
        c_last4 = colE.text_input("Card Last 4", value=st.session_state['auto_last4'], max_chars=4)
        cat = st.selectbox("Category", ["Admin", "Cleaning/Maint.", "Travel", "Catering", "Vendor", "Marketing", "Franchise", "Other"])
        details = st.text_area("Details")
        no_p = st.checkbox("NO PHOTO AVAILABLE")
        
        if st.form_submit_button("Save"):
            if not uploaded_file and not no_p: st.error("Photo required")
            else:
                df = load_data()
                new_row = pd.DataFrame([[v_date.strftime('%m/%d/%Y'), doc_type, acc_num, st.session_state['user'], vendor, amt, pay_m, c_last4, cat, details, "Yes"]], columns=df.columns)
                pd.concat([df, new_row], ignore_index=True).to_csv(DATA_FILE, index=False)
                st.success("Saved!")

with tab2:
    st.header("Summary")
    df = load_data()
    st.dataframe(df, use_container_width=True)
    st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name="expenses.csv")

with tab3:
    st.header("Modify or Delete Entries")
    df = load_data()
    if not df.empty:
        # Create a list of labels for the dropdown to pick which row to edit
        df_display = df.copy()
        df_display['Label'] = df.index.astype(str) + ": " + df['Vendor'] + " ($" + df['Amount'].astype(str) + ")"
        selected_label = st.selectbox("Select Record to Edit/Delete", df_display['Label'])
        index_to_act = int(selected_label.split(":")[0])
        
        row = df.iloc[index_to_act]
        
        with st.expander("Edit Selected Record"):
            new_vendor = st.text_input("Edit Vendor", value=row['Vendor'])
            new_amt = st.number_input("Edit Amount", value=float(row['Amount']))
            new_cat = st.selectbox("Edit Category", ["Admin", "Cleaning/Maint.", "Travel", "Catering", "Vendor", "Marketing", "Franchise", "Other"], index=["Admin", "Cleaning/Maint.", "Travel", "Catering", "Vendor", "Marketing", "Franchise", "Other"].index(row['Category']))
            
            if st.button("Update Record"):
                df.at[index_to_act, 'Vendor'] = new_vendor
                df.at[index_to_act, 'Amount'] = new_amt
                df.at[index_to_act, 'Category'] = new_cat
                df.to_csv(DATA_FILE, index=False)
                st.success("Updated!")
                st.rerun()

        if st.button("🗑️ Delete This Record", help="This cannot be undone!"):
            df = df.drop(index_to_act)
            df.to_csv(DATA_FILE, index=False)
            st.warning("Deleted!")
            st.rerun()
    else:
        st.info("No data to manage.")
