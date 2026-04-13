"""
OCR Provider基础接口 / OCR Provider Base Interface
所有OCR供应商实现此接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OCRField:
    """OCR识别出的单个字段"""
    text: str
    confidence: float
    bbox: list[float] | None = None  # [x1, y1, x2, y2] normalized
    field_type: str = "text"  # text / number / checkbox


@dataclass
class OCRResponse:
    """OCR识别响应"""
    fields: list[OCRField]
    raw_text: str
    tables: list[list[list[str]]] | None = None  # 表格数据 rows x cols
    table_html: list[str] | None = None  # 原始HTML表格，保留合并单元格结构
    metadata: dict | None = None


class OCRProvider(ABC):
    """OCR供应商抽象基类 / Abstract base class for OCR providers"""

    @abstractmethod
    async def recognize_image(
        self,
        image_path: str,
        language: str = "auto",
    ) -> OCRResponse:
        """
        识别图片中的文字和表格
        Recognize text and tables from an image
        """
        ...

    @abstractmethod
    async def recognize_table(
        self,
        image_path: str,
        language: str = "auto",
    ) -> OCRResponse:
        """
        专门识别表格结构
        Specifically recognize table structures
        """
        ...
