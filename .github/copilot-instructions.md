# Hotel OCR Solution - Copilot Instructions

## Project Overview
A hotel property OCR solution that converts handwritten forms (printed from Excel templates) back into structured Excel files via photo capture and OCR recognition.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI
- **OCR**: Third-party SaaS (ABBYY Cloud, 合合信息/TextIn, Azure Document Intelligence)
- **Frontend**: Mobile-friendly HTML/CSS/JS (no framework, BYOD-compatible)
- **Output**: Excel (openpyxl) → SharePoint / Email
- **Deployment**: Docker

## Key Conventions
- Use Python type hints throughout
- API responses follow standard JSON format with `code`, `message`, `data` fields
- All OCR provider integrations implement a common `OCRProvider` interface
- Environment variables for all secrets and API keys
- Chinese + English bilingual comments for core business logic
