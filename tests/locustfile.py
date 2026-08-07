"""
Locust load test for the Dialo backend.
Run: locust -f tests/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s
"""

from locust import HttpUser, task, between
import random

SAMPLE_QUERIES = [
    "What is your return policy?",
    "How do I reset my password?",
    "What are your business hours?",
    "Do you offer international shipping?",
    "How can I track my order?",
    "What payment methods do you accept?",
    "How do I contact support?",
]


class DialoUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.session_id = f"loadtest-{random.randint(10000, 99999)}"

    @task(10)
    def chat(self):
        query = random.choice(SAMPLE_QUERIES)
        self.client.post(
            "/api/chat",
            json={"query": query, "session_id": self.session_id},
        )

    @task(2)
    def health(self):
        self.client.get("/api/health")

    @task(1)
    def history(self):
        self.client.get(f"/api/history/{self.session_id}")
