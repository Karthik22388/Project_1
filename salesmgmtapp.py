import streamlit as st
import psycopg2
import hashlib 
import pandas as pd
import numpy as np

st.set_page_config(page_title="Sales Dashboard", layout="wide")

# --- User Session & Role Setup ---
user_role = st.session_state.get("role", "Admin")
username = st.session_state.get("username", "admin_chennai")
# If they are a regular admin, dynamically extract their branch name
if user_role == "Admin":
    # Splits "admin_chennai" by the underscore and capitalizes "chennai" -> "Chennai"
    user_branch = username.split("_")[-1].capitalize()
else:
    user_branch = "All"

#password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_connection():
    return psycopg2.connect(
        host = "localhost",
        port = 5432,
        database ="my_db",
        user ="postgres",
        password ="sairam"
    )

#Function to execute a query and return results as a DataFrame
def execute_query(query):
    conn = get_connection()
    df = pd.read_sql(query,conn)
    conn.close()
    return df


#Authentication
def authenticate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, password, role FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    conn.close()
    
     # Case 1: plain text password stored in DB (for testing)
    if user and user[1] == password: #plain text check
        return user[2]
    # Case 2: hashed password stored in DB
    elif user and user[1] == hash_password(password):    # hashed
        return user[2]
    return None

def insert_sales_record (sale_date, name, mobile_number, 
                        product_name, gross_sales, status, branch_name):
                        
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """
                INSERT INTO customer_sales (sale_date, name, mobile_number, product_name, 
                gross_sales, status, branch_name, branch_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 
                        (SELECT branch_id FROM branches WHERE branch_name = %s)
            );
        """    
        cur.execute(query,(sale_date, name, mobile_number, product_name, gross_sales,status,branch_name,branch_name))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def insert_payment_record (sale_id, payment_date, amount_paid, payment_method):                        
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """
                INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                VALUES (%s, %s, %s, %s);
        """    
        cur.execute(query,(sale_id, payment_date, amount_paid, payment_method))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

#Session State Initilization
if "logged_in" not in st.session_state:
    st.title("🏫 Education Institute Sales Analysis Dashboard")
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""    

if not st.session_state.logged_in:
    username = st.text_input("Username", width=300)
    password = st.text_input("Password", type = "password",width=300)

    if st.button("Login"):
        role = authenticate_user(username,password)
        if role: 
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role            
            st.rerun()
        else:
            st.error("Invalid username or password.")    
    st.info("Please log in to access Sales data system.",width=350)

else:        
    st.sidebar.title(f"👤 Welcome")
    st.sidebar.success(f"**User:** {st.session_state.username} \n\n **Role:** {st.session_state.role}")

    # 🛑 LOGOUT BUTTON IMPLEMENTATION
    if st.sidebar.button("Log Out", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

    st.sidebar.markdown("---")
        
    #Navigation
    available_pages = ["Dashboard", "Add Sales", "Add Payment", "Sales Report", "Pending Payments"]
    
    if user_role == "Super Admin":
        available_pages.append("SQL Analytics")

    page = st.sidebar.radio("📌 Navigation", available_pages)    

    if page == "Dashboard":
        st.title(f"📊 Sales Insights ({user_branch} View)")            
        query = """
        SELECT 
            SUM(gross_sales) AS total_gross_sales, 
            SUM(received_amount) AS total_recvd_amount,
            SUM(pending_amount) AS total_pending_amount 
        FROM customer_sales
        WHERE 1=1
        """
        if user_role == "Admin":
            query += f" AND branch_name = '{user_branch}'"

        df = execute_query(query) # Extract the value
        total_sales = df["total_gross_sales"].iloc[0] or 0
        total_received = df["total_recvd_amount"].iloc[0] or 0
        total_pending = df["total_pending_amount"].iloc[0] or 0
    
        # Display in Streamlit metric card
        col1, col2, col3 = st.columns(3)
        col1.metric(label="💰 Total Gross Sales", value=f"₹ {round(total_sales):,}")
        col2.metric(label="✅ Received Amount", value=f"₹ {round(total_received):,}")
        col3.metric(label="📉 Pending Amount", value=f"₹ {round(total_pending):,}")

        st.markdown("---")

        # 2. Dynamic Filter Controls
        col_b, col_d, col_e = st.columns(3)
            
        with col_b:    
            if user_role == "Super Admin":
                branches_df = execute_query("SELECT branch_name FROM branches;")
                branch_selection = st.selectbox("🏢 Select Branch", ["All"] + list(branches_df["branch_name"]))
            else:
                st.selectbox("🏢 Your Branch", [user_branch], disabled=True)
                branch_selection = user_branch
            
        with col_d:    
            date_range = st.date_input("📅 Select Date Range", [])

        with col_e:
            product_df = execute_query("SELECT product_name FROM customer_sales;")
            product_selection = st.selectbox("🏢 Select Product", ["All"] + list(product_df["product_name"]))

        #Main table query
        query = """
        SELECT 
            b.branch_name,
            cs.status AS sales_status,
            SUM(cs.gross_sales) AS total_gross_sales, 
            SUM(cs.received_amount) AS received_amount,
            SUM(cs.pending_amount) AS pending_amount,
            COUNT(cs.sale_id) AS total_sales_count
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        WHERE 1=1
        """
        # Apply branch filter
        if branch_selection != "All":
            query += f" AND b.branch_name = '{branch_selection}'"
        if len(date_range) == 2:
            start_date, end_date = date_range
            query += f" AND cs.sale_date BETWEEN '{start_date}' AND '{end_date}'"
        if product_selection != "All":
            query += f" AND cs.product_name = '{product_selection}'"
        query += " GROUP BY b.branch_name, cs.status ORDER BY b.branch_name, cs.status;"

        df = execute_query(query)
        
        if not df.empty:
            df["total_gross_sales"] = df["total_gross_sales"].apply(lambda x: f"₹ {round(x):,}")
            df["received_amount"] = df["received_amount"].apply(lambda x: f"₹ {round(x):,}")
            df["pending_amount"] = df["pending_amount"].apply(lambda x: f"₹ {round(x):,}")
            st.dataframe(df)
        
    elif page == "Add Sales":
        st.title("➕ Add New Sales Record")

        # Lock input drop-downs to the admin's specific branch parameters
        if user_role == "Admin":
            df_branches = execute_query(f"SELECT branch_id, branch_name FROM branches WHERE branch_name = '{user_branch}';")
        else:
            df_branches = execute_query("SELECT branch_id, branch_name FROM branches ORDER BY branch_id;")

        #Input Form
        branch_name = st.selectbox("📦 Select Branch Name", list(df_branches["branch_name"]))
        sale_date = st.date_input("📅 Sale Date")
        name = st.text_input("👤 Customer Name")
        mobile_number = st.text_input("📱 Mobile Number")
        df_products = execute_query("SELECT DISTINCT product_name FROM customer_sales ORDER BY product_name;")
        product_name = st.selectbox("📦 Select Product", list(df_products["product_name"]))
        gross_sales = st.number_input("💰 Gross Sales", min_value=0)
        status = st.selectbox("📌 Status", ["Open", "Close"])
    
        # Submit button
        if st.button("Save Sale"):
            success = insert_sales_record(sale_date, name, mobile_number,product_name, 
                                          gross_sales, status, branch_name
            )
            if success:st.success("✅ Sale record added successfully!")
            else: st.error("❌ Failed to add sale record.")
            
    elif page == "Add Payment":
        st.title("➕ Add Payment Record")

    # Form inputs
        if user_role == "Admin":
            sale_id_query = f"""
                SELECT DISTINCT ps.sale_id 
                FROM payment_splits ps
                JOIN customer_sales cs ON ps.sale_id = cs.sale_id
                WHERE cs.branch_name = '{user_branch}'
                ORDER BY ps.sale_id;
            """
        else:
            sale_id_query = "SELECT DISTINCT sale_id FROM payment_splits ORDER BY sale_id;"
        
        df_payments = execute_query(sale_id_query)
        sale_list = list(df_payments["sale_id"])
        
        if not sale_list:
            st.info(f"ℹ️ No active sales records found for {user_branch if user_role == 'Admin' else 'any branch'}.")
        else:
            sale_id = st.selectbox("📦 Select Sale ID", sale_list)
            payment_date = st.date_input("📅 Payment Date")
            amount_paid = st.number_input("✅ Amount Paid", min_value=0)
            
            df_pay_method = execute_query("SELECT DISTINCT payment_method FROM payment_splits ORDER BY payment_method;")
            pay_list = list(df_pay_method["payment_method"])
            payment_method = st.selectbox("📱 Select Payment Method", pay_list)

        # Submit button
        if st.button("Save Payment"):
            success = insert_payment_record(
                sale_id, payment_date, amount_paid, payment_method
            )
            if success:
                st.success("✅ Payment record added successfully!")
            else:
                st.error("❌ Failed to add payment record.")

    elif page == "Sales Report":
        st.title("📈 Sales Report")
        tab1, tab2, tab3 = st.tabs(["📊 Executive Overview", "👥 Branch Performance", "📋 Open vs Close"])

        branch_condition = f"WHERE branch_name = '{user_branch}'" if user_role == "Admin" else ""
        joint_condition = f"WHERE b.branch_name = '{user_branch}'" if user_role == "Admin" else ""

        with tab1:
            st.subheader("High-Level Performance")
            query = f"""
            SELECT 
                SUM(gross_sales) AS total_gross_sales, 
                SUM(received_amount) AS total_recvd_amount,
                SUM(pending_amount) AS total_pending_amount 
            FROM customer_sales {branch_condition};
            """              
            df = execute_query(query)
            total_sales = df["total_gross_sales"].iloc[0]
            total_received = df["total_recvd_amount"].iloc[0]
            total_pending = df["total_pending_amount"].iloc[0]
            col1, col2, col3 = st.columns(3)
            col1.metric(label="💰 Total Gross Sales", value=f"₹ {round(total_sales):,}")
            col2.metric(label="✅ Received Amount", value=f"₹ {round(total_received):,}")
            col3.metric(label="📉 Pending Amount", value=f"₹ {round(total_pending):,}")

        with tab2:
            st.subheader("Branch Performance")
            query = f"""
            SELECT 
                b.branch_name,
                SUM(cs.gross_sales) AS total_gross_sales, 
                SUM(cs.received_amount) AS received_amount,
                SUM(cs.pending_amount) AS pending_amount,
                COUNT(cs.sale_id) AS total_sales_count
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            {joint_condition} GROUP BY b.branch_name, cs.status ORDER BY b.branch_name, cs.status;
            """
            df = execute_query(query)
            df["total_gross_sales"] = df["total_gross_sales"].apply(lambda x: f"₹ {round(x):,}")
            df["received_amount"] = df["received_amount"].apply(lambda x: f"₹ {round(x):,}")
            df["pending_amount"] = df["pending_amount"].apply(lambda x: f"₹ {round(x):,}")
            
            st.dataframe(df, use_container_width=True) 

        with tab3:
            st.subheader("Open vs Close")
            query = f"""
            SELECT 
                cs.status AS Sale_Status, 
                cs.branch_name,
                cs.product_name, 
                sum(cs.gross_sales) AS total_gross_sales, 
                sum(cs.received_amount) AS received_amount, 
                sum(cs.pending_amount) AS pending_amount
	        FROM customer_sales cs 
	        {branch_condition} GROUP BY cs.status, cs.branch_name, cs.product_name
            """
            df = execute_query(query)
            df["total_gross_sales"] = df["total_gross_sales"].apply(lambda x: f"₹ {round(x):,}")
            df["received_amount"] = df["received_amount"].apply(lambda x: f"₹ {round(x):,}")
            df["pending_amount"] = df["pending_amount"].apply(lambda x: f"₹ {round(x):,}")

            st.dataframe(df, use_container_width=True) 

    elif page == "Pending Payments":
        st.title("💰 Pending Payment Report")
        branch_condition = f"WHERE branch_name = '{user_branch}'" if user_role == "Admin" else ""
        query = f"""
        SELECT  
                cs.name AS Customer_Name,
                cs.branch_name,
                cs.product_name, 
                sum(cs.gross_sales) AS total_gross_sales, 
                sum(cs.received_amount) AS received_amount, 
                sum(cs.pending_amount) AS pending_amount
	    FROM customer_sales cs
        {branch_condition} GROUP BY cs.name, cs.branch_name, cs.product_name
        """
        df = execute_query(query)
        df["total_gross_sales"] = df["total_gross_sales"].apply(lambda x: f"₹ {round(x):,}")
        df["received_amount"] = df["received_amount"].apply(lambda x: f"₹ {round(x):,}")
        df["pending_amount"] = df["pending_amount"].apply(lambda x: f"₹ {round(x):,}")
        st.dataframe(df,use_container_width=True, hide_index=True) 

    elif page == "SQL Analytics":
        st.title("➕ Select questions from dropdown:")
        
        queries_map = {
        "1. Retrieve all records from the customer_sales table": """
        SELECT * FROM customer_sales;
        """,
        "2. Retrieve all records from the branches table": """
        SELECT * FROM branches;
        """,
        "3. Retrieve all records from the payment_splits table": """
            SELECT * FROM payment_splits;
        """,
        "4. Display all sales with status = 'Open'": """
            SELECT * FROM customer_sales 
            WHERE status = 'Open';
        """,
        "5. Retrieve all sales belonging to the Chennai branch": """
            SELECT cs.* 
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            WHERE b.branch_name = 'Chennai';
        """,
        "6. Calculate the total gross sales across all branches": """
            SELECT to_char(SUM(gross_sales), '₹99,99,99,999') AS total_gross_sales 
            FROM customer_sales;
        """,
        "7. Calculate the total received amount across all sales": """
            SELECT to_char(SUM(received_amount), '₹99,99,99,999') AS total_received_amount 
            FROM customer_sales;
        """,
        "8. Calculate the total pending amount across all sales.":"""
        SELECT to_char(SUM(pending_amount), '₹99,99,99,999') AS total_pending_amount 
            FROM customer_sales;
        """,
        "9. Count the total number of sales per branch.":"""
        SELECT branches.branch_name, COUNT(customer_sales.sale_id) FROM customer_sales
	    JOIN branches
	    ON customer_sales.branch_id = branches.branch_id
	    GROUP BY branches.branch_name;
        """,
        "10. Find the average gross sales amount":"""
        SELECT branches.branch_name, to_char(AVG(customer_sales.gross_sales), '₹99,99,99,999') AS Avg_gross_sales FROM customer_sales
        JOIN branches
        ON customer_sales.branch_id = branches.branch_id
        GROUP BY branches.branch_name;
        """,
        "11. Retrieve sales details along with the branch name":"""
        SELECT branches.branch_name, to_char(SUM(customer_sales.gross_sales), '₹99,99,99,999') AS total_gross_sales FROM customer_sales
	    JOIN branches
	    ON customer_sales.branch_id = branches.branch_id
	    GROUP BY branches.branch_name;
        """,
        "12. Retrieve sales details along with total payment received (using payment_splits)":"""   
        SELECT 
            cs.sale_id, cs.sale_date, cs.name AS customer_name, cs.product_name, to_char(cs.gross_sales, '₹99,99,99,999'),
            to_char(ps_total.total_received, '₹99,99,99,999') AS total_payment_received,
            cs.status
        FROM customer_sales cs
        LEFT JOIN (
            SELECT 
                sale_id, 
                SUM(amount_paid) AS total_received
            FROM payment_splits
            GROUP BY sale_id
        ) ps_total ON cs.sale_id = ps_total.sale_id;
    """,
        "13. Show branch-wise total gross sales (using JOIN & GROUP BY)":"""
        SELECT branches.branch_name, to_char(SUM(customer_sales.gross_sales), '₹99,99,99,999') AS total_gross_sales FROM customer_sales
        JOIN branches
        ON customer_sales.branch_id = branches.branch_id
        GROUP BY branches.branch_name;
        """,
        "14. Display sales along with payment method used": """
        SELECT customer_sales.*, payment_splits.payment_method
        FROM customer_sales
        JOIN payment_splits
        ON customer_sales.sale_id = payment_splits.sale_id;
        """,
        "15. Retrieve sales along with branch admin name": """
        SELECT customer_sales.*, branches.branch_admin_name
        FROM customer_sales
        JOIN branches
        ON customer_sales.branch_id = branches.branch_id;
        """,
        "16. Find sales where the pending amount is greater than 5000":"""
        SELECT * FROM customer_sales WHERE gross_sales > 5000;
        """,
        "17. Retrieve top 3 highest gross sales":"""
        SELECT 
            b.branch_name, 
            cs.sale_id,
            cs.name AS customer_name,
            cs.product_name,
            cs.gross_sales
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        ORDER BY cs.gross_sales DESC
        LIMIT 3;
        """,
        "18. Find the branch with highest total gross sales":"""
        SELECT 
            b.branch_name,
            cs.branch_id,
            to_char(sum(cs.gross_sales), '₹99,99,99,999') AS total_gross_sales
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            GROUP BY b.branch_name, cs.branch_id
            ORDER BY total_gross_sales DESC
            LIMIT 1;
        """,
        "19. Retrieve monthly sales summary (group by month & year)":"""
        SELECT 
            EXTRACT(YEAR FROM sale_date) AS year, EXTRACT(MONTH FROM sale_date) AS month, 
            to_char(sum(cs.gross_sales), '₹99,99,99,999')	
        FROM customer_sales cs
        GROUP BY year, month;
        """,
        "20. Calculate payment method-wise total collection (Cash / UPI / Card)":"""
        SELECT
            payment_method,
            to_char(sum(amount_paid), '₹99,99,99,999') AS total_amount_collected
            FROM payment_splits
            GROUP BY payment_method
            ORDER BY payment_method;
        """
        }
        
        #2. Pass the dictionary keys directly into the selectbox
        selected_question = st.selectbox("📦 Select SQL Questions", list(queries_map.keys()))
        conn = get_connection()
        if selected_question:
            sql_query = queries_map[selected_question]
        st.markdown("### 🖥️ Executing SQL Query:")
        st.code(sql_query, language="sql")
        try:
            # Run the query against your database
            df = pd.read_sql(sql_query,conn)
        
            # Display the result using modern clean parameters
            st.markdown("### 📋 Query Results")
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("The query executed successfully but returned 0 records.")            
        except Exception as e:
            st.error(f"Database Error: {e}")