import streamlit as st
import pandas as pd
from dashboard import show_dashboard
from PredictandTrain import show_predict
from DataPenjualan import show_data_penjualan
from PIL import Image
import pymysql
import base64
import io

# Konfigurasi koneksi database MySQL
db_config = {
    'host': 'localhost',       # Ganti dengan host database kamu
    'user': 'admin',           # Ganti dengan username database kamu
    'password': '',            # Ganti dengan password database kamu
    'database': 'db_zul'       # Ganti dengan nama database kamu
}

# Fungsi untuk mengambil data dari MySQL
def load_data(query):
    connection = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    try:
        df = pd.read_sql(query, connection)
    finally:
        connection.close()
    return df

query = "SELECT * FROM penjualan_zul_toys"
df = load_data(query)

# Membuat kolom 'Tanggal' dari kolom 'Bulan' dan 'Tahun'
df['Tanggal'] = pd.to_datetime(df['Tahun'].astype(str) + '-' + df['Bulan'].astype(str), format='%Y-%m')

# Load the local image
image = Image.open("logo.png")

def image_to_base64(image):
    """Convert an image to a base64-encoded string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# Convert image to base64
img_base64 = image_to_base64(image)

# HTML to position the logo image
logo_html = f"""
<style>
.sidebar-content {{
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 0px; /* Adjust this value to move the logo up or down */
}}
.logo {{
    margin-bottom: 5px; /* Adjust this value to add space below the logo */
}}
</style>
<div class="sidebar-content">
    <img src="data:image/png;base64,{img_base64}" class="logo" width="350">
</div>
"""

st.sidebar.markdown(logo_html, unsafe_allow_html=True)

# Main function to control the page display
def main():
    st.sidebar.title("Menu")

    # Use selectbox for navigation
    page = st.sidebar.selectbox(
        "Pilih Halaman",
        ["Dashboard", "Data Penjualan Perbulan", "Prediksi Penjualan"]
    )

    if page == "Dashboard":
        show_dashboard(df)
    elif page == "Data Penjualan Perbulan":
        show_data_penjualan(df)
    elif page == "Prediksi Penjualan":
        show_predict(df)

# Run the app
if __name__ == "__main__":
    main()
