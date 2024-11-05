import streamlit as st
from streamlit_pannellum import streamlit_pannellum
import base64

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

# streamlit run panoram.py