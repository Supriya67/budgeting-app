import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import plotly.express as px
import bcrypt

# connect to DB
conn = sqlite3.connect('budget.db',check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

def signup():
    st.subheader("🔐 Create New Account")
    new_user = st.text_input("Username", key="signup_username")
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type='password', key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if new_password != confirm_password:
            st.warning("Passwords do not match.")
        elif not new_user or not new_password:
            st.warning("Username and password cannot be empty.")
        else:
            # Check if user already exists
            cur.execute("SELECT * FROM users WHERE username=?", (new_user,))
            if cur.fetchone():
                st.error("Username already exists. Try another.")
            else:
                # Hash password and store
                hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
                cur.execute("INSERT INTO users (username,email, password) VALUES (?, ?, ?)", (new_user,new_email, hashed_pw))
                conn.commit()
                st.success("Account created! Please log in.")
    if st.button("Login"):
        # Set page to login and rerun the app
        st.session_state['page'] = "Login"
        st.rerun()
#function to verify user login credential
def login():
    st.subheader("🔑 Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type='password', key="login_password")
    if st.button("Login"):
        cur.execute("SELECT id, password FROM users WHERE username=?", (username,))
        result = cur.fetchone()

        if result and bcrypt.checkpw(password.encode(), result[1]):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Welcome back, {username}!")
            st.session_state['user_id'] = result[0]  # or however you're storing it
            st.session_state['page'] = "Dashboard"  # ⬅ Force switch
            st.rerun()
        else:
            st.error("Invalid username or password.")
    if st.button("Sign Up"):
        st.session_state['page'] = "Sign Up"
        st.rerun()

def logout():
    if st.sidebar.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.session_state["user_id"] = None
        st.session_state["page"] = "Login"  # Redirect to Login page
        st.rerun()

def get_categories():
    cur.execute("SELECT name FROM categories ORDER BY name")
    rows = cur.fetchall()
    return [row[0] for row in rows]

def add_categories(name):
    try:
        cur.execute("INSERT INTO categories (name) VALUES (?)",(name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


#add income or expenses in tranaction table    
def add_transaction(user_id, t_type, category, amount, t_date, t_desc):
    cur.execute(''' 
                INSERT INTO transactions (user_id, type, category, amount, date, description)
                VALUES (?, ?, ?, ?, ?, ?)
    ''' ,(user_id, t_type, category, amount, t_date, t_desc) )
    conn.commit() 

def delete_transaction(user_id, transaction_id):
    query = "DELETE FROM transactions WHERE id = ? AND user_id = ?"
    cur.execute(query, (transaction_id, user_id))
    conn.commit()

# to get users transaction
def get_user_transactions(user_id):
    cur.execute('SELECT id, type, category, amount, date, description FROM transactions WHERE user_id = ?',(user_id,))
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=['ID', 'Type', 'Category' , 'Amount', 'Date' , 'Description'])

def fetch_filtered_transactions(user_id, from_date, to_date):
    df = get_user_transactions(user_id)
    df['Date'] = pd.to_datetime(df['Date'])
    return df[(df['Date'] >= pd.to_datetime(from_date)) & (df['Date'] <= pd.to_datetime(to_date))]

def dashboard():

    # Add Transaction
    categories = get_categories()
    categories.append("Add new category ...")
    category = st.selectbox("Category", categories)
    if category == "Add new category ...":
            new_category = st.text_input("New category name")
            if st.button("Add Category"):
                if new_category.strip() == "":
                    st.error("Category name cannot be empty")
                else:
                    success = add_categories(new_category.strip())
                    if success:
                        st.success(f"Category '{new_category.strip()}' added!")
                        st.rerun()
                    else:
                        st.error("Category already exists")
    else:
        # Show the rest of the transaction form only if category is valid
        with st.form("transaction_form"):
            t_type = st.radio("Type", ['income','expense'], horizontal=True)
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            with col2:
                t_date = st.date_input("Date", value=date.today())
            t_desc = st.text_area("Description (optional)")

            submitted = st.form_submit_button("Add Transaction")

            if submitted:
                add_transaction(st.session_state['user_id'], t_type, category, amount, str(t_date), t_desc)
                st.success("Transaction added!")
    
    

    # Filter and Show Transactions
    st.write("### Filter by Date Range")

    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", value=date.today())
    with col2:
        to_date = st.date_input("To date", value=date.today())

    if from_date > to_date:
        st.error(" 'From Date' cannot be greater than 'To date'")
    else:
        df = get_user_transactions(st.session_state['user_id'])
        df['Date'] = pd.to_datetime(df['Date'])
        filtered_df = df[(df['Date'] >= pd.to_datetime(from_date)) & (df['Date'] <= pd.to_datetime(to_date))]
        
        st.write("### Your Transaction")
        st.dataframe(filtered_df)

        if not filtered_df.empty:
            
            total_income = filtered_df[filtered_df['Type'] == 'income']['Amount'].sum()
            total_expense = filtered_df[filtered_df['Type'] == 'expense']['Amount'].sum()
            balance = total_income - total_expense

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Income", f"${total_income:.2f}")
            with col2:
                st.metric("💸 Expense", f"${total_expense:.2f}")
            with col3:
                st.metric("📉 Balance", f"${balance:.2f}")

            st.write("### 📊 Metrics by Category")
            # Create horizontal tabs
            selected_tab = st.radio("Select View", ["Income", "Expense"], horizontal=True)
            if selected_tab == "Income":
                income_df = filtered_df[filtered_df["Type"] == "income"]
                if not income_df.empty:
                    income_grouped = income_df.groupby("Category")["Amount"].sum()
                    for cat, val in income_grouped.items():
                        st.metric(label=cat, value=f"${val:.2f}")
                else:
                    st.info("No income data available.")

            elif selected_tab == "Expense":
                expense_df = filtered_df[filtered_df["Type"] == "expense"]
                if not expense_df.empty:
                    expense_grouped = expense_df.groupby("Category")["Amount"].sum()
                    for cat, val in expense_grouped.items():
                        st.metric(label=cat, value=f"${val:.2f}")
                else:
                    st.info("No expense data available.")



            # Expense Bar Chart
            expense_data = filtered_df[filtered_df['Type'] == 'expense']
            if not expense_data.empty:
                expense_by_category = expense_data.groupby('Category')['Amount'].sum().reset_index()
                
                st.write("### Expense by Category - Interactive Bar Chart")
                fig = px.bar(expense_by_category, 
                            x='Category', 
                            y='Amount', 
                            color='Amount',
                            color_continuous_scale='Reds',
                            labels={'Amount': 'Amount ($)', 'Category': 'Category'},
                            title='Expenses by Category')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No expenses to show in graph.")

            # 🥧 Pie Charts for Category Breakdown
            st.write("### 🥧 Category Breakdown by Type")

            col1, col2 = st.columns(2)
            with col1:
                expense_pie = filtered_df[filtered_df['Type'] == 'expense'].groupby('Category')['Amount'].sum().reset_index()
                if not expense_pie.empty:
                    fig_expense = px.pie(
                        expense_pie,
                        names='Category',
                        values='Amount',
                        title='Expense Distribution',
                        color_discrete_sequence=px.colors.sequential.Reds
                    )
                    st.plotly_chart(fig_expense, use_container_width=True)
                else:
                    st.info("No expense data to show.")

            with col2:
                income_pie = filtered_df[filtered_df['Type'] == 'income'].groupby('Category')['Amount'].sum().reset_index()
                if not income_pie.empty:
                    fig_income = px.pie(
                        income_pie,
                        names='Category',
                        values='Amount',
                        title='Income Distribution',
                        color_discrete_sequence=px.colors.sequential.Greens
                    )
                    st.plotly_chart(fig_income, use_container_width=True)
                else:
                    st.info("No income data to show.")

            # Delete Transaction
            st.write("### Delete a Transaction")
            if not filtered_df.empty:
                # Generate options with transaction ID embedded
                options = {
                    f"{row['Date'].date()} | {row['Category']} | ${row['Amount']:.2f} | {row['Description']}": row['ID']
                    for _, row in filtered_df.iterrows()
                }

                selected_label = st.selectbox("Select transaction to delete", list(options.keys()))
                selected_id = options[selected_label]

                if st.button("Delete selected transaction"):
                    user_id = st.session_state['user_id']
                    # Confirm the transaction exists before deleting
                    cur.execute("SELECT id FROM transactions WHERE id = ? AND user_id = ?", (selected_id, user_id))
                    record = cur.fetchone()
                    if record:
                        delete_transaction(user_id, selected_id)
                        st.success("✅ Transaction deleted!")
                        st.rerun()
                    else:
                        st.error("❌ Transaction not found or doesn't belong to this user.")
            else:
                st.info("No transactions available for deletion.")

        else:
            st.info("No transactions found in the selected date range.")
    

    

# Streamlit app UI
st.title("PocketGaurd - Budgeting Made Easy")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None

# Sidebar Navigation
if 'page' not in st.session_state:
    st.session_state['page'] = "Login"  # default page

st.session_state['page'] = st.sidebar.selectbox("📁 Navigation", ["Login", "Sign Up", "Dashboard"], 
                                                index=["Login", "Sign Up", "Dashboard"].index(st.session_state['page']))
page = st.session_state['page']

if page == "Sign Up":
    signup()
elif page == "Login":
    login()
elif page == "Dashboard":
    if st.session_state["logged_in"]:
        logout()
        st.write(f"### Welcome, {st.session_state['username']}!")
        dashboard()  # Your main budgeting app content
    else:
        st.warning("🔒 Please log in to access the dashboard.")
        col1,col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                st.session_state['page'] = "Login"
                st.rerun()
        with col2:
            if st.button("Sign Up"):
                st.session_state['page'] = "Sign Up"
                st.rerun()
        