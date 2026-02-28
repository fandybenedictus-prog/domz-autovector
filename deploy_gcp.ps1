<#
.SYNOPSIS
Script untuk mengotomatisasi deployment AutoVektor ke Google Cloud Platform (GCP).

.DESCRIPTION
Script ini akan:
1. Meminta Project ID GCP Anda
2. Mengaktifkan services (API) yang dibutuhkan
3. Membuat Google Cloud Storage bucket untuk file media Django
4. Mendeploy code ke Google Cloud Run

.PREREQUISITES
1. Google Cloud CLI (gcloud) harus sudah terinstall.
2. Anda harus sudah login (gcloud auth login).
3. Anda harus sudah membuat Project di GCP Billing-enabled.

#>

# Set agar tidak berhenti saat error karena gcloud storage ls akan mengembalikan error jika bucket belum ada
# $ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🔥 AUTOVEKTOR GCP DEPLOYMENT SCRIPT 🔥" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Cek apakah gcloud terinstall
$GCLOUD_CMD = "gcloud"
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    # Coba cari di path default instalasi Windows
    $DEFAULT_PATH = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    if (Test-Path $DEFAULT_PATH) {
        $GCLOUD_CMD = "& `"$DEFAULT_PATH`""
        Write-Host "Menggunakan gcloud dari: $DEFAULT_PATH" -ForegroundColor Cyan
    }
    else {
        Write-Host "ERROR: Google Cloud CLI (gcloud) tidak ditemukan!" -ForegroundColor Red
        Write-Host "Silahkan install dari: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
        Write-Host "Jika sudah install, pastikan Anda merestart terminal atau komputer." -ForegroundColor Yellow
        Exit
    }
}

# Fungsi bantuan untuk menjalankan gcloud
function Invoke-Gcloud {
    param([string]$ArgsString)
    Invoke-Expression "$GCLOUD_CMD $ArgsString"
}

# Minta input Project ID
$PROJECT_ID = Read-Host "Masukkan Google Cloud Project ID Anda (misal: my-autovektor-123)"
if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
    Write-Host "Project ID tidak boleh kosong. Keluar." -ForegroundColor Red
    Exit
}

Write-Host "`n[1/5] Mengatur Project ID ke: $PROJECT_ID..." -ForegroundColor Green
Invoke-Gcloud "config set project $PROJECT_ID"

Write-Host "`n[2/5] Mengaktifkan Cloud Run, Cloud Build, dan Cloud Storage API (Ini mungkin memakan waktu beberapa menit)..." -ForegroundColor Green
Invoke-Gcloud "services enable run.googleapis.com cloudbuild.googleapis.com storage.googleapis.com --project=$PROJECT_ID"

# Konfigurasi variabel
$REGION = "asia-southeast2" # Jakarta
$APP_NAME = "autovektor"

# Nama bucket disarankan unik secara global (menggunakan project id)
$BUCKET_NAME = "$PROJECT_ID-media-bucket"

# Cek apakah bucket sudah ada
Write-Host "`n[3/5] Memeriksa/Membuat Google Cloud Storage Bucket ($BUCKET_NAME)..." -ForegroundColor Green
try {
    Invoke-Expression "$GCLOUD_CMD storage ls gs://$BUCKET_NAME 2>&1" | Out-Null
}
catch {
    # Abaikan error dari PowerShell
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Bucket belum ada. Sedang membuat bucket di region $REGION..." -ForegroundColor Yellow
    Invoke-Gcloud "storage buckets create 'gs://$BUCKET_NAME' --location=$REGION --project=$PROJECT_ID"
    
    # Jadikan bucket public agar file gambar bisa diakses dari web
    Write-Host "Mengatur bucket agar public-read..." -ForegroundColor Yellow
    Invoke-Gcloud "storage buckets add-iam-policy-binding 'gs://$BUCKET_NAME' --member='allUsers' --role='roles/storage.objectViewer'"
}
else {
    Write-Host "Bucket gs://$BUCKET_NAME sudah ada. Lanjut!" -ForegroundColor Cyan
}

Write-Host "`n[4/5] Menyiapkan variabel rahasia..." -ForegroundColor Green
# Membuat secret key Django yang acak
$SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object { [char]$_ })

Write-Host "`n[5/5] Memulai Deployment ke Google Cloud Run (Proses ini akan mengunduh paket, membuild Docker, dan men-deploy) 🚀" -ForegroundColor Green
Write-Host "Harap tunggu 3-10 menit..." -ForegroundColor Yellow

# CATATAN: DATABASE_URL untuk sementara dikosongkan. 
# Jika DATABASE_URL kosong, aplikasi akan menggunakan SQLite secara otomatis.
# User harus memasukkan DATABASE_URL secara manual di panel Cloud Run nanti jika menggunakan Cloud SQL.

Invoke-Gcloud "run deploy $APP_NAME --source . --region $REGION --allow-unauthenticated --set-env-vars=`"SECRET_KEY=$SECRET_KEY,GS_BUCKET_NAME=$BUCKET_NAME,DEBUG=False,ALLOWED_HOSTS=*`""

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n================================================" -ForegroundColor Cyan
    Write-Host "✅ DEPLOYMENT BERHASIL! 🎉" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "`nLangkah Selanjutnya (Sangat Penting):" -ForegroundColor Yellow
    Write-Host "1. Buka Google Cloud Console: https://console.cloud.google.com/sql"
    Write-Host "2. Buat database PostgreSQL baru."
    Write-Host "3. Edit Service Cloud Run '$APP_NAME', dan tambahkan variabel lingkungan (Environment Variables):"
    Write-Host "   Nama Variabel: DATABASE_URL"
    Write-Host "   Value        : postgres://<user>:<password>@<public_ip_atau_socket>:5432/<nama_db>"
    Write-Host "4. Jika Anda belum menyetting database, aplikasi Anda saat ini menggunakan file SQLite *sementara* yang akan reset secara berkala."
}
else {
    Write-Host "`n❌ TERJADI KESALAHAN SAAT DEPLOYMENT!" -ForegroundColor Red
}

Write-Host "`nTekan Enter untuk keluar..."
Read-Host
