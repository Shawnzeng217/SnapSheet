from pydantic import BaseModel
from typing import Any, Optional


class APIResponse(BaseModel):
    """统一API响应格式 / Standard API response"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


class OCRResultItem(BaseModel):
    """单个识别字段 / Single recognized field"""
    field_name: str
    value: str
    confidence: float
    position: Optional[list] = None  # bounding box [x1, y1, x2, y2]


class OCRResult(BaseModel):
    """OCR识别结果 / OCR recognition result"""
    task_id: str
    template_id: Optional[str] = None
    items: list[OCRResultItem] = []
    raw_text: str = ""
    table_html: list[str] = []  # 原始HTML表格，保留colspan/rowspan结构
    output_file: Optional[str] = None


class TemplateInfo(BaseModel):
    """模板信息 / Template metadata"""
    template_id: str
    name: str
    description: str = ""
    field_count: int = 0
    languages: list[str] = ["zh", "en"]
