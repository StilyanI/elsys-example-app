# locustfile.py
from locust import HttpUser, task, between
import io
import random
import string

class FileStorageUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.uploaded_filename = None

    @task(1)
    def get_root(self):
        with self.client.get("/", name="GET /") as resp:
            if resp.status_code != 200:
                resp.failure(f"Root endpoint failed: {resp.status_code}")
            else:
                resp.success()

    @task(2)
    def post_file(self):
        fname = "locust_" + "".join(random.choices(string.ascii_lowercase, k=5)) + ".txt"
        content = b"Hello Locust " + "".join(random.choices(string.ascii_letters, k=20)).encode("utf-8")
        files = {"file": (fname, io.BytesIO(content), "text/plain")}
        with self.client.post("/files", files=files, name="POST /files") as resp:
            if resp.status_code != 200:
                resp.failure(f"Upload failed: {resp.status_code} – {resp.text}")
            else:
                json = resp.json()
                self.uploaded_filename = json.get("filename")
                resp.success()


    @task(2)
    def get_files_list(self):
        with self.client.get("/files", name="GET /files") as resp:
            if resp.status_code != 200:
                resp.failure(f"List files failed: {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def get_uploaded_file(self):
        if not self.uploaded_filename:
            return
        url = f"/files/{self.uploaded_filename}"
        with self.client.get(url, name="GET /files/[filename]") as resp:
            if resp.status_code != 200:
                resp.failure(f"Get file failed: {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def get_metrics(self):
        with self.client.get("/metrics", name="GET /metrics") as resp:
            if resp.status_code != 200:
                resp.failure(f"Metrics failed: {resp.status_code}")
            else:
                resp.success()
