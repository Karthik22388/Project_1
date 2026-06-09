# Project_1
Sales Management System
# 📊 Sales Management System
with
## 🚩 Problem Statement
Organizations operating across multiple branches often face challenges in tracking sales, managing payment collections, monitoring pending amounts, and maintaining structured financial records.  
Manual tracking methods may result in:
- Data inconsistencies  
- Duplicate entries  
- Incorrect payment calculations  
- Lack of transparency in revenue sharing  

The objective of this project is to design and implement a **structured Sales Management System** with defined roles Super Admin / Admin using **PostgreSQL, Python, and Streamlit**.

---

## 🎯 Project Objectives
The system will:
- Store branch-wise sales records  
- Automatically calculate net sales  
- Support split payment tracking  
- Automatically update received and pending amounts using database triggers  
- Provide an interactive **Streamlit dashboard** for both Super Admin and Admin users  

This solution ensures **accurate financial reporting, automated calculations, and real-time sales monitoring**.

---

## 💼 Business Use Cases
- Track branch-wise sales performance  
- Monitor received vs pending payments  
- Automatically calculate net revenue  
- Manage split payments for customers  
- Identify high-performing branches  
- Analyze sales trends by date  
- Monitor revenue-sharing payouts  
- Generate financial summaries for business decision-making  

---

## 🛠️ Tech Stack
- **Backend Database**: PostgreySQL  
- **Frontend Dashboard**: Streamlit  
- **Programming Language**: Python  
- **Database Triggers**: For auto-updating received & pending amounts  

---

## 📂 Project Structure
salesmgmtapp.py
│── login sessions    # User authentication
│── dashboard         # Streamlit dashboard with metrics
│── add_sales         # Form to insert new sales records
│── add_payment       # Payment tracking
│── Sales report      # To view sales report by high performance, Branch performanch, Open vs Close
│── Pending Payments  # To view Pending Payments from sales record
│── SQL Analytics     # Auto output based on 20 SQL questions 
│── db functions      # Database connection & helper functions
│── requirements.txt  # Python dependencies
│── README.md         # Project documentation






