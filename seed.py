"""seed.py : isi data awal (12 buku). Jalankan: python seed.py"""
import asyncio
import database as db

BUKU = [
    ("Laskar Pelangi", "Andrea Hirata", "Novel", 85000, 500),
    ("Bumi Manusia", "Pramoedya Ananta Toer", "Novel", 110000, 500),
    ("Filosofi Teras", "Henry Manampiring", "Self-help", 98000, 500),
    ("Atomic Habits", "James Clear", "Self-help", 120000, 500),
    ("Clean Code", "Robert C. Martin", "Teknologi", 350000, 500),
    ("Python Crash Course", "Eric Matthes", "Teknologi", 280000, 500),
    ("Sapiens", "Yuval Noah Harari", "Sejarah", 135000, 500),
    ("Negeri 5 Menara", "Ahmad Fuadi", "Novel", 79000, 500),
    ("Rich Dad Poor Dad", "Robert Kiyosaki", "Bisnis", 95000, 500),
    ("Dilan 1990", "Pidi Baiq", "Novel", 69000, 500),
    ("Cantik Itu Luka", "Eka Kurniawan", "Novel", 99000, 500),
    ("Sistem Terdistribusi", "Andrew Tanenbaum", "Teknologi", 420000, 500),
]


async def main():
    await db.init_db()
    if await db.list_books(0, 1):
        print("Data sudah ada, seed dilewati. (Hapus toko_buku.db untuk reset total)")
        return
    for b in BUKU:
        await db.insert_book(*b)
    print(f"Berhasil memasukkan {len(BUKU)} buku.")


if __name__ == "__main__":
    asyncio.run(main())
