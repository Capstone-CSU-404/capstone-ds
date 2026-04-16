import streamlit as st 
 
st.write(
    """
    # My first app
    Hello, para calon praktisi data masa depan!
    """
)
import pandas as pd
# Menambahkan teks dengan format berbeda
st.markdown("## Selamat Belajar Streamlit! 🎉")

# Menampilkan angka
st.number_input("Masukkan angka favorit Anda:", min_value=0, max_value=100)

# Tombol
if st.button("Klik Saya"):
    st.write("Halo! Terima kasih sudah klik tombolnya! 👋")

# Slider
usia = st.slider("Pilih usia Anda:", 0, 100, 25)
st.write(f"Usia Anda: {usia} tahun")

# Checkbox
if st.checkbox("Tampilkan pesan rahasia"):
    st.success("Anda menemukan pesan rahasia! ✨")

# Pilihan dropdown
opsi = st.selectbox(
    "Pilih warna favorit:",
    ["Merah", "Biru", "Hijau", "Kuning"]
)
st.write(f"Warna favorit Anda: {opsi}")

# Menampilkan data dalam bentuk tabel
import pandas as pd
data = {
    'Nama': ['Andi', 'Budi', 'Citra'],
    'Nilai': [85, 90, 88]
}
df = pd.DataFrame(data)
st.write("### Data Nilai Siswa")
st.dataframe(df)

# Membuat grafik sederhana
import numpy as np
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)
st.line_chart(chart_data)