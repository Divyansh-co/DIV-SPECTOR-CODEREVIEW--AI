import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["engineer"] == "Divyansh Mishra"

def test_get_evaluation_metrics():
    response = client.get("/api/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "precision" in data
    assert "recall" in data
    assert "f1_score" in data
    assert data["total_cases"] >= 10

def test_submit_review_job():
    payload = {
        "target_type": "local_path",
        "path_or_url": "c:/ai-code-reviewer/backend",
        "mode": "diff",
        "diff_content": """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
-def query(): pass
+def query(user):
+    cursor.execute(f"SELECT * FROM users WHERE name = '{user}'")
"""
    }
    response = client.post("/api/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
