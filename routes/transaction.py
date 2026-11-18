"""
routes/transaction.py : endpoint transaksi + background processing + lock stok.

Alur:
  POST /transactions
    1. cek buku ada (404 kalau tidak)
    2. potong stok (dilindungi asyncio.Lock) -> 409 kalau stok tidak cukup
    3. simpan transaksi berstatus "pending"
    4. jadwalkan BackgroundTask, lalu LANGSUNG balas 202 (tanpa menunggu)
  Background worker:
    pending -> processing -> (sleep 3 dtk) -> completed / failed

Mode lock bisa diganti lewat environment variable USE_LOCK:
    USE_LOCK=1 (default) : pakai asyncio.Lock
    USE_LOCK=0           : TANPA lock (untuk demo race condition)
"""
import asyncio
import os
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

import database as db
from models import Transaction, TransactionAccepted, TransactionCreate

router = APIRouter(prefix="/transactions", tags=["Transactions"])

USE_LOCK = os.getenv("USE_LOCK", "1") != "0"

# Lock tingkat modul. asyncio.Lock bekerja di dalam SATU event loop / SATU proses:
# coroutine yang mencoba masuk saat lock dipegang akan di-suspend (bukan
# memblokir thread), lalu dilanjutkan setelah lock dilepas.
stok_lock = asyncio.Lock()


# ------------------------------------------------------------------ VERSI 1: TANPA LOCK
async def potong_stok_tanpa_lock(item_id: int, qty: int) -> bool:
    # RACE CONDITION: baca -> (jeda) -> tulis tidak atomik.
    # Dua request yang membaca stok yang sama sebelum salah satunya menulis
    # akan sama-sama lolos, sehingga stok bisa menjadi negatif (overselling).
    stok_terkini = await db.get_stok(item_id)

    # Jeda buatan: event loop pindah ke request lain di sini, membuka
    # "jendela waktu" terjadinya race condition.
    await asyncio.sleep(0.01)

    if stok_terkini is None or stok_terkini < qty:
        return False

    await db.decrement_stok(item_id, qty)
    return True


# ------------------------------------------------------------------ VERSI 2: DENGAN LOCK
async def potong_stok_dengan_lock(item_id: int, qty: int) -> bool:
    # Critical section: hanya SATU coroutine yang boleh masuk sekaligus.
    # Request kedua menunggu di sini sampai request pertama selesai
    # (baca + tulis), sehingga ia melihat stok yang sudah terbaru.
    async with stok_lock:
        stok_terkini = await db.get_stok(item_id)

        await asyncio.sleep(0.01)  # jeda yang sama, tapi kini aman

        if stok_terkini is None or stok_terkini < qty:
            return False

        # Lapis pengaman kedua: UPDATE ... WHERE stok >= qty (atomik di level DB).
        # asyncio.Lock tidak melindungi antar-PROSES (multi-worker), ini yang melindungi.
        return await db.decrement_stok_atomic(item_id, qty)


async def potong_stok(item_id: int, qty: int) -> bool:
    if USE_LOCK:
        return await potong_stok_dengan_lock(item_id, qty)
    return await potong_stok_tanpa_lock(item_id, qty)


# ------------------------------------------------------------------ BACKGROUND WORKER
async def proses_transaksi_background(trx_id: int, item_id: int, qty: int):
    """Fungsi pekerja internal (BUKAN endpoint HTTP). Berjalan setelah respon dikirim."""
    try:
        # 1. pending -> processing
        await db.update_trx_status(trx_id, "processing")

        # 2. Simulasi pekerjaan I/O (mis. pembayaran / kirim notifikasi).
        # asyncio.sleep tidak memblokir event loop, jadi request lain tetap dilayani.
        await asyncio.sleep(3)

        # 3. processing -> completed
        await db.update_trx_status(trx_id, "completed")
    except Exception:
        # Gagal: tandai failed dan kembalikan stok yang sudah dipotong
        await db.update_trx_status(trx_id, "failed")
        await db.increment_stok(item_id, qty)


# ------------------------------------------------------------------ ENDPOINT
@router.post("", response_model=TransactionAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(data: TransactionCreate, bg: BackgroundTasks):
    book = await db.get_book(data.item_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Buku tidak terdaftar")

    if not await potong_stok(data.item_id, data.qty):
        raise HTTPException(status_code=409, detail="Stok habis atau tidak mencukupi")

    trx_id = await db.insert_transaction(data.item_id, data.qty, status="pending")

    # Jadwalkan pemrosesan di latar belakang; respon langsung dikirim sekarang
    bg.add_task(proses_transaksi_background, trx_id, data.item_id, data.qty)
    return {"id": trx_id, "status": "pending", "message": "Transaksi diproses"}


@router.get("", response_model=list[Transaction])
async def list_transactions(
    status: Optional[Literal["pending", "processing", "completed", "failed"]] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return await db.list_transactions(status, skip, limit)


@router.get("/{trx_id}", response_model=Transaction)
async def get_transaction(trx_id: int):
    trx = await db.get_transaction(trx_id)
    if trx is None:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return trx
