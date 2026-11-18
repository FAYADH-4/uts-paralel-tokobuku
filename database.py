"""
database.py : koneksi aiosqlite + inisialisasi tabel + semua query.

Semua operasi DB memakai aiosqlite (async / non-blocking), jadi event loop
tidak terblokir saat menunggu I/O disk.
"""
import os
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toko_buku.db")

# CATATAN: kolom stok SENGAJA tanpa CHECK (stok >= 0).
# Alasannya: pada Tahap 1 pengujian (tanpa lock) kita ingin melihat stok
# benar-benar menjadi negatif (overselling). Jika ada CHECK, DB akan menolak
# dan race condition tidak terlihat. Pada versi dengan lock, stok tidak
# akan pernah negatif karena dijaga oleh logika aplikasi.
CREATE_BOOKS_TABLE = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    penulis TEXT NOT NULL,
    kategori TEXT NOT NULL,
    harga REAL NOT NULL,
    stok INTEGER NOT NULL
);
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    qty INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def connect():
    # timeout=30 : kalau DB sedang dikunci proses lain (multi-worker),
    # tunggu sampai 30 detik, jangan langsung error "database is locked".
    return aiosqlite.connect(DB_PATH, timeout=30)


async def init_db():
    async with connect() as db:
        # WAL = pembaca dan penulis tidak saling memblokir (lebih baik utk multi-worker)
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute(CREATE_BOOKS_TABLE)
        await db.execute(CREATE_TRANSACTIONS_TABLE)
        await db.commit()


# ---------------------------------------------------------------- BOOKS
async def list_books(skip: int, limit: int):
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM books ORDER BY id LIMIT ? OFFSET ?", (limit, skip)
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_book(book_id: int):
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def insert_book(judul, penulis, kategori, harga, stok) -> int:
    async with connect() as db:
        cur = await db.execute(
            "INSERT INTO books (judul, penulis, kategori, harga, stok) VALUES (?,?,?,?,?)",
            (judul, penulis, kategori, harga, stok),
        )
        await db.commit()
        return cur.lastrowid


async def update_book(book_id, judul, penulis, kategori, harga, stok) -> bool:
    async with connect() as db:
        cur = await db.execute(
            "UPDATE books SET judul=?, penulis=?, kategori=?, harga=?, stok=? WHERE id=?",
            (judul, penulis, kategori, harga, stok, book_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def delete_book(book_id: int) -> bool:
    # Hard delete: baris benar-benar dihapus dari tabel
    async with connect() as db:
        cur = await db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        await db.commit()
        return cur.rowcount > 0


# ---------------------------------------------------------------- STOK
async def get_stok(item_id: int):
    async with connect() as db:
        cur = await db.execute("SELECT stok FROM books WHERE id = ?", (item_id,))
        row = await cur.fetchone()
        return row[0] if row else None


async def decrement_stok(item_id: int, qty: int):
    """Kurangi stok tanpa pengecekan (dipakai versi TANPA lock)."""
    async with connect() as db:
        await db.execute("UPDATE books SET stok = stok - ? WHERE id = ?", (qty, item_id))
        await db.commit()


async def decrement_stok_atomic(item_id: int, qty: int) -> bool:
    """
    Kurangi stok hanya jika stok masih cukup, dalam SATU statement SQL.
    Dipakai versi DENGAN lock sebagai lapis pengaman kedua (berguna saat
    multi-worker, karena asyncio.Lock hanya berlaku di dalam satu proses).
    """
    async with connect() as db:
        cur = await db.execute(
            "UPDATE books SET stok = stok - ? WHERE id = ? AND stok >= ?",
            (qty, item_id, qty),
        )
        await db.commit()
        return cur.rowcount > 0


async def increment_stok(item_id: int, qty: int):
    async with connect() as db:
        await db.execute("UPDATE books SET stok = stok + ? WHERE id = ?", (qty, item_id))
        await db.commit()


# ---------------------------------------------------------------- TRANSACTIONS
async def insert_transaction(item_id: int, qty: int, status: str = "pending") -> int:
    async with connect() as db:
        cur = await db.execute(
            "INSERT INTO transactions (item_id, qty, status) VALUES (?,?,?)",
            (item_id, qty, status),
        )
        await db.commit()
        return cur.lastrowid


async def update_trx_status(trx_id: int, status: str):
    async with connect() as db:
        await db.execute("UPDATE transactions SET status=? WHERE id=?", (status, trx_id))
        await db.commit()


async def get_transaction(trx_id: int):
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM transactions WHERE id = ?", (trx_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_transactions(status, skip: int, limit: int):
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        if status:
            cur = await db.execute(
                "SELECT * FROM transactions WHERE status=? ORDER BY id DESC LIMIT ? OFFSET ?",
                (status, limit, skip),
            )
        else:
            cur = await db.execute(
                "SELECT * FROM transactions ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, skip),
            )
        return [dict(r) for r in await cur.fetchall()]
