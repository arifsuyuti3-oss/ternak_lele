from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Kolam, SiklusBudidaya, Transaksi, ProfilUser
import datetime
import random

def home(request):
    """Halaman utama game"""
    return render(request, 'game/index.html')

def register_view(request):
    """Registrasi user baru"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password != password2:
            messages.error(request, 'Password tidak cocok')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan')
            return redirect('register')
        
        user = User.objects.create_user(username=username, password=password)
        # Buat profil user dengan modal awal
        ProfilUser.objects.create(user=user, uang=100000)
        
        # Beri kolam pertama gratis
        kolam = Kolam.objects.create(
            pemilik=user,
            nama="Kolam Pertamaku",
            ukuran='kecil',
            kapasitas_maksimal=500
        )
        
        messages.success(request, 'Registrasi berhasil! Silakan login.')
        return redirect('login')
    
    return render(request, 'game/register.html')

def login_view(request):
    """Login user"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username atau password salah')
    
    return render(request, 'game/login.html')

def logout_view(request):
    """Logout user"""
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    """Dashboard utama game"""
    profil = request.user.profil
    kolams = request.user.kolams.filter(is_aktif=True)
    
    # Hitung total lele dan siklus aktif
    total_lele = 0
    siklus_aktif = []
    for kolam in kolams:
        siklus = kolam.siklus.filter(is_aktif=True).first()
        if siklus:
            total_lele += siklus.jumlah_benih
            siklus_aktif.append(siklus)
    
    # Cek siklus yang sudah mencapai target panen
    hari_ini = timezone.now().date()
    for siklus in siklus_aktif:
        if hari_ini >= siklus.target_panen:
            messages.info(request, f'Siklus di {siklus.kolam.nama} sudah siap panen!')
    
    # Riwayat transaksi
    transaksis = request.user.transaksis.all().order_by('-tanggal')[:10]
    
    context = {
        'profil': profil,
        'kolams': kolams,
        'total_lele': total_lele,
        'siklus_aktif': siklus_aktif,
        'transaksis': transaksis,
    }
    return render(request, 'game/dashboard.html', context)

@login_required
def beli_benih(request):
    """Fitur beli benih lele"""
    if request.method == 'POST':
        kolam_id = request.POST['kolam']
        jumlah = int(request.POST['jumlah'])
        ukuran = request.POST['ukuran']
        
        kolam = get_object_or_404(Kolam, id=kolam_id, pemilik=request.user)
        
        # Cek apakah kolam sudah ada siklus aktif
        if kolam.siklus.filter(is_aktif=True).exists():
            messages.error(request, 'Kolam ini masih memiliki siklus aktif!')
            return redirect('beli_benih')
        
        # Harga benih berdasarkan ukuran (simulasi)
        if ukuran == 'kecil':
            harga_per_ekor = 200  # benih 1-3 cm
            ukuran_cm = 2
            lama_pemeliharaan = 30  # hari
        elif ukuran == 'sedang':
            harga_per_ekor = 500  # benih 3-5 cm
            ukuran_cm = 4
            lama_pemeliharaan = 20
        else:  # besar
            harga_per_ekor = 1000  # benih 5-8 cm
            ukuran_cm = 6
            lama_pemeliharaan = 15
        
        total_harga = jumlah * harga_per_ekor
        
        # Cek uang
        if request.user.profil.uang < total_harga:
            messages.error(request, 'Uang tidak cukup!')
            return redirect('beli_benih')
        
        # Buat siklus baru
        target_panen = timezone.now().date() + datetime.timedelta(days=lama_pemeliharaan)
        siklus = SiklusBudidaya.objects.create(
            kolam=kolam,
            tahap='pendederan1' if ukuran == 'kecil' else 'pendederan2' if ukuran == 'sedang' else 'pendederan3',
            jumlah_benih=jumlah,
            ukuran_benih_cm=ukuran_cm,
            target_panen=target_panen
        )
        
        # Kurangi uang
        request.user.profil.uang -= total_harga
        request.user.profil.save()
        
        # Catat transaksi
        Transaksi.objects.create(
            user=request.user,
            jenis='beli_benih',
            jumlah=jumlah,
            harga_satuan=harga_per_ekor,
            total_harga=total_harga,
            keterangan=f'Beli benih ukuran {ukuran_cm}cm untuk {kolam.nama}'
        )
        
        messages.success(request, f'Berhasil membeli {jumlah} benih lele! Target panen: {target_panen}')
        return redirect('dashboard')
    
    # GET request: tampilkan form
    kolams = request.user.kolams.filter(is_aktif=True)
    return render(request, 'game/beli_benih.html', {'kolams': kolams})

@login_required
def beri_pakan(request):
    """Fitur memberi pakan lele"""
    if request.method == 'POST':
        siklus_id = request.POST['siklus']
        jumlah_pakan = float(request.POST['jumlah_pakan'])
        
        siklus = get_object_or_404(SiklusBudidaya, id=siklus_id, kolam__pemilik=request.user, is_aktif=True)
        
        # Harga pakan per kg (simulasi)
        harga_per_kg = 10000
        total_harga = jumlah_pakan * harga_per_kg
        
        # Cek uang
        if request.user.profil.uang < total_harga:
            messages.error(request, 'Uang tidak cukup!')
            return redirect('dashboard')
        
        # Update jumlah pakan
        siklus.jumlah_pakan_kg += jumlah_pakan
        siklus.save()
        
        # Kurangi uang
        request.user.profil.uang -= total_harga
        request.user.profil.save()
        
        # Simulasi pertumbuhan (random)
        pertumbuhan = random.uniform(0.2, 0.5)
        siklus.ukuran_benih_cm += pertumbuhan
        siklus.save()
        
        # Catat transaksi
        Transaksi.objects.create(
            user=request.user,
            jenis='beli_pakan',
            jumlah=int(jumlah_pakan),
            harga_satuan=int(harga_per_kg),
            total_harga=int(total_harga),
            keterangan=f'Beli pakan {jumlah_pakan}kg untuk siklus {siklus.id}'
        )
        
        messages.success(request, f'Berhasil memberi pakan! Lele tumbuh {pertumbuhan:.1f}cm')
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def jual_lele(request):
    """Fitur menjual lele yang sudah siap panen"""
    if request.method == 'POST':
        siklus_id = request.POST['siklus']
        
        siklus = get_object_or_404(SiklusBudidaya, id=siklus_id, kolam__pemilik=request.user, is_aktif=True)
        
        hari_ini = timezone.now().date()
        if hari_ini < siklus.target_panen:
            messages.error(request, 'Lele belum mencapai ukuran panen ideal!')
            return redirect('dashboard')
        
        # Hitung hasil panen (berat per ekor berdasarkan ukuran)
        berat_per_ekor_kg = siklus.ukuran_benih_cm * 3 / 100  # konversi cm ke kg (estimasi)
        total_berat_kg = siklus.jumlah_benih * berat_per_ekor_kg
        
        # Harga jual per kg (simulasi)
        harga_per_kg = 25000
        total_pendapatan = int(total_berat_kg * harga_per_kg)
        
        # Tambah uang
        request.user.profil.uang += total_pendapatan
        request.user.profil.total_panen += 1
        request.user.profil.save()
        
        # Nonaktifkan siklus
        siklus.is_aktif = False
        siklus.save()
        
        # Catat transaksi
        Transaksi.objects.create(
            user=request.user,
            jenis='jual_lele',
            jumlah=int(siklus.jumlah_benih),
            harga_satuan=int(harga_per_kg),
            total_harga=total_pendapatan,
            keterangan=f'Panen {siklus.jumlah_benih} ekor, berat {total_berat_kg:.1f}kg'
        )
        
        messages.success(request, f'Selamat! Panen sukses. Pendapatan: Rp{total_pendapatan}')
        return redirect('dashboard')
    
    # GET request: tampilkan siklus yang siap panen
    siap_panen = []
    for kolam in request.user.kolams.filter(is_aktif=True):
        for siklus in kolam.siklus.filter(is_aktif=True):
            if timezone.now().date() >= siklus.target_panen:
                siap_panen.append(siklus)
    
    return render(request, 'game/jual_lele.html', {'siap_panen': siap_panen})

@login_required
def history(request):
    """Riwayat transaksi"""
    transaksis = request.user.transaksis.all().order_by('-tanggal')
    return render(request, 'game/history.html', {'transaksis': transaksis})