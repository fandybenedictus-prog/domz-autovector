"""
Signals – auto-create UserProfile saat User baru dibuat
"""

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Buat UserProfile setiap kali objek User baru disimpan."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Pastikan UserProfile tersimpan bersama User."""
    # Guard: kalau profile belum ada (misal user ini sudah ada sebelum signals aktif)
    if hasattr(instance, 'profile'):
        instance.profile.save()
