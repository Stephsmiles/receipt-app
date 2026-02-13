import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

# --- LOGIN LIST (Username : Password) ---
USER_DB = {
    "admin": "admin123",
    "staff": "staff123"
}

# --- APP SETUP ---
st.set_page_config(page_title="Receipt Tracker", layout="wide")
DATA_FILE = "receipts.csv"

def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except:
        return pd.DataFrame(columns=["Date", "Employee", "Vendor", "Amount", "Category"])

# --- LOGIN SCREEN ---
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
            st.error("Wrong password")
    st.stop() # Stops the rest of the app from loading

# --- MAIN APP (Only shows if logged in) ---
st.sidebar.write(f"User: {st.session_state['user']}")
if st.sidebar.button("Logout"):
    del st.session_state["authenticated"]
    st.rerun()

st.title("🧾 Business Receipt Tracker")

tab1, tab2 = st.tabs(["📝 Add Receipt", "📊 View Reports"])

# TAB 1: ADD RECEIPT
with tab1:
    st.header("Enter New Receipt")
    with st.form("receipt_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_input = st.date_input("Date", date.today())
            vendor = st.text_input("Vendor (e.g., Walmart)")
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.0, step=0.01)
            category = st.selectbox("Category", ["Supplies", "Travel", "Meals", "Other"])
        
        # Taking a photo (Mobile feature)
        uploaded_file = st.file_uploader("Attach Photo (Optional)", type=['png', 'jpg'])

        if st.form_submit_button("Save Receipt"):
            df = load_data()
            new_entry = pd.DataFrame([[date_input, st.session_state['user'], vendor, amount, category]], 
                                     columns=["Date", "Employee", "Vendor", "Amount", "Category"])
            # Save to file
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            updated_df.to_csv(DATA_FILE, index=False)
            st.success("Saved!")

# TAB 2: REPORTS
with tab2:
    st.header("Search & Reports")
    df = load_data()
    
    if not df.empty:
        search = st.text_input("Search (Vendor or Employee)")
        if search:
            df = df[df['Vendor'].str.contains(search, case=False) | df['Employee'].str.contains(search, case=False)]
        
        st.dataframe(df, use_container_width=True)
        st.metric("Total Spent", f"${df['Amount'].sum():,.2f}")
        
        # Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Excel/CSV", data=csv, file_name="receipts.csv")
    else:
        st.info("No receipts entered yet.")
