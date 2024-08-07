import streamlit as st
import pymysql
import pandas as pd

# Konfigurasi koneksi database MySQL
db_config = {
    'host': 'localhost',
    'user': 'admin',
    'password': '',
    'database': 'db_zul'
}

def get_db_connection():
    return pymysql.connect(**db_config)

def load_data(query):
    try:
        connection = get_db_connection()
        df = pd.read_sql(query, connection)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        df = pd.DataFrame()
    finally:
        connection.close()
    return df

def initialize_session_state():
    if 'bulan' not in st.session_state:
        st.session_state.bulan = 1
    if 'tahun' not in st.session_state:
        st.session_state.tahun = 2022

def generate_new_id(bulan, tahun):
    prefix = f'Zul-{bulan}-{tahun}-%'
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT MAX(ID_PENJUALAN_PERBULAN) FROM penjualan_zul_toys 
                WHERE ID_PENJUALAN_PERBULAN LIKE %s
            """, (prefix,))
            result = cursor.fetchone()
    except Exception as e:
        st.error(f"Error generating new ID: {e}")
        return None
    finally:
        conn.close()

    if result[0]:
        last_id = result[0]
        last_number = int(last_id.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    new_id = f'Zul-{bulan}-{tahun}-{str(new_number).zfill(1)}'
    return new_id

def calculate_margin(costprice, salesprice1):
    if salesprice1 != 0:
        margin = ((salesprice1 - costprice) / salesprice1) * 100
    else:
        margin = 0
    return margin

def update_values(bulan, tahun, jumlah, salesprice1, costprice):
    id_penjualan = generate_new_id(str(bulan).zfill(2), tahun)
    total = jumlah * salesprice1
    margin = calculate_margin(costprice, salesprice1)
    total_laba = total * (margin / 100)
    return id_penjualan, total, margin, total_laba

def create_record_from_df(df):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
            INSERT INTO penjualan_zul_toys (ID_PENJUALAN_PERBULAN, Kode, Nama, Jumlah, Satuan, Bulan, Tahun, costprice, salesprice1, Total, Margin, Total_Laba, is_holiday, Awal_Ramadhan, Hari_Raya_Idul_Fitri)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(query, df.values.tolist())
            conn.commit()
    except Exception as e:
        st.error(f"Error creating record: {e}")
    finally:
        conn.close()

def update_record_in_db(df):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
            UPDATE penjualan_zul_toys
            SET Kode = %s, Nama = %s, Jumlah = %s, Satuan = %s, Bulan = %s, Tahun = %s, costprice = %s, salesprice1 = %s, Total = %s, Margin = %s, Total_Laba = %s, is_holiday = %s, Awal_Ramadhan = %s, Hari_Raya_Idul_Fitri = %s
            WHERE ID_PENJUALAN_PERBULAN = %s
            """
            cursor.execute(query, (
                df['Kode'][0], df['Nama'][0], df['Jumlah'][0], df['Satuan'][0],
                df['Bulan'][0], df['Tahun'][0], df['costprice'][0], df['salesprice1'][0],
                df['Total'][0], df['Margin'][0], df['Total_Laba'][0], df['is_holiday'][0],
                df['Awal_Ramadhan'][0], df['Hari_Raya_Idul_Fitri'][0],
                df['ID_PENJUALAN_PERBULAN'][0]
            ))
            conn.commit()
    except Exception as e:
        st.error(f"Error updating record: {e}")
    finally:
        conn.close()

def update_checkboxes_in_db(bulan, tahun, is_holiday, awal_ramadhan, hari_raya_idul_fitri):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = """
            UPDATE penjualan_zul_toys
            SET is_holiday = %s, Awal_Ramadhan = %s, Hari_Raya_Idul_Fitri = %s
            WHERE Bulan = %s AND Tahun = %s
            """
            cursor.execute(query, (is_holiday, awal_ramadhan, hari_raya_idul_fitri, bulan, tahun))
            conn.commit()
    except Exception as e:
        st.error(f"Error updating records: {e}")
    finally:
        conn.close()

def check_duplicate(nama, bulan, tahun):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT COUNT(*) FROM penjualan_zul_toys
            WHERE Nama = %s AND Bulan = %s AND Tahun = %s
            """, (nama, bulan, tahun))
            count = cursor.fetchone()[0]
    except Exception as e:
        st.error(f"Error checking duplicates: {e}")
        count = 0
    finally:
        conn.close()
    return count > 0

def validate_inputs(jumlah, salesprice1, costprice):
    if jumlah < 0 or salesprice1 < 0 or costprice < 0:
        st.error("Jumlah, Salesprice1, dan Costprice harus bernilai positif.")
        return False
    return True

def get_kode_and_kategori(nama, df):
    row = df[df['Nama'] == nama]
    if not row.empty:
        return row['Kode'].values[0]
    return ''

def delete_record_from_db(id_penjualan):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM penjualan_zul_toys
                WHERE ID_PENJUALAN_PERBULAN = %s
            """, (id_penjualan,))
            conn.commit()
    except Exception as e:
        st.error(f"Error deleting record: {e}")
    finally:
        conn.close()

def generate_new_id_import(bulan, tahun, last_id_number):
    new_number = last_id_number + 1
    new_id = f'Zul-{bulan}-{tahun}-{str(new_number).zfill(1)}'
    return new_id

def import_data_from_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            return pd.DataFrame()  # Return an empty DataFrame if file type is unsupported

        # Process and validate the DataFrame
        required_columns = ['Kode', 'Nama', 'Jumlah', 'Satuan', 'Bulan', 'Tahun', 'costprice', 'salesprice1']
        if not all(col in df.columns for col in required_columns):
            st.error(f"Data file must contain the following columns: {', '.join(required_columns)}")
            return pd.DataFrame()  # Return an empty DataFrame if columns are missing


        # Get the last ID number from the database for the specific month and year
        bulan = str(int(df['Bulan'].max())).zfill(2)
        tahun = df['Tahun'].max()
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT MAX(CAST(SUBSTRING_INDEX(ID_PENJUALAN_PERBULAN, '-', -1) AS UNSIGNED))
                    FROM penjualan_zul_toys
                    WHERE ID_PENJUALAN_PERBULAN LIKE %s
                """, (f'Zul-{bulan}-{tahun}-%',))
                result = cursor.fetchone()
                last_id_number = result[0] if result[0] is not None else 0
        except Exception as e:
            st.error(f"Error fetching last ID number: {e}")
            last_id_number = 0
        finally:
            conn.close()
        
        # Generate IDs for each row in the DataFrame
        df['ID_PENJUALAN_PERBULAN'] = [generate_new_id_import(bulan, tahun, i + last_id_number) for i in range(len(df))]
        

        return df

    except Exception as e:
        st.error(f"Error importing data: {e}")
        return pd.DataFrame()

def show_data_penjualan(df):
    st.title('Data Penjualan Perbulan')

    # Muat semua data dari database
    df_loaded = df.copy()
     # Define date range from DataFrame
    min_date = df_loaded['Tanggal'].min().date()
    max_date = df_loaded['Tanggal'].max().date()

    # Add filter inputs for date range
    st.subheader("Filter Data")
    
    # Create two columns for date input
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start date", value=min_date)
    
    with col2:
        end_date = st.date_input("End date", value=max_date)

    if start_date > end_date:
        st.error("Start date should be before end date.")
    else:
        # Filter data based on selected dates
        filtered_df = df_loaded[(df_loaded['Tanggal'].dt.date >= start_date) & (df_loaded['Tanggal'].dt.date <= end_date)]
        st.write(f"Menampilkan data dari {start_date} sampai {end_date}")
        st.write(filtered_df)
   
    # Pastikan start_date tidak setelah end_date
    if start_date > end_date:
        st.error('Start Date harus sebelum atau sama dengan End Date.')
        return

    # Pilih aksi
    action = st.selectbox("Pilih Tindakan:", [None, "Import File","Buat Baru", "Edit", "Hapus",])

    if action == "Buat Baru":
        st.subheader("Masukkan Data")
        bulan_options = list(range(1, 13))
        tahun_options = list(range(2022, 2030))
        
        if 'bulan' not in st.session_state:
            st.session_state.bulan = 1
        if 'tahun' not in st.session_state:
            st.session_state.tahun = 2024

        bulan = st.selectbox('Bulan', bulan_options, index=st.session_state.bulan - 1)
        tahun = st.selectbox('Tahun', tahun_options, index=tahun_options.index(st.session_state.tahun))

        if bulan != st.session_state.bulan or tahun != st.session_state.tahun:
            st.session_state.bulan = bulan
            st.session_state.tahun = tahun

        id_penjualan, total, margin, total_laba = update_values(st.session_state.bulan, st.session_state.tahun, 0, 0, 0)
        st.text_input('ID_PENJUALAN_PERBULAN', value=id_penjualan, disabled=True)

        nama = st.selectbox('Nama', options=df_loaded['Nama'].unique().tolist())
        kode = get_kode_and_kategori(nama, df_loaded)
        satuan = st.selectbox('Satuan', options=df_loaded['Satuan'].unique().tolist())
        costprice = st.number_input('Costprice', min_value=0, value=0)
        salesprice1 = st.number_input('Salesprice1', min_value=0, value=0)
        jumlah = st.number_input('Jumlah', min_value=0, value=0)
        id_penjualan, total, margin, total_laba = update_values(st.session_state.bulan, st.session_state.tahun, jumlah, salesprice1, costprice)

        st.write(f"Margin: {margin:.2f}%")
        st.write(f"Total: {total}")
        st.write(f"Total Laba: {total_laba}")
        is_holiday = st.checkbox("Apakah ada event?", value=False)
        awal_ramadhan = st.checkbox("Awal Ramadhan", value=False)
        hari_raya = st.checkbox("Hari raya Idul Fitri", value=False)
        if st.button('Simpan'):
            if validate_inputs(jumlah, salesprice1, costprice):
                if check_duplicate(nama, st.session_state.bulan, st.session_state.tahun):
                    st.error('Data dengan nama barang, bulan, dan tahun yang sama sudah ada di database. Silahkan edit atau hapus terlebih dahulu!')
                else:
                    data = {
                        'ID_PENJUALAN_PERBULAN': [id_penjualan],
                        'Kode': [kode],
                        'Nama': [nama],
                        'Jumlah': [jumlah],
                        'Satuan': [satuan],
                        'Bulan': [bulan],
                        'Tahun': [tahun],
                        'costprice': [costprice],
                        'salesprice1': [salesprice1],
                        'Total': [total],
                        'Margin': [margin],
                        'Total_Laba': [total_laba],
                        'is_holiday': [is_holiday],
                        'Awal_Ramadhan': [awal_ramadhan],
                        'Hari_Raya_Idul_Fitri': [hari_raya]
                    }
                    df_to_insert = pd.DataFrame(data)
                    create_record_from_df(df_to_insert)
                    st.success("Record berhasil disimpan!")

    elif action == "Edit":
        st.subheader("Edit Data")
        unique_combinations = df_loaded[['Nama', 'Bulan', 'Tahun']].drop_duplicates()

        nama_edit = st.selectbox('Pilih Nama Barang yang Akan Diedit', options=unique_combinations['Nama'].unique())
        bulan_edit = st.selectbox('Pilih Bulan', options=list(range(1, 13)), index=list(range(1, 13)).index(unique_combinations[(unique_combinations['Nama'] == nama_edit)]['Bulan'].values[0]) if not unique_combinations[unique_combinations['Nama'] == nama_edit].empty else 1)
        tahun_edit = st.selectbox('Pilih Tahun', options=list(range(2022, 2030)), index=list(range(2022, 2030)).index(unique_combinations[(unique_combinations['Nama'] == nama_edit)]['Tahun'].values[0]) if not unique_combinations[unique_combinations['Nama'] == nama_edit].empty else 2022)

        if nama_edit and bulan_edit and tahun_edit:
            selected_row = df_loaded[(df_loaded['Nama'] == nama_edit) & (df_loaded['Bulan'] == bulan_edit) & (df_loaded['Tahun'] == tahun_edit)]
            
            if not selected_row.empty:
                edit_row = selected_row.iloc[0]

                st.text_input('ID_PENJUALAN_PERBULAN', value=edit_row['ID_PENJUALAN_PERBULAN'], disabled=True)
                kode = get_kode_and_kategori(nama_edit, df_loaded)
                
                jumlah = st.number_input('Jumlah', min_value=0, value=edit_row['Jumlah'])
                satuan = st.selectbox('Satuan', options=df_loaded['Satuan'].unique().tolist())
                costprice = st.number_input('Costprice', min_value=0, value=edit_row['costprice'])
                salesprice1 = st.number_input('Salesprice1', min_value=0, value=edit_row['salesprice1'])
                
                # Checkbox states
                is_holiday = st.checkbox("Apakah ada event?", value=edit_row['is_holiday'] == 1)
                is_ramadhan = st.checkbox("Awal Ramadhan?", value=edit_row['Awal_Ramadhan'] == 1)
                is_idulFitri = st.checkbox("Hari Raya Idul Fitri", value=edit_row['Hari_Raya_Idul_Fitri'] == 1)

                id_penjualan, total, margin, total_laba = update_values(bulan_edit, tahun_edit, jumlah, salesprice1, costprice)

                st.write(f"Margin: {margin:.2f}%")
                st.write(f"Total: {total}")
                st.write(f"Total Laba: {total_laba}")

                if st.button('Update'):
                    # Update the specific row
                    updated_data = {
                        'ID_PENJUALAN_PERBULAN': [edit_row['ID_PENJUALAN_PERBULAN']],
                        'Kode': [kode],
                        'Nama': [edit_row['Nama']],
                        'Jumlah': [jumlah],
                        'Satuan': [satuan],
                        'Bulan': [bulan_edit],
                        'Tahun': [tahun_edit],
                        'costprice': [costprice],
                        'salesprice1': [salesprice1],
                        'Total': [jumlah * salesprice1],
                        'Margin': [calculate_margin(costprice, salesprice1)],
                        'Total_Laba': [jumlah * salesprice1 * (calculate_margin(costprice, salesprice1) / 100)],
                        'is_holiday': [1 if is_holiday else 0],
                        'Awal_Ramadhan':[1 if is_ramadhan else 0],
                        'Hari_Raya_Idul_Fitri':[1 if is_idulFitri else 0]
                    }
                    df_update = pd.DataFrame(updated_data)
                    update_record_in_db(df_update)
                    
                    # Update all records with the same bulan and tahun for the checkboxes
                    update_checkboxes_in_db(bulan_edit, tahun_edit,
                                            1 if is_holiday else 0,
                                            1 if is_ramadhan else 0,
                                            1 if is_idulFitri else 0)
                    st.success('Record updated successfully!')

    elif action == "Hapus":
        st.subheader("Hapus Data")
        unique_combinations = df_loaded[['Nama', 'Bulan', 'Tahun']].drop_duplicates()
        
        # Pilih bulan dan tahun terlebih dahulu
        bulan_hapus = st.selectbox('Pilih Bulan', options=list(range(1, 13)))
        tahun_hapus = st.selectbox('Pilih Tahun', options=list(range(2022, 2030)))
        
        # Filter data berdasarkan bulan dan tahun
        filtered_data = df_loaded[(df_loaded['Bulan'] == bulan_hapus) & (df_loaded['Tahun'] == tahun_hapus)]
        
        if not filtered_data.empty:
            st.write("Data yang akan dihapus:")
            st.dataframe(filtered_data)

            hapus_semua = st.checkbox("Hapus semua barang pada bulan dan tahun ini")
            
            if hapus_semua:
                if st.button('Hapus Semua'):
                    try:
                        conn = get_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM penjualan_zul_toys WHERE Bulan = %s AND Tahun = %s", (bulan_hapus, tahun_hapus))
                            conn.commit()
                        st.success('Semua data untuk bulan dan tahun ini berhasil dihapus!')
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error deleting all records for this period: {e}")
                    finally:
                        conn.close()
            else:
                nama_hapus = st.selectbox('Pilih Nama Barang yang Akan Dihapus', options=filtered_data['Nama'].unique())
                
                if nama_hapus:
                    selected_row = filtered_data[filtered_data['Nama'] == nama_hapus]
                    
                    if not selected_row.empty:
                        delete_row = selected_row.iloc[0]
                        st.text_input('ID_PENJUALAN_PERBULAN', value=delete_row['ID_PENJUALAN_PERBULAN'], disabled=True)
                        st.text_input('Nama', value=delete_row['Nama'], disabled=True)
                        st.number_input('Jumlah', value=delete_row['Jumlah'], disabled=True)
                        st.text_input('Satuan', value=delete_row['Satuan'], disabled=True)
                        st.number_input('Costprice', value=delete_row['costprice'], disabled=True)
                        st.number_input('Salesprice1', value=delete_row['salesprice1'], disabled=True)
                        st.checkbox("Apakah ada event?", value=delete_row['is_holiday'], disabled=True)
                        st.checkbox("Awal Ramadhan?", value=delete_row['Awal_Ramadhan'], disabled=True)
                        st.checkbox("Hari Raya Idul Fitri", value=delete_row['Hari_Raya_Idul_Fitri'], disabled=True)
                        if st.button('Hapus'):
                            try:
                                delete_record_from_db(delete_row['ID_PENJUALAN_PERBULAN'])
                                st.success('Record deleted successfully!')
                                # Refresh DataFrame
                                df_loaded = load_data(df)

                                # Refresh DataFrame
                                st.session_state.df_loaded = load_data()
                                # Rerun Streamlit app to refresh view
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting record: {e}")

    elif action == "Import File":
            st.subheader("Import Data dari File")
            uploaded_file = st.file_uploader("Pilih file CSV atau Excel", type=["csv", "xlsx"])

            if uploaded_file is not None:
                df_imported = import_data_from_file(uploaded_file)
                if not df_imported.empty:
                    is_holiday_default = st.checkbox("Set semua entri sebagai holiday", value=False)
                    is_awal_ramadhan = st.checkbox("Set semua entri sebagai awal Ramadhan", value=False)
                    is_hari_raya = st.checkbox("Set semua entri sebagai hari raya Idul Fitri", value=False)
                    df_imported['is_holiday'] = is_holiday_default
                    df_imported['Awal_Ramadhan'] = is_awal_ramadhan
                    df_imported['Hari_Raya_Idul_Fitri'] = is_hari_raya
                    desired_columns = ['ID_PENJUALAN_PERBULAN','Kode', 'Nama', 'Jumlah', 'Satuan', 'Bulan', 'Tahun', 'costprice',
                                        'salesprice1', 'Total', 'Margin', 'Total_Laba', 'is_holiday','Awal_Ramadhan','Hari_Raya_Idul_Fitri']
                    df_imported = df_imported.reindex(columns=desired_columns)
                    st.write("Data yang diimpor:")
                    st.dataframe(df_imported)

                    if st.button('Simpan Data ke Database'):
                        try:
                            create_record_from_df(df_imported)
                            st.success('Data berhasil disimpan ke database')
                        except Exception as e:
                            st.error(f"Error saving data: {e}")


def main():
    if 'df_loaded' not in st.session_state:
        st.session_state.df_loaded = load_data()  # Initialize session state with data

    df_loaded = st.session_state.df_loaded

    # Show Data
    show_data_penjualan(df_loaded)

if __name__ == "__main__":
    main()