import sqlite3
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="wide")
DB_NAME = "expense_tracker.db"

st.markdown("""
<style>
.stApp{background:#f4f8fc}.block-container{padding-top:1.5rem;max-width:1450px}
h1,h2,h3{color:#102744}
.hero{background:linear-gradient(110deg,#0b2545,#087e8b);padding:25px 28px;border-radius:18px;color:white;margin-bottom:20px}
.hero h1{color:white;margin:0;font-size:32px}.hero p{color:#d9f4f5;margin:7px 0 0;font-size:16px}
div[data-testid="stMetric"]{background:white;border:1px solid #e2eaf3;padding:17px;border-radius:15px;box-shadow:0 4px 14px #1432500d}
div[data-testid="stMetricLabel"]{color:#58708c}div[data-testid="stMetricValue"]{color:#102744}
div[data-testid="stForm"]{background:white;border:1px solid #dce8f3;padding:20px;border-radius:16px}
.stButton button,.stFormSubmitButton button{background:linear-gradient(90deg,#08a878,#0797a7);color:white;border:0;border-radius:10px;font-weight:600}
.stButton button:hover,.stFormSubmitButton button:hover{color:white;background:#087e8b}
section[data-testid="stSidebar"]{background:#0b1d35}section[data-testid="stSidebar"] *{color:#f4f8fc}
</style>""", unsafe_allow_html=True)

def connect_db():
    return sqlite3.connect(DB_NAME)

def create_table():
    with connect_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_date TEXT NOT NULL,
            transaction_type TEXT NOT NULL, category TEXT NOT NULL,
            amount REAL NOT NULL, description TEXT)""")
        conn.commit()

def add_transaction(tx_date, tx_type, category, amount, description):
    with connect_db() as conn:
        conn.execute("INSERT INTO transactions (transaction_date, transaction_type, category, amount, description) VALUES (?, ?, ?, ?, ?)",
                     (tx_date.isoformat(), tx_type, category, amount, description.strip()))
        conn.commit()

def get_transactions():
    with connect_db() as conn:
        return pd.read_sql_query("SELECT * FROM transactions ORDER BY transaction_date DESC, id DESC", conn)

def delete_transaction(tx_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (int(tx_id),))
        conn.commit()

create_table()
with st.sidebar:
    st.markdown("## 💰 MoneyMate")
    st.caption("PERSONAL FINANCE")
    page = st.radio("Navigation", ["Dashboard", "Add Transaction", "View Transactions", "Expense Chart"], label_visibility="collapsed")
    st.divider()
    st.markdown("### 🌱 Smart money tip")
    st.write("Small steps today can build better saving habits tomorrow.")
    st.caption("Student project • Python + SQLite")

st.markdown("""<div class="hero"><h1>👋 Welcome to your Expense Tracker</h1>
<p>Track your income, control your spending, and work towards your financial goals.</p></div>""", unsafe_allow_html=True)
df = get_transactions()
if not df.empty:
    df["month"] = df["transaction_date"].str[:7]
income = float(df.loc[df.transaction_type == "Income", "amount"].sum()) if not df.empty else 0
expenses = float(df.loc[df.transaction_type == "Expense", "amount"].sum()) if not df.empty else 0
balance = income - expenses
this_month = date.today().strftime("%Y-%m")
month_df = df[df["month"] == this_month] if not df.empty else df
month_expenses = float(month_df.loc[month_df.transaction_type == "Expense", "amount"].sum()) if not month_df.empty else 0

if page == "Dashboard":
    st.subheader("📊 Your financial overview")
    a,b,c,d = st.columns(4)
    a.metric("💚 Total Income", f"₹{income:,.2f}")
    b.metric("❤️ Total Expenses", f"₹{expenses:,.2f}")
    c.metric("💙 Remaining Balance", f"₹{balance:,.2f}")
    d.metric("💜 This Month's Expenses", f"₹{month_expenses:,.2f}")
    left,right = st.columns([1.3,1])
    with left:
        st.subheader("🧾 Recent transactions")
        if df.empty:
            st.info("No transactions yet. Choose Add Transaction from the sidebar to get started.")
        else:
            recent = df[["transaction_date","transaction_type","category","amount","description"]].head(6).copy()
            recent.columns = ["Date","Type","Category","Amount (₹)","Description"]
            st.dataframe(recent, use_container_width=True, hide_index=True)
    with right:
        st.subheader("🍩 Where your money goes")
        chart = df[df.transaction_type == "Expense"].groupby("category", as_index=False)["amount"].sum() if not df.empty else pd.DataFrame()
        if chart.empty:
            st.info("Your expense chart will appear after you add an expense.")
        else:
            fig = px.pie(chart, names="category", values="amount", hole=.58, color_discrete_sequence=["#08a878","#168aad","#ffb703","#ef476f","#7b61ff","#06b6d4"])
            fig.update_layout(margin=dict(t=10,b=10,l=5,r=5), legend_title_text="", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    st.caption("💡 Tip: Enter each transaction to keep your balance and chart up to date.")

elif page == "Add Transaction":
    st.subheader("➕ Add a new transaction")
    st.write("Enter the details below.")
    with st.form("transaction_form", clear_on_submit=True):
        c1,c2,c3 = st.columns(3)
        tx_date = c1.date_input("Date", value=date.today())
        tx_type = c2.selectbox("Transaction type", ["Expense","Income"])
        categories = ["Salary","Allowance","Scholarship","Gift","Other income"] if tx_type == "Income" else ["Food","Travel","Shopping","Bills","Education","Health","Entertainment","Other expense"]
        category = c3.selectbox("Category", categories)
        c4,c5 = st.columns(2)
        amount = c4.number_input("Amount (₹)", min_value=0.0, step=50.0, format="%.2f")
        description = c5.text_input("Description (optional)", placeholder="e.g. Lunch, bus fare, books")
        save = st.form_submit_button("💾 Save Transaction")
        if save:
            if amount <= 0:
                st.error("Please enter an amount greater than ₹0.")
            else:
                add_transaction(tx_date, tx_type, category, amount, description)
                st.success("Transaction saved successfully!")
                st.rerun()

elif page == "View Transactions":
    st.subheader("📚 All transactions")
    if df.empty:
        st.info("No transactions available yet. Add one from the sidebar.")
    else:
        months = ["All months"] + sorted(df["month"].unique(), reverse=True)
        chosen_month = st.selectbox("Filter by month", months)
        shown = df if chosen_month == "All months" else df[df["month"] == chosen_month]
        shown = shown[["id","transaction_date","transaction_type","category","amount","description"]].copy()
        shown.columns = ["ID","Date","Type","Category","Amount (₹)","Description"]
        st.dataframe(shown, use_container_width=True, hide_index=True)
        st.subheader("🗑️ Delete a transaction")
        labels = {f"ID {r.id} | {r.transaction_date} | {r.category} | ₹{r.amount:,.2f}": int(r.id) for r in df.itertuples(index=False)}
        chosen = st.selectbox("Choose a record", list(labels.keys()))
        confirm = st.checkbox("I want to delete this transaction.")
        if st.button("Delete selected transaction", disabled=not confirm):
            delete_transaction(labels[chosen])
            st.success("Transaction deleted.")
            st.rerun()

elif page == "Expense Chart":
    st.subheader("📈 Expense analysis")
    if df.empty or not (df.transaction_type == "Expense").any():
        st.info("Add some expense transactions to see your chart.")
    else:
        months = ["All months"] + sorted(df["month"].unique(), reverse=True)
        chosen_month = st.selectbox("Select month", months)
        chart_df = df[df.transaction_type == "Expense"]
        if chosen_month != "All months":
            chart_df = chart_df[chart_df["month"] == chosen_month]
        chart = chart_df.groupby("category", as_index=False)["amount"].sum()
        if chart.empty:
            st.info("No expenses found for this period.")
        else:
            fig = px.bar(chart, x="category", y="amount", color="category", title="Total expenses by category", color_discrete_sequence=["#08a878","#168aad","#ffb703","#ef476f","#7b61ff","#06b6d4"])
            fig.update_layout(showlegend=False, xaxis_title="Category", yaxis_title="Amount (₹)", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"**Total expenses: ₹{float(chart_df.amount.sum()):,.2f}**")

st.divider()
st.caption("Made with Python • Streamlit • SQLite • Pandas • Plotly")
