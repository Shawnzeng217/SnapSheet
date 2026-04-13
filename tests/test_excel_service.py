"""
Tests for Excel generation service
"""
import os
import pytest
from app.services.excel_service import ExcelService
from app.models import OCRResult, OCRResultItem


@pytest.fixture
def excel_service():
    return ExcelService()


@pytest.fixture
def sample_ocr_result():
    return OCRResult(
        task_id="test-001",
        items=[
            OCRResultItem(field_name="room", value="301", confidence=0.95),
            OCRResultItem(field_name="status", value="已清洁", confidence=0.88),
            OCRResultItem(field_name="inspector", value="张三", confidence=0.92),
        ],
        raw_text="301\n已清洁\n张三",
    )


@pytest.mark.asyncio
async def test_generate_data_only(excel_service, sample_ocr_result):
    path = await excel_service.generate(sample_ocr_result, output_mode="data_only")
    assert path.endswith(".xlsx")
    assert os.path.exists(path)
    os.remove(path)


@pytest.mark.asyncio
async def test_generate_template_restore_fallback(excel_service, sample_ocr_result):
    """Without a template, should fallback to data_only"""
    path = await excel_service.generate(
        sample_ocr_result, template_id="nonexistent", output_mode="template_restore"
    )
    assert path.endswith(".xlsx")
    assert os.path.exists(path)
    os.remove(path)
