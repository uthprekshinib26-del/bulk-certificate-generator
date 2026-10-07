import csv
import io

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.certificate import GenerationJob, Certificate
from app.schemas import GenerationRequest
from app.services.job_processor import process_job


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create a generation job using JSON
@router.post("/jobs")
def create_generation_job(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = GenerationJob(
        status="pending",
        total=len(request.recipients),
        successful=0,
        failed=0
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    for recipient in request.recipients:
        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            status="pending"
        )

        db.add(certificate)

    db.commit()

    background_tasks.add_task(
        process_job,
        job.id,
        request.event_name,
        request.date
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "total_recipients": len(request.recipients),
        "message": "Certificate generation job created successfully."
    }


# Upload CSV and create a bulk generation job
@router.post("/jobs/bulk")
async def create_bulk_job(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    contents = await file.read()

    try:
        text = contents.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))

        students = []

        for row in reader:
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()

            if name and email:
                students.append({
                    "name": name,
                    "email": email
                })

        if not students:
            raise HTTPException(
                status_code=400,
                detail="CSV contains no valid students."
            )

        job = GenerationJob(
            status="pending",
            total=len(students),
            successful=0,
            failed=0
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        for student in students:
            certificate = Certificate(
                job_id=job.id,
                recipient_name=student["name"],
                recipient_email=student["email"],
                status="pending"
            )

            db.add(certificate)

        db.commit()

        background_tasks.add_task(
            process_job,
            job.id,
            "Bulk Certificate Event",
            "07 October 2026"
        )

        return {
            "job_id": job.id,
            "status": "pending",
            "total_recipients": len(students),
            "message": "Bulk certificate job created successfully."
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV must be UTF-8 encoded."
        )


# Check job status
@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Generation job not found."
        )

    processed = job.successful + job.failed

    if job.total > 0:
        progress = int((processed / job.total) * 100)
    else:
        progress = 0

    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.total,
        "successful": job.successful,
        "failed": job.failed,
        "progress": progress
    }


# Get certificates belonging to a job
@router.get("/jobs/{job_id}/certificates")
def get_job_certificates(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Generation job not found."
        )

    certificates = db.query(Certificate).filter(
        Certificate.job_id == job_id
    ).all()

    return [
        {
            "certificate_id": certificate.id,
            "recipient_name": certificate.recipient_name,
            "recipient_email": certificate.recipient_email,
            "status": certificate.status,
            "file_path": certificate.file_path,
            "error_message": certificate.error_message
        }
        for certificate in certificates
    ]


# Download certificate
@router.get("/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    certificate = db.query(Certificate).filter(
        Certificate.id == certificate_id
    ).first()

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found."
        )

    if certificate.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Certificate is not ready for download."
        )

    return FileResponse(
        certificate.file_path,
        media_type="application/pdf",
        filename=certificate.file_path.split("\\")[-1]
    )