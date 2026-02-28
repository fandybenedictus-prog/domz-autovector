"""
Forms – AutoVektor Core App
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# ---------------------------------------------------------------------------
# Registrasi User
# ---------------------------------------------------------------------------
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tailwind-friendly class injection
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': (
                    'w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-600 '
                    'text-white placeholder-gray-400 focus:outline-none focus:border-indigo-500'
                )
            })


# ---------------------------------------------------------------------------
# Top-Up Saldo
# ---------------------------------------------------------------------------
NOMINAL_CHOICES = [
    (10_000,  'Rp10.000'),
    (20_000,  'Rp20.000'),
    (50_000,  'Rp50.000'),
    (100_000, 'Rp100.000'),
    (200_000, 'Rp200.000'),
    (500_000, 'Rp500.000'),
]

class TopUpForm(forms.Form):
    nominal = forms.ChoiceField(
        choices=NOMINAL_CHOICES,
        label='Pilih Nominal Top-Up',
        widget=forms.Select(attrs={
            'class': (
                'w-full px-4 py-2 rounded-lg bg-gray-800 border border-gray-600 '
                'text-white focus:outline-none focus:border-indigo-500'
            )
        }),
    )
    bukti_transfer = forms.ImageField(
        label='Upload Bukti Transfer (JPG/PNG)',
        widget=forms.ClearableFileInput(attrs={
            'class': 'hidden',
            'id':    'bukti-input',
            'accept': 'image/*',
        }),
    )

    def clean_nominal(self):
        # Kembalikan sebagai integer, bukan string
        return int(self.cleaned_data['nominal'])


# ---------------------------------------------------------------------------
# Upload Gambar untuk Di-Trace
# ---------------------------------------------------------------------------
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']
MAX_IMAGE_SIZE_MB = 20

class TraceUploadForm(forms.Form):
    gambar = forms.ImageField(
        label='Upload Gambar (JPG / PNG / WebP)',
        widget=forms.ClearableFileInput(attrs={
            'class':  'hidden',
            'id':     'gambar-input',
            'accept': 'image/jpeg,image/png,image/webp',
        }),
    )

    def clean_gambar(self):
        gambar = self.cleaned_data['gambar']

        # Validasi ukuran file (maks MAX_IMAGE_SIZE_MB MB)
        if gambar.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(
                f'Ukuran file maksimal adalah {MAX_IMAGE_SIZE_MB} MB.'
            )

        # Validasi tipe MIME
        content_type = getattr(gambar, 'content_type', None)
        if content_type and content_type not in ALLOWED_IMAGE_TYPES:
            raise forms.ValidationError(
                'Hanya file JPG, PNG, dan WebP yang diperbolehkan.'
            )

        return gambar
