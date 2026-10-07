from app.database.database import SessionLocal
from app.models.certificate import GenerationJob, Certificate
from app.services.certificate_generator import generate_certificate


def process_job(job_id: int, event_name: str, date: str):
    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if not job:
            return

        job.status = "processing"
        db.commit()

        certificates = db.query(Certificate).filter(
            Certificate.job_id == job_id
        ).all()

        for certificate in certificates:
            try:
                file_path = generate_certificate(
                    recipient_name=certificate.recipient_name,
                    event_name=event_name,
                    date=date,
                    certificate_id=certificate.id
                )

                certificate.status = "completed"
                certificate.file_path = file_path

                job.successful += 1

            except Exception as error:
                certificate.status = "failed"
                certificate.error_message = str(error)

                job.failed += 1

            db.commit()

        if job.failed > 0 and job.successful > 0:
            job.status = "completed_with_errors"
        elif job.failed == job.total:
            job.status = "failed"
        else:
            job.status = "completed"

        db.commit()

    except Exception:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if job:
            job.status = "failed"
            db.commit()

    finally:
        db.close()
    