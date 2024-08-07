import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
import seaborn as sns
import matplotlib.pyplot as plt

# Load model dan encoder
encoder_dict = joblib.load('encoder_dict.pkl')
model_rf = joblib.load('model_rfr.pkl')
k_means = joblib.load('kmeans_total.pkl')

def one_hot_encoder(data, feature, keep_first=True):
    one_hot_cols = pd.get_dummies(data[feature], prefix='', prefix_sep='')
    
    # Menangani nama kolom
    for col in one_hot_cols.columns:
        if '_' in col:
            one_hot_cols.rename(columns={col: col.split('_')[1]}, inplace=True)
    
    new_data = pd.concat([data, one_hot_cols], axis=1)
    new_data.drop(feature, axis=1, inplace=True)
    
    if not keep_first:
        new_data = new_data.iloc[:, 1:] 
    return new_data

def create_unique_dataframe(df):
    # Ambil nilai unik dari kolom 'Nama'
    unique_df = df.drop_duplicates(subset=['Nama'])
    
    # Pilih kolom yang diperlukan
    columns_to_include = ['Kode', 'Nama', 'Satuan', 'costprice',
                           'Penjualan Sering', 'Penjualan jarang',
                           'Penjualan lumayan', 'Penjualan sangat jarang',
                           'Penjualan sangat sering']
    
    # Filter kolom yang diinginkan
    unique_df = unique_df[columns_to_include]
    return unique_df
# Encode kolom tanggal
def encode_month(date):
    base_date = pd.Timestamp('2022-09-01')
    months_difference = (date.year - base_date.year) * 12 + (date.month - base_date.month)
    return months_difference

def show_predict(df):
    st.title("Selamat Datang di Halaman Prediksi Penjualan")
    
    # Clustering Total Penjualan Produk Keseluruhan
    total_penjualan_per_produk = df.groupby('Nama')['Total'].sum().reset_index()
    total_penjualan_per_produk.rename(columns={'Total': 'Total_Penjualan'}, inplace=True)
    
    # Standardisasi total penjualan
    scaler = StandardScaler()
    total_penjualan_per_produk['Total_Penjualan_Scaled'] = scaler.fit_transform(total_penjualan_per_produk[['Total_Penjualan']])
    
    # Menentukan jumlah klaster
    total_penjualan_per_produk['Cluster'] = k_means.fit_predict(total_penjualan_per_produk[['Total_Penjualan_Scaled']])
    
    # Menggabungkan kategori penjualan ke dataframe utama
    df = pd.merge(df, total_penjualan_per_produk[['Nama', 'Cluster']], on='Nama', how='left')
    
    # Menambahkan kolom baru dengan label kategori produk
    cluster_labels = {0: 'Penjualan sangat jarang', 1: 'Penjualan Sering', 2: 'Penjualan jarang', 3: 'Penjualan sangat sering', 4: 'Penjualan lumayan'}
    df['Cluster'] = df['Cluster'].map(cluster_labels)
    df = one_hot_encoder(df, 'Cluster', keep_first=True)
    df.drop(columns=['ID_PENJUALAN_PERBULAN', 'Total', 'Total_Laba', 'Margin'], inplace=True)
    df_train = df.copy()

    # Latih Data di Database
    # Fungsi untuk melakukan label encoding
    categorical_cols = ['Kode', 'Nama', 'Satuan', 'is_holiday', 'Awal_Ramadhan', 'Hari_Raya_Idul_Fitri', 
                        'Penjualan sangat jarang', 'Penjualan Sering', 'Penjualan jarang', 
                        'Penjualan sangat sering', 'Penjualan lumayan']
    # label encoding untuk setiap kolom
    updated_encoders = {}
    for col in categorical_cols:
        if col in encoder_dict:
            df_train[col] = encoder_dict[col].transform(df_train[col])
        else:
                    # Buat encoder baru untuk kolom yang tidak ada dalam encoder_dict
                    le = LabelEncoder()
                    new_dataframe[col] = le.fit_transform(new_dataframe[col])
                    updated_encoders[col] = le
                    st.warning(f"Encoder untuk kolom {col} tidak ditemukan. Encoder baru dibuat.")
            
            # Simpan encoder baru untuk kolom yang tidak ada
    if updated_encoders:
        joblib.dump({**encoder_dict, **updated_encoders}, 'encoder_dict.pkl')

    # Encode Tanggal
    df_train['Tanggal'] = pd.to_datetime(df_train['Tanggal'])
    df_train['Tanggal'] = df_train['Tanggal'].apply(encode_month)
    # Train Data
    X_train = df_train[['Kode', 'Nama', 'Satuan', 'Bulan', 'Tahun', 'salesprice1', 'is_holiday',
       'Tanggal', 'Awal_Ramadhan', 'Hari_Raya_Idul_Fitri', 'Penjualan Sering',
       'Penjualan jarang', 'Penjualan lumayan', 'Penjualan sangat jarang',
       'Penjualan sangat sering']]
    y_train = df_train['Jumlah']
    model_rf.fit(X_train, y_train)

    # Membuat data unik berdasarkan nama produk
    data_prediksi = create_unique_dataframe(df)
    action = st.selectbox("Pilih Tindakan:", [None, "Prediksi semua produk", "Prediksi produk tertentu"])
    if action == "Prediksi semua produk":
        # Fungsi untuk menambahkan kolom dengan input pengguna
        def add_new_columns_with_input(new_df, input_date, input_bulan, input_tahun, input_is_holiday, input_ramadhan, input_raya):
            new_df = new_df.copy()
            new_df['is_holiday'] = input_is_holiday
            new_df['Awal_Ramadhan'] = input_ramadhan
            new_df['Hari_Raya_Idul_Fitri'] = input_raya
            new_df['Tanggal'] = input_date
            new_df['Bulan'] = input_bulan
            new_df['Tahun'] = input_tahun
            return new_df
        
        selected_month = st.selectbox('Pilih Bulan:', range(1, 13))
        selected_year = st.selectbox('Pilih Tahun:', range(2022, 2025))

        input_date = datetime(selected_year, selected_month, 1)
        input_is_holiday = st.checkbox('Apakah ada event?')
        input_ramadhan = st.checkbox('Apakah awal Ramadhan?')
        input_raya = st.checkbox('Apakah Hari Raya Idul Fitri?')

        if st.button('Prediksi'):
            new_dataframe = add_new_columns_with_input(data_prediksi, input_date, selected_month, selected_year, input_is_holiday, input_ramadhan, input_raya)
            
            # Tambahkan kolom 'salesprice1' dari df yang sesuai untuk setiap 'Nama'
            salesprice_mapping = df[['Nama', 'salesprice1']].drop_duplicates().set_index('Nama')['salesprice1'].to_dict()
            new_dataframe['salesprice1'] = new_dataframe['Nama'].map(salesprice_mapping)

            # Pastikan urutan kolom sama
            desired_columns = ['Kode', 'Nama', 'Satuan', 'Bulan', 'Tahun', 'salesprice1', 'is_holiday',
                            'Tanggal', 'Awal_Ramadhan', 'Hari_Raya_Idul_Fitri', 'Penjualan Sering',
                            'Penjualan jarang', 'Penjualan lumayan', 'Penjualan sangat jarang',
                            'Penjualan sangat sering']
            new_dataframe = new_dataframe.reindex(columns=desired_columns)

            new_dataframe['Tanggal'] = pd.to_datetime(new_dataframe['Tanggal'])

            new_dataframe['Tanggal'] = new_dataframe['Tanggal'].apply(encode_month)
            new_dataframe1 = new_dataframe.copy()
            # Fungsi untuk melakukan label encoding pada input prediksi
            categorical_cols = ['Kode', 'Nama', 'Satuan', 'is_holiday', 'Awal_Ramadhan', 'Hari_Raya_Idul_Fitri', 
                                'Penjualan sangat jarang', 'Penjualan Sering', 'Penjualan jarang', 
                                'Penjualan sangat sering', 'Penjualan lumayan']

            # label encoding untuk setiap kolom
            for col in categorical_cols:
                if col in encoder_dict:
                    new_dataframe1[col] = encoder_dict[col].transform(new_dataframe1[col])
                else:
                    st.warning(f"Encoder untuk kolom {col} tidak ditemukan.")
            
            # Lakukan prediksi
            y_pred = model_rf.predict(new_dataframe1)

            # Membuat df_results dengan kolom yang diinginkan
            df_results = new_dataframe[['Kode', 'Nama', 'Satuan', 'Bulan', 'Tahun', 'salesprice1', 'is_holiday', 
                                        'Tanggal', 'Awal_Ramadhan', 'Hari_Raya_Idul_Fitri']]
            df_results['Jumlah_Penjualan_Predicted'] = y_pred  

            # Tampilkan hasil prediksi
            st.write(df_results)
            # Visualisasi Barplot untuk 20 prediksi tertinggi
            # Visualisasi Barplot untuk 20 prediksi tertinggi
            top_20 = df_results.nlargest(20, 'Jumlah_Penjualan_Predicted')
            st.subheader("Grafik Prediksi 20 Tertinggi")
            plt.figure(figsize=(12, 8))  # Sesuaikan ukuran gambar untuk barplot lebih besar
            sns.barplot(data=top_20, x='Jumlah_Penjualan_Predicted', y='Nama', palette='viridis')
            plt.title('20 Prediksi Tertinggi Jumlah Penjualan')
            plt.xlabel('Jumlah Penjualan Predicted')
            plt.ylabel('Nama Produk')
            plt.xticks(rotation=45, ha='right')  # Putar label sumbu X untuk visibilitas yang lebih baik
            plt.tight_layout()
            st.pyplot(plt)

    elif action == "Prediksi produk tertentu":
        st.subheader("Masukan Data")
        def get_kode_and_kategori(nama, df):
            row = df[df['Nama'] == nama].iloc[0]
            return row['Kode'], row['Penjualan sangat jarang'],row['Penjualan Sering'],row['Penjualan jarang'],row['Penjualan sangat sering'],row['Penjualan lumayan']
        
        nama_options = df['Nama'].unique()
        input_nama = st.selectbox('Nama:', nama_options)
        
        sat_options = df['Satuan'].unique()
        input_sat = st.selectbox('Satuan:', sat_options)
        
        selected_month = st.selectbox('Bulan:', range(1, 13))
        selected_year = st.selectbox('Tahun:', range(2022, 2025))
        
        input_salesprice = st.number_input('Sales Price 1:', min_value=0, format='%d')
        input_is_holiday = st.checkbox('Apakah ada event?')
        input_date = datetime(selected_year, selected_month, 1)
        input_ramadhan = st.checkbox('Apakah awal Ramadhan?')
        input_raya = st.checkbox('Apakah Hari Raya Idul Fitri?')

        if st.button('Prediksi'):
            # Get Kode and kategori_produk based on Nama
            kode,Penjualan_sangat_jarang,Penjualan_Sering,Penjualan_jarang, Penjualan_sangat_sering, Penjualan_lumayan = get_kode_and_kategori(input_nama, df)
            
            # Create a dataframe with the user input and additional columns
            pred_df = pd.DataFrame({
                'Kode': [kode],
                'Nama': [input_nama],
                'Satuan': [input_sat],
                'Bulan': [selected_month],
                'Tahun': [selected_year],
                'salesprice1': [input_salesprice],
                'is_holiday': [input_is_holiday],
                'Tanggal': [input_date],
                'Awal_Ramadhan': [input_ramadhan],
                'Hari_Raya_Idul_Fitri': [input_raya],
                'Penjualan sangat jarang': [Penjualan_sangat_jarang],
                'Penjualan Sering':[Penjualan_Sering],
                'Penjualan jarang':[Penjualan_jarang],
                'Penjualan sangat sering':[Penjualan_sangat_sering],
                'Penjualan lumayan':[Penjualan_lumayan]
            })

            # Ensure columns are in desired order
            desired_columns = ['Kode', 'Nama', 'Satuan', 'Bulan', 'Tahun', 'salesprice1', 'is_holiday',
                            'Tanggal', 'Awal_Ramadhan', 'Hari_Raya_Idul_Fitri', 'Penjualan Sering',
                            'Penjualan jarang', 'Penjualan lumayan', 'Penjualan sangat jarang',
                            'Penjualan sangat sering']
            pred_df = pred_df.reindex(columns=desired_columns)

            # Convert date to months since a base date
            pred_df['Tanggal'] = pd.to_datetime(pred_df['Tanggal']).apply(encode_month)

            # Encode categorical columns
            categorical_cols = ['Kode','Nama','Satuan','is_holiday','Awal_Ramadhan','Hari_Raya_Idul_Fitri','Penjualan sangat jarang','Penjualan Sering','Penjualan jarang','Penjualan sangat sering','Penjualan lumayan']
            for col in categorical_cols:
                if col in encoder_dict:
                    pred_df[col] = encoder_dict[col].transform(pred_df[col])
            # Perform prediction
            y_pred = model_rf.predict(pred_df)

            # Prepare results dataframe
            pred_df['Jumlah_Penjualan_Predicted'] = y_pred  

            # Show predicted results
            st.write("Hasil Prediksi:")
            st.write(pred_df['Jumlah_Penjualan_Predicted'])  



     
