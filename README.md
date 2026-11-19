https://youtu.be/GANTI_DENGAN_LINK_VIDEO_UNLISTED

# API Toko Buku - UTS Komputasi Paralel dan Terdistribusi

REST API **FastAPI + SQLite (aiosqlite)** dengan transaksi asinkron (BackgroundTasks) dan pencegahan race condition (asyncio.Lock).

Nama: Fayadh Al Farisi | NIM: 201220064

Laporan: [docs/laporan_uts.pdf](docs/laporan_uts.pdf)

## Struktur Project
```
main.py                  # entry point FastAPI
database.py              # koneksi aiosqlite dan pembuatan tabel
models.py                # skema Pydantic
routes/resource.py       # CRUD buku
routes/transaction.py    # transaksi, BackgroundTasks, Lock
seed.py                  # data awal (12 buku)
test_race.py             # uji race condition
test_api.py              # uji otomatis semua endpoint
locustfile.py            # benchmark Locust
docs/                    # laporan PDF dan screenshot
```

## Instalasi
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
```
Mac/Linux: aktifkan venv dengan `source venv/bin/activate`.

## Menjalankan
```
uvicorn main:app --port 8000
```
Swagger UI: http://127.0.0.1:8000/docs

Uji semua endpoint otomatis (server harus hidup, jalankan di terminal lain):
```
python test_api.py
```

## Uji Race Condition (test_race.py)
Mode diatur lewat variabel `USE_LOCK`. Pastikan `set` dan `uvicorn` ada di terminal yang sama.

Terminal 1 (tanpa lock):
```
set USE_LOCK=0
uvicorn main:app --port 8000
```
Terminal 2:
```
python test_race.py
```
Hasil: kedua request 202, stok akhir -1 (overselling).

Ulangi dengan lock (hentikan server dengan Ctrl+C):
```
set USE_LOCK=1
uvicorn main:app --port 8000
```
Lalu `python test_race.py` lagi. Hasil: satu 202, satu 409, stok akhir 0.

PowerShell: ganti `set USE_LOCK=0` dengan `$env:USE_LOCK="0"`. Mac/Linux: `export USE_LOCK=0`.

## Benchmark (Locust)
Setiap skenario dijalankan 10 detik. Reset database sebelum tes tulis:
```
del toko_buku.db
python seed.py
```
Jalankan server dengan `--workers 1`, lalu ulangi dengan `--workers 4`:
```
set USE_LOCK=1
uvicorn main:app --workers 1 --port 8000
```
Di terminal lain:
```
locust -f locustfile.py --headless -u 20 -r 20 -t 10s --host http://127.0.0.1:8000 ReadUser
locust -f locustfile.py --headless -u 10 -r 10 -t 10s --host http://127.0.0.1:8000 WriteUser
```

Ringkasan hasil:

| Skenario | Worker | Throughput (req/s) | Rata-rata latensi (ms) |
|---|---|---|---|
| GET /books (20 user) | 1 | 1.359 | 14 |
| GET /books (20 user) | 4 | 2.240 | 7 |
| POST /transactions (10 user) | 1 | 10,34 | 922 |
| POST /transactions (10 user) | 4 | 11,92 | 398 |

Detail dan analisis ada di laporan. Screenshot ada di folder `docs/`.

## Endpoint
| Method | Path | Keterangan |
|---|---|---|
| GET | /books?skip=0&limit=10 | Daftar buku |
| GET | /books/{id} | Detail buku |
| POST | /books | Tambah buku (201) |
| PUT | /books/{id} | Perbarui buku |
| DELETE | /books/{id} | Hapus permanen |
| POST | /transactions | Buat transaksi (202, status pending) |
| GET | /transactions?status=pending | Daftar transaksi |
| GET | /transactions/{id} | Detail transaksi |