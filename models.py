"""models.py : skema Pydantic untuk validasi request dan serialisasi response."""
from typing import Literal
from pydantic import BaseModel, Field


class BookBase(BaseModel):
    judul: str = Field(..., min_length=1, max_length=200)
    penulis: str = Field(..., min_length=1, max_length=100)
    kategori: str = Field(..., min_length=1, max_length=50)
    harga: float = Field(..., gt=0)
    stok: int = Field(..., ge=0)


class BookCreate(BookBase):
    pass


class BookUpdate(BookBase):
    pass


class Book(BookBase):
    id: int
    # Sengaja tanpa ge=0 di model respon: biar stok negatif (overselling)
    # bisa terbaca saat demo race condition tanpa lock.
    # Input (BookCreate/BookUpdate) tetap ge=0.
    stok: int


class TransactionCreate(BaseModel):
    item_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)


class Transaction(BaseModel):
    id: int
    item_id: int
    qty: int
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: str


class TransactionAccepted(BaseModel):
    id: int
    status: str
    message: str