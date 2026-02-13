import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import re
from datetime import date
import plotly.express as px

# --- DATA HANDLING ---
DATA_FILE = "company_receipts.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["Date", "Employee", "Vendor", "Amount", "Category"])

# --- UI SETUP ---
st.set_page_config(page_title="Corporate Expense Tracker", layout="wide")
st.title("📂 Business Receipt & Invoice Manager")

tab1, tab2 = st.tabs(["📥 Data Entry", "📊 Reports & Analytics"])

with tab1:
    st.header("New Entry")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload Receipt/Invoice", type=['jpg', 'png', 'jpeg'])
        auto_amount = 0.0
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.image(img, caption="Preview", width=400)
            if st.button("✨ Auto-Fill from Image"):
                # Simple OCR Logic
                raw_text = pytesseract.image_to_string(img)
                prices = re.findall(r"\d+\.\d{2}", raw_text)
                if prices:
                    auto_amount = float(max(prices))
                    st.success(f"Detected: ${auto_amount}")

    with col2:
        with st.form("entry_form", clear_on_submit=True):
            emp = st.text_input("Employee Name")
            vend = st.text_input("Vendor")
            amt = st.number_input("Amount ($)", value=auto_amount, step=0.01)
            dt = st.date_input("Date", date.today())
            cat = st.selectbox("Category", ["Office Supplies", "Software", "Travel", "Meals", "Maintenance"])
            
            if st.form_submit_button("Submit to Records"):
                if emp and vend:
                    df = load_data()
                    new_data = pd.DataFrame([[dt, emp, vend, amt, cat]], columns=df.columns)
                    pd.concat([df, new_data]).to_csv(DATA_FILE, index=False)
                    st.toast("Record Saved!", icon="✅")

with tab2:
    st.header("Company Spending Report")
    df = load_data()

    if not df.empty:
        # Filters
        c1, c2, c3 = st.columns(3)
        with c1:
            start_date = st.date_input("From", value=date(2024, 1, 1))
        with c2:
            end_date = st.date_input("To", value=date.today())
        with c3:
            query = st.text_input("Search Employee/Vendor")

        # Filtering Logic
        filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        if query:
            filtered = filtered[filtered['Employee'].str.contains(query, case=False) | 
                                filtered['Vendor'].str.contains(query, case=False)]

        # Dashboard Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Spend", f"${filtered['Amount'].sum():,.2f}")
        m2.metric("Total Invoices", len(filtered))
        m3.metric("Avg. Invoice", f"${filtered['Amount'].mean():,.2f}" if len(filtered)>0 else "$0")

        # Visuals
        st.markdown("---")
        chart_col, table_col = st.columns([1, 1])
        
        with chart_col:
            st.subheader("Spending by Category")
            fig = px.pie(filtered, values='Amount', names='Category', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

        with table_col:
            st.subheader("Filtered Records")
            st.dataframe(filtered, use_container_width=True, hide_index=True)

        # Export Actions
        st.download_button("📥 Export to CSV", data=filtered.to_csv(index=False), file_name="report.csv")
    else:
        st.info("No data available yet. Please add a receipt in the first tab.")
