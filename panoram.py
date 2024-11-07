import streamlit as st
from datetime import datetime, timedelta
import random
import string
import gspread
from google.oauth2.service_account import Credentials
import base64
from streamlit_pannellum import streamlit_pannellum
import pandas as pd

# Extract credentials and spreadsheet info from secrets
gsheets_creds = st.secrets["connections"]["gsheets"]
master_key = st.secrets["admin"]["MASTER_KEY"]
admin_password = st.secrets["admin"]["ADMIN_PASSWORD"]

# Setup Google Sheets client
scope = ["https://www.googleapis.com/auth/spreadsheets"]
client = gspread.authorize(Credentials.from_service_account_info(gsheets_creds, scopes=scope))
sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

# Helper function to get sheet
def get_sheet(sheet_name="tokens"):
    return client.open_by_url(sheet_url).worksheet(sheet_name)

# Function to generate a random token
def generate_token(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to handle tokens in the sheet
def manage_tokens(token=None, expiration_date=None):
    sheet = get_sheet()
    if token and expiration_date:
        sheet.append_row([token, expiration_date.strftime("%Y-%m-%d %H:%M:%S")])  # Store token
    elif token:  # Validate token
        records = sheet.get_all_records()
        for record in records:
            if record["Token"] == token:
                exp_date = datetime.strptime(record["Expiration_Date"], "%Y-%m-%d %H:%M:%S")
                if exp_date >= datetime.now():
                    return True
        return False
    else:  # Clear expired tokens
        data = sheet.get_all_records()
        valid_rows = [["Token", "Expiration_Date"]] + [
            [row["Token"], row["Expiration_Date"]] for row in data if datetime.strptime(row["Expiration_Date"], "%Y-%m-%d %H:%M:%S") >= datetime.now()
        ]
        sheet.clear()
        sheet.update("A1", valid_rows)

# Function to display a 360° image
def display_panorama(image_data, title):
    panorama_url = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
    streamlit_pannellum(config={"default": {"firstScene": title}, "scenes": {title: {"title": title, "type": "equirectangular", "panorama": panorama_url, "autoLoad": True}}})

# Main app function
def main():
    st.sidebar.title("Admin Login")
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        password_input = st.sidebar.text_input("Enter Admin Password:", type="password")
        if st.sidebar.button("Login") and password_input == admin_password:
            st.session_state.admin_authenticated = True
            st.sidebar.success("Access granted.")
            st.rerun()
        elif password_input:
            st.sidebar.error("Incorrect password.")
    else:
        st.sidebar.title("Token Generator")
        days = st.sidebar.number_input("Token Validity (days)", min_value=1, max_value=30, value=7, step=1)
        
        if st.sidebar.button("Generate Token"):
            token = generate_token()
            expiration_date = datetime.now() + timedelta(days=days)
            manage_tokens(token, expiration_date)
            st.sidebar.success("Token generated.")
            st.sidebar.code(token)
            st.sidebar.write(f"Expires on: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")

        if st.sidebar.button("Clear Expired Tokens"):
            manage_tokens()
            st.sidebar.success("Expired tokens cleared.")
            
        # Button to display the DataFrame of the sheet
        if st.sidebar.button("Display All Tokens"):
            sheet = get_sheet()
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            st.sidebar.write("Sheet Data:")
            st.sidebar.dataframe(df)
            
    st.title("360° Photo Access")
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        access_code = st.text_input("Enter Password:", type="password")
        if st.button("Submit") and (access_code == master_key or manage_tokens(access_code)):
            st.session_state.authenticated = True
            st.success("Access granted.")
            st.rerun()
        elif access_code:
            st.error("Invalid Password.")
    else:
        st.title("Multi-File 360° Photo Viewer")
        uploaded_files = st.file_uploader("Upload up to 3 images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if uploaded_files:
            for i, uploaded_file in enumerate(uploaded_files[:3]):
                st.write(f"Displaying Panorama {i + 1}")
                display_panorama(uploaded_file.read(), f"Panorama {i + 1}")

if __name__ == "__main__":
    main()
