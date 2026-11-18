"""routes/resource.py : endpoint CRUD untuk resource utama (books)."""
from fastapi import APIRouter, HTTPException, Query, status

import database as db
from models import Book, BookCreate, BookUpdate

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", response_model=list[Book], status_code=status.HTTP_200_OK)
async def list_books(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    # await = event loop bebas melayani request lain selagi DB bekerja
    return await db.list_books(skip, limit)


@router.get("/{book_id}", response_model=Book)
async def get_book(book_id: int):
    book = await db.get_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan")
    return book


@router.post("", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookCreate):
    new_id = await db.insert_book(data.judul, data.penulis, data.kategori, data.harga, data.stok)
    return await db.get_book(new_id)


@router.put("/{book_id}", response_model=Book)
async def update_book(book_id: int, data: BookUpdate):
    ok = await db.update_book(book_id, data.judul, data.penulis, data.kategori, data.harga, data.stok)
    if not ok:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan")
    return await db.get_book(book_id)  # kembalikan data terbaru


@router.delete("/{book_id}")
async def delete_book(book_id: int):
    ok = await db.delete_book(book_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan")
    return {"message": f"Buku {book_id} berhasil dihapus permanen"}
