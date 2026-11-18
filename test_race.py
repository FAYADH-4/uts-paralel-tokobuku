"""
test_race.py : uji race condition.
Reset stok buku id=1 menjadi 1, kirim 2 request serentak, lalu tampilkan stok akhir.
Jalankan server dulu (terminal 1), lalu: python test_race.py (terminal 2)
"""
import asyncio
import httpx

BASE = "http://127.0.0.1:8000"


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # Reset stok buku 1 menjadi 1
        buku = (await client.get(f"{BASE}/books/1")).json()
        buku.pop("id")
        buku["stok"] = 1
        await client.put(f"{BASE}/books/1", json=buku)
        print("Stok awal buku 1 di-reset menjadi 1\n")

        payload = {"item_id": 1, "qty": 1}
        # Dua request dikirim serentak
        res1, res2 = await asyncio.gather(
            client.post(f"{BASE}/transactions", json=payload),
            client.post(f"{BASE}/transactions", json=payload),
        )
        print("Respon Request 1:", res1.status_code, res1.json())
        print("Respon Request 2:", res2.status_code, res2.json())

        akhir = (await client.get(f"{BASE}/books/1")).json()
        print("\nStok akhir buku 1:", akhir["stok"])


if __name__ == "__main__":
    asyncio.run(main())
