import streamlit as st
import pandas as pd
import plotly.express as px
import joblib


kmeans_penjualan = joblib.load('kmeans_penjualan.pkl')

def show_dashboard(df):
    df['kategori_produk'] = kmeans_penjualan.fit_predict(df[['Jumlah']])
    # Menambahkan kolom baru dengan label kategori produk
    cluster_labels = {0: 'Penjualan baik', 1: 'Penjualan sangat baik', 2: 'Penjualan lemah', 3: 'Penjualan cukup baik'}
    df['kategori_produk'] = df['kategori_produk'].map(cluster_labels)
    st.title("Selamat Datang di Dashboard Penjualan ZulToys!")
    
    # Define date range from DataFrame
    min_date = df['Tanggal'].min().date()
    max_date = df['Tanggal'].max().date()

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
        filtered_df = df[(df['Tanggal'].dt.date >= start_date) & (df['Tanggal'].dt.date <= end_date)]
        st.write(f"Menampilkan data dari {start_date} sampai {end_date}")
        st.write(filtered_df)

        st.header('Visualisasi Data')

        # Layout kolom untuk menampilkan dua visualisasi berdampingan
        col1, col2 = st.columns(2)
        
        # Visualisasi 1: Penjualan per Bulan per Kategori menggunakan Plotly Express
        with col1:
            penjualan_per_bulan_perkategori = filtered_df.groupby(['Tanggal', 'kategori_produk'])['Jumlah'].sum().reset_index()
            fig1 = px.bar(penjualan_per_bulan_perkategori, x='Tanggal', y='Jumlah', color='kategori_produk',
                          labels={'Tanggal': 'Bulan', 'Jumlah': 'Jumlah Penjualan'},
                          title='Total Penjualan per Bulan per Kategori')
            st.plotly_chart(fig1)

        # Visualisasi 2: Total Penjualan per Bulan menggunakan Plotly Express
        with col2:
            penjualan_per_bulan = filtered_df.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig2 = px.line(penjualan_per_bulan, x='Tanggal', y='Jumlah', title='Total Penjualan per Bulan')
            st.plotly_chart(fig2)

        # Visualisasi penjualan mainan terlaris
        penjualan_mainan_terlaris = filtered_df.groupby('Nama')['Jumlah'].sum().reset_index()
        mainan_terlaris_20 = penjualan_mainan_terlaris.nlargest(20, 'Jumlah')
        fig_mainan_terlaris = px.bar(mainan_terlaris_20, x='Nama', y='Jumlah', title='Top 20 Mainan Terlaris',
                                     labels={'Nama': 'Nama Mainan', 'Jumlah': 'Total Penjualan'})
        st.plotly_chart(fig_mainan_terlaris)

        # List nama mainan terlaris untuk multi-select box
        list_nama_mainan = df['Nama'].unique().tolist()
        # Multi-select box untuk memilih nama mainan
        selected_mainan = st.multiselect('Pilih Nama Mainan', list_nama_mainan)
        # Filter DataFrame berdasarkan pilihan nama mainan
        df_selected_mainan = df[df['Nama'].isin(selected_mainan)]
        # Membuat visualisasi berdasarkan pilihan nama mainan
        fig_selected_mainan = px.line(df_selected_mainan, x='Tanggal', y='Jumlah', color='Nama',
                                      hover_data={'Jumlah': True, 'Nama': False},
                                      title='Penjualan Mainan Terpilih')
        st.plotly_chart(fig_selected_mainan)
