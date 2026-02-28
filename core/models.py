"""
Core app – Database Models

• UserProfile  : profil user dengan saldo deposit
• TopUpTransaction : pencatatan request top-up saldo
• TraceJob     : pencatatan setiap job konversi gambar → SVG
"""

from django.db import models
from django.contrib.auth.models import User


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------
class UserProfile(models.Model):
    """
    Profil tambahan untuk tiap user.
    Dibuat otomatis melalui signal post_save pada User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Saldo disimpan sebagai integer (Rupiah bulat, bukan pecahan desimal)
    saldo = models.IntegerField(default=0)

    def __str__(self):
        return f"Profil {self.user.username} – Saldo: Rp{self.saldo:,}"


# ---------------------------------------------------------------------------
# TopUpTransaction
# ---------------------------------------------------------------------------
class TopUpTransaction(models.Model):
    """
    Setiap kali user ingin menambah saldo, mereka mengisi nominal
    dan meng-upload bukti transfer. Admin memverifikasi secara manual
    melalui halaman Django Admin → saldo user otomatis bertambah.
    """
    STATUS_CHOICES = [
        ('pending',  'Menunggu Verifikasi'),
        ('verified', 'Terverifikasi'),
        ('rejected', 'Ditolak'),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topup_transactions')
    nominal         = models.IntegerField(help_text='Jumlah saldo yang ingin ditambahkan (Rupiah)')
    bukti_transfer  = models.ImageField(upload_to='buktibayar/', help_text='Screenshot/foto bukti transfer')
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tanggal         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Top-Up Transaction'
        verbose_name_plural = 'Top-Up Transactions'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.user.username} – Rp{self.nominal:,} ({self.tanggal:%d %b %Y})"


# ---------------------------------------------------------------------------
# TraceJob
# ---------------------------------------------------------------------------
class TraceJob(models.Model):
    """
    Setiap kali user meng-upload gambar untuk dikonversi ke SVG,
    sebuah TraceJob dibuat. File SVG baru bisa diunduh setelah
    user membayar Rp2.000 (is_paid=True).
    """
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trace_jobs')
    gambar_asli  = models.ImageField(upload_to='uploads/')
    file_vektor  = models.FileField(upload_to='vektor_output/', blank=True, null=True)
    is_paid      = models.BooleanField(default=False)
    tanggal      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Trace Job'
        verbose_name_plural = 'Trace Jobs'

    def __str__(self):
        status = "✅ Dibayar" if self.is_paid else "⏳ Belum Dibayar"
        return f"{status} – {self.user.username} ({self.tanggal:%d %b %Y %H:%M})"
