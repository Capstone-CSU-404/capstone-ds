import pandas as pd
import requests
from bs4 import BeautifulSoup

url = 'https://id.jobstreet.com/id/data-scientist-jobs?sortmode=ListedDate'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.90"
}
s = requests.session()
s.headers.update(headers)

page = s.get(url)
if page.status_code == 200:
    print("Request berhasil!")
else:
    print(f"Request gagal dengan kode status: {page.status_code}")
soup = BeautifulSoup(page.text, "lxml")
joblist = soup.find('div', class_='papho0 _21bfxf1')
jobs_data = []
for artikel in joblist.find_all('article', {'class': 'papho0 papho1 _1j97a3y7i _1j97a3y6e _1j97a3y9q _1j97a3y8m _1j97a3yh _1j97a3y66 _1j97a3y5e vrt92ib vrt92i9 vrt92ia w75d4w18 w75d4w1b _1j97a3y32 _1j97a3y35'}):
    title = artikel.find('div', {'class': 'papho0 _1j97a3y5g _1j97a3y52'})
    company = artikel.find(attrs={'data-automation':'jobCompany'})
    location = artikel.find(attrs={'data-automation':'jobLocation'})
    gaji = artikel.find('span', {'class':'papho0 _15904gq2 _1j97a3y4y _1j97a3y0 _1j97a3yr _15904gq4'})
    waktu = artikel.find('span',{'class':'papho0 _1j97a3y4y w75d4w0 w75d4w1 w75d4w22 _1708b944 w75d4w7'})

posisi_text = posisi.get_text() if posisi else "Posisi tidak ditemukan"
perusahaan_text = perusahaan.get_text() if perusahaan else "Perusahaan tidak ditemukan"
lokasi_text = lokasi.get_text() if lokasi else "Lokasi tidak ditemukan"
gaji_text = gaji.get_text() if gaji else "Gaji tidak disebutkan"
waktu_text = waktu.get_text() if waktu else "Waktu tidak ditemukan"

jobs_data.append({
    "Posisi": posisi_text,
    "Perusahaan": perusahaan_text,
    "Lokasi": lokasi_text,
    "Gaji": gaji_text,
    "Waktu": waktu_text
})

jobs_data = []

for i in range(1,8):
  url = f'https://id.jobstreet.com/id/Data-Scientist-jobs?page={i}&sortmode=ListedDate'

  headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.90"
    }

  s = requests.session()
  s.headers.update(headers)

  try:
      page = s.get(url)
      soup = BeautifulSoup(page.text, "lxml")
      joblist = soup.find('div', class_='papho0 _21bfxf1')

      for artikel in joblist.find_all('article', {'class': 'papho0 papho1 _1j97a3y7i _1j97a3y6e _1j97a3y9q _1j97a3y8m _1j97a3yh _1j97a3y66 _1j97a3y5e vrt92ib vrt92i9 vrt92ia w75d4w18 w75d4w1b _1j97a3y32 _1j97a3y35'}):
          posisi = artikel.find('div', {'class' : 'papho0 _1j97a3y5g _1j97a3y52'})
          perusahaan = artikel.find(attrs={'data-automation':'jobCompany'})
          lokasi = artikel.find(attrs={'data-automation':'jobLocation'})
          gaji = artikel.find('span', {'class':'papho0 _15904gq2 _1j97a3y4y _1j97a3y0 _1j97a3yr _15904gq4'})
          waktu = artikel.find('span',{'class':'papho0 _1j97a3y4y w75d4w0 w75d4w1 w75d4w22 _1708b944 w75d4w7'})

          posisi_text = posisi.get_text() if posisi else "Posisi tidak ditemukan"
          perusahaan_text = perusahaan.get_text() if perusahaan else "Perusahaan tidak disebutkan"
          lokasi_text = lokasi.get_text() if lokasi else "Lokasi tidak ditemukan"
          gaji_text = gaji.get_text() if gaji else "Gaji tidak disebutkan"
          waktu_text = waktu.get_text() if waktu else "Waktu tidak ditemukan"

          jobs_data.append({
            "Posisi": posisi_text,
            "Perusahaan": perusahaan_text,
            "Lokasi": lokasi_text,
            "Gaji": gaji_text,
            "Waktu": waktu_text
          })

          print(posisi_text)
          # print(perusahaan_text)
          # print(lokasi_text)
          # print(gaji_text)
          # print(waktu_text)
          print("===============================")
  except requests.exceptions.RequestException as e:
      print(f"Error: {e}")

df_jobs_full = pd.DataFrame(jobs_data)

df_jobs_full.to_csv('[Jobstreet]Full_Data_Job_Listings.csv', index=False)
     
