# Gunakan base image Python yang ringan
FROM python:3.10-slim

# Set environment variables agar output Python tidak di-buffer dan byte code tidak ditulis
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tentukan working directory di dalam container
WORKDIR /app

# Install system dependencies yang dibutuhkan oleh OpenCV, psycopg2, dsb.
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements terlebih dahulu untuk caching
COPY requirements.txt /app/

# Install dependencies Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code project ke dalam working directory container
COPY . /app/

# Jalankan collectstatic untuk mengumpulkan file statis (gunakan temp secret key)
RUN SECRET_KEY=temp-key-for-collectstatic python manage.py collectstatic --noinput

# Ekspos port 7860 (standar untuk Hugging Face Spaces)
EXPOSE 7860

# Jalankan server menggunakan gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "autovektor.wsgi:application"]
