from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.certificate_generator import generate_certificate
import app.services.job_processor as job_processor


client = TestClient(app)


# Test 1: Create a generation job
def test_create_job():
    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Workshop",
            "date": "07 October 2026",
            "recipients": [
                {
                    "name": "Test User",
                    "email": "test@example.com"
                }
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "job_id" in data
    assert data["total_recipients"] == 1


# Test 2: Invalid email should be rejected
def test_invalid_email():
    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Workshop",
            "date": "07 October 2026",
            "recipients": [
                {
                    "name": "Test User",
                    "email": "invalid-email"
                }
            ]
        }
    )

    assert response.status_code == 422


# Test 3: Job not found
def test_job_not_found():
    response = client.get("/jobs/999999")

    assert response.status_code == 404


# Test 4: Bulk CSV upload
def test_bulk_csv_upload():
    csv_content = (
        "name,email\n"
        "Test User 1,test1@example.com\n"
        "Test User 2,test2@example.com\n"
    )

    response = client.post(
        "/jobs/bulk",
        files={
            "file": (
                "test.csv",
                csv_content,
                "text/csv"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_recipients"] == 2
    assert "job_id" in data


# Test 5: Certificate generation
def test_certificate_generation():
    file_path = generate_certificate(
        recipient_name="Test User",
        event_name="Python Workshop",
        date="07 October 2026",
        certificate_id=99999
    )

    assert Path(file_path).exists()

    Path(file_path).unlink()


# Test 6: Job status and progress
def test_job_status_and_progress():
    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Workshop",
            "date": "07 October 2026",
            "recipients": [
                {
                    "name": "Progress User",
                    "email": "progress@example.com"
                }
            ]
        }
    )

    job_id = response.json()["job_id"]

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0
    assert data["progress"] == 100


# Test 7: One certificate can fail without stopping the job
def test_individual_certificate_failure(monkeypatch):

    def fake_generate_certificate(
        recipient_name,
        event_name,
        date,
        certificate_id
    ):
        if recipient_name == "Failed User":
            raise Exception("Certificate generation failed")

        return generate_certificate(
            recipient_name,
            event_name,
            date,
            certificate_id
        )

    monkeypatch.setattr(
        job_processor,
        "generate_certificate",
        fake_generate_certificate
    )

    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Workshop",
            "date": "07 October 2026",
            "recipients": [
                {
                    "name": "Successful User",
                    "email": "success@example.com"
                },
                {
                    "name": "Failed User",
                    "email": "failed@example.com"
                }
            ]
        }
    )

    job_id = response.json()["job_id"]

    response = client.get(f"/jobs/{job_id}")

    data = response.json()

    assert data["total"] == 2
    assert data["successful"] == 1
    assert data["failed"] == 1
    assert data["progress"] == 100


# Test 8: Retrieve generated certificates
def test_retrieve_certificates():
    response = client.post(
        "/jobs",
        json={
            "event_name": "Python Workshop",
            "date": "07 October 2026",
            "recipients": [
                {
                    "name": "Retrieve User",
                    "email": "retrieve@example.com"
                }
            ]
        }
    )

    job_id = response.json()["job_id"]

    response = client.get(
        f"/jobs/{job_id}/certificates"
    )

    assert response.status_code == 200

    certificates = response.json()

    assert len(certificates) == 1
    assert certificates[0]["recipient_name"] == "Retrieve User"
    assert certificates[0]["status"] == "completed"