# Bulk Certificate Generator API

A FastAPI-based application that generates participation certificates in bulk from a CSV file.

## Features

- Generate certificates for multiple recipients
- Upload recipient details using CSV
- Track certificate generation jobs
- Show generation progress
- Handle individual certificate failures
- Download generated certificates as PDF
- SQLite database for storing job and certificate information
- Automated API tests

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- ReportLab
- Pytest

## Project Structure

bulk-certificate-generator/

├── app/
│   ├── api/
│   │   └── routes.py
│   ├── database/
│   │   └── database.py
│   ├── models/
│   │   └── certificate.py
│   ├── schemas/
│   │   └── __init__.py
│   └── services/
│       ├── certificate_generator.py
│       └── job_processor.py
│
├── generated/
├── tests/
├── students.csv
├── requirements.txt
└── README.md

## Installation

Clone the repository:

```bash
git clone <git clone https://github.com/uthprekshinib26-del/bulk-certificate-generator.git>