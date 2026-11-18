"""main.py : inisialisasi FastAPI dan registrasi router."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

import database
from routes import resource, transaction


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dijalankan sekali saat server (tiap worker) start: siapkan tabel
    await database.init_db()
    yield


app = FastAPI(title="API Toko Buku - UTS Komputasi Paralel", lifespan=lifespan)

app.include_router(resource.router)
app.include_router(transaction.router)


@app.get("/", tags=["Root"])
async def root():
    return {"message": "API Toko Buku berjalan. Buka /docs untuk Swagger UI."}
