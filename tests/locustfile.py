from locust import HttpUser, task, between
import io
import random


class FileStorageUser(HttpUser):
    wait_time = between(1, 3)

    @task(2)
    def list_files(self):
        self.client.get("/files")

    @task(2)
    def upload_file(self):
        filename = f"test_{random.randint(1, 10000)}.txt"
        content = f"Hello from Locust {filename}".encode("utf-8")

        self.client.post(
            "/files",
            files={"file": (filename, io.BytesIO(content), "text/plain")}
        )

    @task(1)
    def get_random_file(self):
        res = self.client.get("/files")
        if res.status_code == 200:
            files = res.json().get("files", [])
            if files:
                random_file = random.choice(files)
                self.client.get(f"/files/{random_file}")

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def metrics(self):
        self.client.get("/metrics")