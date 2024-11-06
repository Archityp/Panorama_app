import streamlit as st
from datetime import datetime, timedelta
import random
import string
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from streamlit_pannellum import streamlit_pannellum
import base64

# Access credentials, sheet ID, and scope from secrets data
ADMIN_PASSWORD = st.secrets["PASSWORD"]
GOOGLE_SHEETS_CREDENTIALS = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
SHEET_ID = st.secrets["SHEET_ID"]
SCOPE = st.secrets["SCOPE"]
MASTER_KEY = st.secrets["MASTER_KEY"]
# Google Sheets setup
credentials = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_SHEETS_CREDENTIALS, SCOPE)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).sheet1  # Access the first sheet

# Function to generate a random token
def generate_token(length=12):
    """Generates a random token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to store token in Google Sheets
def store_token_in_sheet(token, expiration_date):
    """Stores the token and expiration date in Google Sheets."""
    sheet.append_row([token, expiration_date.strftime("%Y-%m-%d %H:%M:%S")])  # Adjust columns if needed

# Function to check if the provided token is valid
def validate_token(token):
    """Validates the token by checking Google Sheets for an expiration date."""
    records = sheet.get_all_records()
    for record in records:
        if record["Token"] == token:
            exp_date = datetime.strptime(record["Expiration_Date"], "%Y-%m-%d %H:%M:%S")
            if exp_date >= datetime.now():
                return True
    return False

def clear_expired_tokens():
    """Removes all expired tokens from Google Sheets and clears empty rows."""
    # Fetch all rows (as a list of lists, including empty rows).
    all_rows = sheet.get_all_values()

    # Extract header and data rows
    header = all_rows[0]
    data_rows = all_rows[1:]

    # Keep rows where expiration date is still valid
    valid_rows = [header]  # Start with the header row
    for row in data_rows:
        token, exp_date_str = row  # Assumes 2 columns
        try:
            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d %H:%M:%S")
            if exp_date >= datetime.now():  # Keep only non-expired tokens
                valid_rows.append(row)
        except ValueError:
            continue  # Skip rows with invalid date formats (if any)

    # Clear the sheet and re-write only valid rows to remove gaps
    sheet.clear()
    sheet.update("A1", valid_rows)

# Function to display a 360° image
def display_panorama(image_data, title):
    """Helper function to display a 360° image using Pannellum with a base64-encoded image."""
    image_base64 = base64.b64encode(image_data).decode()
    panorama_url = f"data:image/jpeg;base64,{image_base64}"

    # Display panorama
    streamlit_pannellum(
        config={
            "default": {
                "firstScene": title,
            },
            "scenes": {
                title: {
                    "title": title,
                    "type": "equirectangular",
                    "panorama": panorama_url,
                    "autoLoad": True,
                    "author": "User",
                }
            }
        }
    )


def main():
    # Admin Sidebar Authentication
    st.sidebar.title("Admin Login")
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    # Only show login form if admin is not authenticated
    if not st.session_state.admin_authenticated:
        password_input = st.sidebar.text_input("Enter Admin Password:", type="password")
        if st.sidebar.button("Login"):
            if password_input == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.sidebar.success("Access granted. You are now logged in.")
                st.rerun()
            else:
                st.sidebar.error("Access denied. Incorrect password.")
    else:
        # Admin Token Generator Section
        st.sidebar.title("Token Generator")
        st.sidebar.write("Generate a token with a specified expiration time.")

        # Token duration input
        days = st.sidebar.number_input("Token Validity (days)", min_value=1, max_value=30, value=1, step=1)

        # Generate Token button
        if st.sidebar.button("Generate Token"):
            token = generate_token()
            expiration_date = datetime.now() + timedelta(days=days)
            store_token_in_sheet(token, expiration_date)
            st.sidebar.success("Token generated and saved.")

            # Display the generated token and expiration date
            st.sidebar.write("Generated Token:")
            st.sidebar.code(token)
            st.sidebar.write(f"Expires on: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}")

        # Add button to clear expired tokens
        if st.sidebar.button("Clear Expired Tokens"):
            clear_expired_tokens()
            st.sidebar.success("Expired tokens cleared.")

    # Access control with token or master key
    st.title("360° Photo Access")
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.write("Please enter a valid token or master key to access the 360° photo viewer.")
        access_code = st.text_input("Enter Token:", type="password")
        if st.button("Submit"):
            if access_code == MASTER_KEY or validate_token(access_code):
                st.session_state.authenticated = True
                st.success("Access granted.")
                st.rerun()
            else:
                st.error("Invalid token or master key.")
    else:
        # Main photo viewer logic after successful authentication
        st.title("Multi-File 360° Photo Viewer")
        st.write("Upload up to 3 images to preview them interactively in separate viewers.")

        # Allow multiple file uploads
        uploaded_files = st.file_uploader("Choose up to 3 images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

        # Limit to 3 files and check for valid uploads
        if uploaded_files:
            if len(uploaded_files) > 3:
                st.warning("Please upload a maximum of 3 files.")
            else:
                # Display each uploaded image in a separate viewer
                for i, uploaded_file in enumerate(uploaded_files):
                    # Read image data
                    image_data = uploaded_file.read()
                    st.write(f"Displaying Panorama {i + 1}")

                    # Display panorama for each file
                    display_panorama(image_data, f"Panorama {i + 1}")
        else:
            st.write("No files uploaded.")

if __name__ == "__main__":
    main()
# streamlit run test_panoram.py
