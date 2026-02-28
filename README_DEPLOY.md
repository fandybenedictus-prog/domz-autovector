# Panduan Deployment Otomatis ke Google Cloud Platform (GCP)

Script `deploy_gcp.ps1` dibuat untuk mempermudah Anda mendeploy AutoVektor ke internet secara langsung.

## Persiapan
1. **Buat Akun Google Cloud**: Jika belum, daftar di [cloud.google.com](https://cloud.google.com/) dan pastikan *Billing* (Kartu Kredit/Debit) sudah aktif. Google memberikan gratis percobaan $300.
2. **Buat Project**: Di console GCP, buat sebuah Project baru. Catat **Project ID**-nya (misalnya: `my-super-app-123`).
3. **Install Gcloud CLI**: Download dan install tools resminya di komputer Anda via [Halaman Resmi Ini](https://cloud.google.com/sdk/docs/install).

## Cara Menjalankan
1. Buka **PowerShell** dari Windows Anda. Lakukan login ke akun google cloud CLI dengan menjalankan perintah lokasi absolut ini:
   ```powershell
   & "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" auth login
   ```
   *Note: Ini akan membuka browser untuk login akun email Anda.*
   
2. Pindah (_cd_) ke folder project ini.
   ```powershell
   cd "C:\Users\ThinkPad T14\Documents\Image Tracer"
   ```

3. Jalankan script otomatis:
   ```powershell
   .\deploy_gcp.ps1
   ```
   > **Note:** Jika muncul error `cannot be loaded because running scripts is disabled on this system`, jalankan dulu command ini:
   > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` lalu ulangi poin 3.

4. Script akan meminta **Project ID** Anda. Ketik dan tekan Enter.
5. Selesai! Tunggu beberapa menit, dan script akan memberikan Anda Link URL Aplikasi Anda.

## Konfigurasi Database (Wajib untuk Produksi)
Secara bawaan, jika aplikasi berada di Cloud, file *database* (`db.sqlite3`) akan terus mereset setiap beberapa jam. Anda harus menggunakan **Google Cloud SQL (PostgreSQL)**.

1. Buka [Google Cloud SQL Console](https://console.cloud.google.com/sql).
2. Buat Instance PostgreSQL.
3. Buat database baru (misal: `autovektor_db`) dan user (misal: `postgres` dan password rahasia).
4. Dapatkan format *Connection String* berikut:
   `postgres://<USER>:<PASSWORD>@<PUBLIC_IP>:5432/<DATABASE_NAME>`
5. Buka [Google Cloud Run Console](https://console.cloud.google.com/run). Pilih aplikasi Anda -> Klik **Edit & Deploy New Revision**.
6. Masuk ke tab **Variables & Secrets**, tambah *Environment Variable* baru:
   - Name: `DATABASE_URL`
   - Value: (Connection String pada langkah 4)
7. Simpan (Deploy)! Aplikasi Anda kini 100% menggunakan database solid.
