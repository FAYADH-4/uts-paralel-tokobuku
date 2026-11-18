"""
test_api.py : tes otomatis semua endpoint (smoke test).
Server harus sudah jalan. Jalankan: python test_api.py
"""
import time
import httpx

BASE = "http://127.0.0.1:8000"
c = httpx.Client(base_url=BASE, timeout=30)
gagal = 0


def cek(nama, res, harapan):
    global gagal
    ok = res.status_code == harapan
    if not ok:
        gagal += 1
    print(("OK    " if ok else "GAGAL "), f"{nama:<34} -> {res.status_code} (harusnya {harapan})")


buku = {"judul": "Buku Tes", "penulis": "Saya", "kategori": "Tes", "harga": 50000, "stok": 10}

print("=== CRUD BOOKS ===")
r = c.get("/books");                       cek("GET /books", r, 200)
r = c.get("/books?skip=0&limit=3");        cek("GET /books?skip=0&limit=3", r, 200)
print("      jumlah data dengan limit=3:", len(r.json()))
r = c.post("/books", json=buku);           cek("POST /books", r, 201)
new_id = r.json()["id"]
r = c.get(f"/books/{new_id}");             cek(f"GET /books/{new_id}", r, 200)
buku["stok"] = 20
r = c.put(f"/books/{new_id}", json=buku);  cek(f"PUT /books/{new_id}", r, 200)
print("      stok setelah PUT:", r.json()["stok"])
r = c.delete(f"/books/{new_id}");          cek(f"DELETE /books/{new_id}", r, 200)
r = c.get(f"/books/{new_id}");             cek("GET buku yang sudah dihapus", r, 404)
r = c.post("/books", json={"judul": "x"}); cek("POST /books data salah", r, 422)

print("\n=== TRANSAKSI ===")
r = c.post("/transactions", json={"item_id": 2, "qty": 1}); cek("POST /transactions", r, 202)
trx_id = r.json()["id"]
print("      status langsung:", r.json()["status"])
r = c.post("/transactions", json={"item_id": 9999, "qty": 1}); cek("POST /transactions buku tdk ada", r, 404)
r = c.post("/transactions", json={"item_id": 2, "qty": 999999}); cek("POST /transactions stok kurang", r, 409)
r = c.get(f"/transactions/{trx_id}");      cek(f"GET /transactions/{trx_id}", r, 200)
print("      status sekarang:", r.json()["status"])
print("      menunggu 4 detik...")
time.sleep(4)
r = c.get(f"/transactions/{trx_id}");      cek("GET detail setelah 4 detik", r, 200)
print("      status akhir:", r.json()["status"], "(harusnya completed)")
if r.json()["status"] != "completed":
    gagal += 1
r = c.get("/transactions?status=completed"); cek("GET /transactions?status=completed", r, 200)
r = c.get("/transactions/999999");         cek("GET transaksi tdk ada", r, 404)

print("\n" + ("SEMUA LOLOS" if gagal == 0 else f"ADA {gagal} YANG GAGAL, screenshot ke Claude"))
