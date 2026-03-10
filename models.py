from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import datetime

class Kolam(models.Model):
    """Model untuk kolam ternak lele"""
    UKURAN_CHOICES = [
        ('kecil', 'Kolam Kecil (2x3 m) - 500 ekor'),
        ('sedang', 'Kolam Sedang (3x4 m) - 1000 ekor'),
        ('besar', 'Kolam Besar (4x5 m) - 2000 ekor'),
    ]
    
    pemilik = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kolams')
    nama = models.CharField(max_length=100)
    ukuran = models.CharField(max_length=20, choices=UKURAN_CHOICES)
    kapasitas_maksimal = models.IntegerField(default=500)
    tanggal_dibuat = models.DateTimeField(auto_now_add=True)
    is_aktif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nama} - {self.pemilik.username}"

class SiklusBudidaya(models.Model):
    """Model untuk siklus budidaya lele"""
    TAHAP_CHOICES = [
        ('pendederan1', 'Pendederan 1 (1-3 cm)'),
        ('pendederan2', 'Pendederan 2 (3-5 cm)'),
        ('pendederan3', 'Pendederan 3 (5-8 cm)'),
        ('pembesaran', 'Pembesaran (8-12 cm)'),
    ]
    
    kolam = models.ForeignKey(Kolam, on_delete=models.CASCADE, related_name='siklus')
    tahap = models.CharField(max_length=20, choices=TAHAP_CHOICES)
    jumlah_benih = models.IntegerField(validators=[MinValueValidator(1)])
    ukuran_benih_cm = models.FloatField(help_text="Ukuran benih dalam cm")
    tanggal_mulai = models.DateField(auto_now_add=True)
    target_panen = models.DateField()
    jumlah_pakan_kg = models.FloatField(default=0)
    is_aktif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Siklus {self.tahap} - {self.jumlah_benih} ekor"

class Transaksi(models.Model):
    """Model untuk transaksi pembelian/pemjualan"""
    JENIS_CHOICES = [
        ('beli_benih', 'Beli Benih'),
        ('beli_pakan', 'Beli Pakan'),
        ('jual_lele', 'Jual Lele'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaksis')
    jenis = models.CharField(max_length=20, choices=JENIS_CHOICES)
    jumlah = models.IntegerField(help_text="Jumlah ekor atau kg pakan")
    harga_satuan = models.IntegerField(help_text="Harga per ekor/kg")
    total_harga = models.IntegerField()
    tanggal = models.DateTimeField(auto_now_add=True)
    keterangan = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.jenis} - Rp{self.total_harga}"

class ProfilUser(models.Model):
    """Profil tambahan untuk user (uang, level, dll)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    uang = models.IntegerField(default=100000)  # Modal awal Rp100.000
    level = models.IntegerField(default=1)
    pengalaman = models.IntegerField(default=0)
    total_panen = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - Rp{self.uang}"