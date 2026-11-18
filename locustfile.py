"""
locustfile.py : skenario beban.
  ReadUser  : GET /books            -> berhenti otomatis setelah 100 request
  WriteUser : POST /transactions    -> berhenti otomatis setelah 50 request

Jalankan (server harus sudah hidup):
  locust -f locustfile.py --headless -u 20 -r 20 --host http://127.0.0.1:8000 ReadUser
  locust -f locustfile.py --headless -u 10 -r 10 --host http://127.0.0.1:8000 WriteUser
"""
import random
import time

from locust import HttpUser, constant, events, task

LIMITS = {"GET /books": 100, "POST /transactions": 50}
counts = {}
state = {"env": None, "start": 0.0}


@events.init.add_listener
def on_init(environment, **kwargs):
    state["env"] = environment


@events.test_start.add_listener
def on_start(environment, **kwargs):
    state["start"] = time.time()


@events.request.add_listener
def on_request(request_type, name, **kwargs):
    key = f"{request_type} {name}"
    counts[key] = counts.get(key, 0) + 1
    if key in LIMITS and counts[key] >= LIMITS[key]:
        state["env"].runner.quit()


@events.test_stop.add_listener
def on_stop(environment, **kwargs):
    print(f"\n>>> TOTAL WAKTU: {time.time() - state['start']:.2f} detik")


class ReadUser(HttpUser):
    wait_time = constant(0)

    @task
    def read_books(self):
        self.client.get("/books?skip=0&limit=10", name="GET /books")


class WriteUser(HttpUser):
    wait_time = constant(0)

    @task
    def create_trx(self):
        self.client.post(
            "/transactions",
            json={"item_id": random.randint(1, 12), "qty": 1},
            name="POST /transactions",
        )
