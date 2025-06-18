import streamlit as st
import sqlite3
import datetime
import random
import string
import base64
import pandas as pd  
import io
from PIL import Image

st.set_page_config(page_title="Visitor Management System",
                   page_icon=":wave:",
                   layout="wide")

def connect_db():
    conn = sqlite3.connect('visitor_manage.db')
    return conn

def create_db_table(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS visitors (
            name TEXT,
            contact TEXT,
            visit_purpose TEXT,
            checkin_time TEXT,
            checkout_time TEXT,
            gate_pass TEXT,
            photo TEXT
        )
    ''')
    conn.commit()

def add_visitor_to_db(conn, name, contact, visit_purpose, checkin_time, gate_pass, photo):
    c = conn.cursor()
    c.execute('''
        INSERT INTO visitors (name, contact, visit_purpose, checkin_time, gate_pass, photo)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, contact, visit_purpose, checkin_time, gate_pass, photo))
    conn.commit()

def update_checkout_time_in_db(conn, gate_pass, checkout_time):
    c = conn.cursor()
    c.execute('''
        UPDATE visitors
        SET checkout_time = ?
        WHERE gate_pass = ?
    ''', (checkout_time, gate_pass))
    conn.commit()

def generate_gate_pass():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_all_visitors_from_db(conn):
    c = conn.cursor()
    c.execute('SELECT * FROM visitors')
    return c.fetchall()

def get_visitor_by_details(conn, gate_pass, contact):
    c = conn.cursor()
    c.execute('SELECT * FROM visitors WHERE gate_pass=? AND contact=?', (gate_pass, contact))
    return c.fetchone()

def get_gate_pass_by_visitor_details(conn, name, contact):
    c = conn.cursor()
    c.execute('SELECT gate_pass FROM visitors WHERE name=? AND contact=?', (name, contact))
    return c.fetchone()

conn = connect_db()
create_db_table(conn)

st.title("Visitor Management System")

menu = ["Home", "Visitor", "Admin"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Home":
    st.subheader("Welcome to Visitor Management System")
    st.write("Navigate to the Visitor section to check in or check out.")
    st.write("Use the Admin section to manage and view visitor data.")

elif choice == "Visitor":
    st.header("Visitor Section")
    action = st.sidebar.radio("Choose an action", ["Check-In", "Check-Out"])

    if action == "Check-In":
        st.subheader("Visitor Check-In")
        with st.form("checkin_form"):
            name = st.text_input("Name")
            contact = st.text_input("Contact Number")
            visit_purpose = st.text_input("Purpose of Visit")
            photo = st.camera_input("Capture Photo")

            if st.form_submit_button("Submit"):
                if name and contact and visit_purpose and photo:
                    if len(contact) == 10 and contact.isdigit() and contact[0] in '6789':
                        checkin_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        gate_pass = generate_gate_pass()
                        photo_bytes = photo.getvalue()
                        photo_encoded = base64.b64encode(photo_bytes).decode('utf-8')

                        add_visitor_to_db(conn, name, contact, visit_purpose, checkin_time, gate_pass, photo_encoded)
                        st.success("Check-In Successful!")
                        st.info(f"Your Gate Pass Number: {gate_pass}")
                    else:
                        st.error("Invalid contact number. Must be 10 digits and start with 6, 7, 8, or 9.")
                else:
                    st.error("Please fill in all fields and capture a photo.")

    elif action == "Check-Out":
        st.subheader("Visitor Check-Out")
        gate_pass = st.text_input("Enter Gate Pass Number")
        if st.button("Check-Out"):
            if gate_pass:
                checkout_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_checkout_time_in_db(conn, gate_pass, checkout_time)
                st.success("Check-Out Successful!")
            else:
                st.error("Please enter your gate pass number.")

elif choice == "Admin":
    st.sidebar.subheader("Admin Login")
    admin_password = st.sidebar.text_input("Password", type="password")
    if admin_password == "admin123":
        st.header("Admin Dashboard")

        st.subheader("Visitor Database")
        data = get_all_visitors_from_db(conn)
        df = pd.DataFrame(data, columns=["Name", "Contact", "Purpose", "Check-In Time", "Check-Out Time", "Gate Pass", "Photo"])
        st.dataframe(df)

        st.subheader("Visitor Details")
        gate_pass = st.text_input("Gate Pass Number")
        contact = st.text_input("Contact Number")
        if st.button("Fetch Details"):
            if gate_pass and contact:
                visitor = get_visitor_by_details(conn, gate_pass, contact)
                if visitor:
                    st.write(f"**Name:** {visitor[0]}")
                    st.write(f"**Contact:** {visitor[1]}")
                    st.write(f"**Purpose:** {visitor[2]}")
                    st.write(f"**Check-In Time:** {visitor[3]}")
                    st.write(f"**Check-Out Time:** {visitor[4]}")
                    
                    photo_bytes = base64.b64decode(visitor[6])
                    photo = Image.open(io.BytesIO(photo_bytes))
                    st.image(photo, caption=visitor[0])
                else:
                    st.error("No visitor found with this gate pass number and contact number.")
            else:
                st.error("Please provide both gate pass number and contact number.")

        if st.button("Download Database"):
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="visitor_data.csv">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("Incorrect password.")

conn.close()