"""
OCR Service / OCR识别服务
根据配置选择OCR供应商，编排识别流程
"""
import re
from app.ocr_providers.base import OCRProvider, OCRResponse
from app.models import OCRResult, OCRResultItem
from app.config import settings

# 手写符号标准化映射 / Handwriting symbol normalization rules
# OCR识别原始值 → 标准化值
_SYMBOL_NORMALIZE_MAP: list[tuple[re.Pattern, str]] = [
    # OK / 通过
    (re.compile(r"^[oO0][kK]$"), "OK"),
    (re.compile(r"^[√✓✔]$"), "✓"),
    (re.compile(r"^[Vv]$"), "✓"),
    # NG / 不合格
    (re.compile(r"^[nN][gG]$"), "NG"),
    (re.compile(r"^[×✗✘xX]$"), "✗"),
    # N/A / 未测试 (斜线、横线等)
    (re.compile(r"^[/\\]$"), "-"),
    (re.compile(r"^[—\-–]+$"), "-"),
    (re.compile(r"^[一]+$"), "-"),
]


def normalize_value(text: str) -> str:
    """
    标准化手写符号 / Normalize handwritten symbols
    OK/ok/0K/√/✓ → "OK"
    NG/×/X        → "NG"
    / \\ — -       → "N/A"
    其他           → 原样返回
    """
    stripped = text.strip()
    if not stripped:
        return ""
    for pattern, replacement in _SYMBOL_NORMALIZE_MAP:
        if pattern.match(stripped):
            return replacement
    return stripped


class OCRService:
    """OCR编排服务 - 选择供应商、调用识别、格式化结果"""

    def __init__(self):
        self._provider: OCRProvider | None = None

    @property
    def provider(self) -> OCRProvider:
        if self._provider is None:
            self._provider = self._create_provider()
        return self._provider

    def _create_provider(self) -> OCRProvider:
        """根据配置创建OCR供应商实例 / Create provider based on config"""
        name = settings.ocr_provider.lower()
        if name == "glm":
            from app.ocr_providers.glm_provider import GLMOCRProvider
            return GLMOCRProvider()
        elif name == "textin":
            from app.ocr_providers.textin_provider import TextInProvider
            return TextInProvider()
        elif name == "abbyy":
            from app.ocr_providers.abbyy_provider import ABBYYProvider
            return ABBYYProvider()
        elif name == "azure":
            from app.ocr_providers.azure_provider import AzureDocProvider
            return AzureDocProvider()
        else:
            raise ValueError(f"Unknown OCR provider: {name}")

    async def recognize(
        self,
        image_path: str,
        template_id: str | None = None,
        language: str = "auto",
    ) -> OCRResult:
        """
        执行OCR识别
        Run OCR recognition on an image
        """
        # 优先使用表格识别模式（因为输入多为表单）
        # Prefer table recognition since inputs are mostly forms
        ocr_response: OCRResponse = await self.provider.recognize_table(
            image_path=image_path,
            language=language,
        )

        # 如果表格识别结果太少，回退到通用识别
        # Fallback to general recognition if table result is sparse
        if not ocr_response.fields and not ocr_response.tables:
            ocr_response = await self.provider.recognize_image(
                image_path=image_path,
                language=language,
            )

        # 转换为统一结果格式 + 语义标准化
        items = []
        for i, field in enumerate(ocr_response.fields):
            items.append(OCRResultItem(
                field_name=f"field_{i}",
                value=normalize_value(field.text),
                confidence=field.confidence,
                position=field.bbox,
            ))

        # 对table_html中的单元格内容也做标准化
        normalized_html = [
            self._normalize_table_html(h) for h in (ocr_response.table_html or [])
        ]

        return OCRResult(
            task_id="",
            template_id=template_id,
            items=items,
            raw_text=ocr_response.raw_text,
            table_html=normalized_html,
        )

    @staticmethod
    def _normalize_table_html(html: str) -> str:
        """
        对HTML表格中 <td>/<th> 内的纯文本做符号标准化
        Normalize cell text content in HTML table

        特殊处理：tbody中的空<td>标记为 "-"（未测试/不适用）
        因为打印表单中的空白填写区如果被手写了符号（如斜杠）但OCR未识别，
        应视为"已标记但无法识别"，用 "-" 表示
        """
        # 先标准化非空单元格
        def _replace_cell(m: re.Match) -> str:
            tag = m.group(1)       # td or th
            attrs = m.group(2)     # attributes
            inner = m.group(3)     # cell content
            close = m.group(4)     # closing tag

            if "<" not in inner:
                inner = normalize_value(inner)

            return f"<{tag}{attrs}>{inner}</{close}>"

        html = re.sub(
            r"<(t[dh])([^>]*)>(.*?)</(t[dh])>",
            _replace_cell,
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # tbody中的空<td>：不做填充，保留原样
        # 因为无法区分"手写符号未识别"和"确实未填写"
        # 标准化只处理OCR实际识别出的符号文本

        return html
