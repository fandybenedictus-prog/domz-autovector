"""
Admin – AutoVektor Core App

Custom admin dengan action untuk verifikasi dan penolakan top-up.
Saat admin memilih "Verify", saldo user secara otomatis bertambah.
"""

from django.contrib import admin
from django.contrib import messages
from .models import UserProfile, TopUpTransaction, TraceJob


# ---------------------------------------------------------------------------
# UserProfile Admin
# ---------------------------------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'saldo')
    search_fields = ('user__username', 'user__email')
    list_editable = ('saldo',)   # Admin bisa langsung edit saldo dari list view


# ---------------------------------------------------------------------------
# TopUpTransaction Admin
# ---------------------------------------------------------------------------
def verify_topup(modeladmin, request, queryset):
    """
    Custom action: Verifikasi transaksi top-up.
    Untuk setiap transaksi yang dipilih:
      - Ubah status → 'verified'
      - Tambahkan nominal ke saldo UserProfile user terkait
    Hanya transaksi berstatus 'pending' yang diproses.
    """
    verified_count = 0
    skipped_count  = 0

    for txn in queryset:
        if txn.status == 'pending':
            # Tambah saldo
            profile = txn.user.profile
            profile.saldo += txn.nominal
            profile.save()

            # Update status transaksi
            txn.status = 'verified'
            txn.save()
            verified_count += 1
        else:
            skipped_count += 1

    if verified_count:
        modeladmin.message_user(
            request,
            f'{verified_count} transaksi berhasil diverifikasi dan saldo user telah diupdate.',
            messages.SUCCESS,
        )
    if skipped_count:
        modeladmin.message_user(
            request,
            f'{skipped_count} transaksi dilewati (bukan status pending).',
            messages.WARNING,
        )

verify_topup.short_description = '✅ Verifikasi top-up & tambah saldo user'


def reject_topup(modeladmin, request, queryset):
    """
    Custom action: Tolak transaksi top-up.
    Saldo TIDAK berubah. Hanya status yang diubah ke 'rejected'.
    """
    updated = queryset.filter(status='pending').update(status='rejected')
    modeladmin.message_user(
        request,
        f'{updated} transaksi ditolak.',
        messages.WARNING,
    )

reject_topup.short_description = '❌ Tolak top-up (tanpa ubah saldo)'


@admin.register(TopUpTransaction)
class TopUpTransactionAdmin(admin.ModelAdmin):
    list_display   = ('user', 'nominal_rupiah', 'status', 'tanggal', 'preview_bukti')
    list_filter    = ('status',)
    search_fields  = ('user__username',)
    readonly_fields = ('user', 'nominal', 'bukti_transfer', 'tanggal', 'preview_bukti')
    actions        = [verify_topup, reject_topup]

    def nominal_rupiah(self, obj):
        return f'Rp{obj.nominal:,}'
    nominal_rupiah.short_description = 'Nominal'

    def preview_bukti(self, obj):
        """Tampilkan thumbnail bukti transfer langsung di admin."""
        from django.utils.html import format_html
        if obj.bukti_transfer:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-height:80px; border-radius:4px;"/>'
                '</a>',
                obj.bukti_transfer.url,
                obj.bukti_transfer.url,
            )
        return '—'
    preview_bukti.short_description = 'Bukti Transfer'


# ---------------------------------------------------------------------------
# TraceJob Admin
# ---------------------------------------------------------------------------
@admin.register(TraceJob)
class TraceJobAdmin(admin.ModelAdmin):
    list_display  = ('user', 'tanggal', 'is_paid', 'has_vector')
    list_filter   = ('is_paid',)
    search_fields = ('user__username',)
    readonly_fields = ('user', 'gambar_asli', 'file_vektor', 'tanggal')

    def has_vector(self, obj):
        return bool(obj.file_vektor)
    has_vector.boolean = True
    has_vector.short_description = 'SVG Tersedia?'
