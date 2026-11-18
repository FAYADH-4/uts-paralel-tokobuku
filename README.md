https://youtu.be/GANTI_DENGAN_LINK_VIDEO_UNLISTED

# API Toko Buku - UTS Komputasi Paralel dan Terdistribusi

REST API **FastAPI + SQLite (aiosqlite)** dengan transaksi asinkron (BackgroundTasks) dan pencegahan race condition (asyncio.Lock).

Nama: GANTI_NAMA | NIM: GANTI_NIM

## Instalasi
```
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python seed.py
```

## Menjalankan
```
uvicorn main:app --port 8000
```
Swagger UI: http://127.0.0.1:8000/docs

## Uji race condition (test_race.py)
Terminal 1 (tanpa lock):
```
set USE_LOCK=0                  # PowerShell: $env:USE_LOCK="0"   | Mac/Linux: export USE_LOCK=0
uvicorn main:app --port 8000
```
Terminal 2: `python test_race.py`  -> stok akhir minus.

Ulangi dengan lock (hentikan server, hapus variabel `USE_LOCK` / set `USE_LOCK=1`):
-> satu sukses (202), satu ditolak (409).

## Benchmark
```
uvicorn main:app --workers 1 --port 8000      # lalu 4 worker: --workers 4
locust -f locustfile.py --headless -u 20 -r 20 --host http://127.0.0.1:8000 ReadUser
locust -f locustfile.py --headless -u 10 -r 10 --host http://127.0.0.1:8000 WriteUser
```

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
