"""
合合信息 TextIn OCR Provider
https://www.textin.com/
"""
import httpx
import base64
from app.ocr_providers.base import OCRProvider, OCRResponse, OCRField
from app.config import settings


class TextInProvider(OCRProvider):
    """合合信息TextIn OCR实现"""

    BASE_URL = "https://api.textin.com"

    def _get_headers(self) -> dict:
        return {
            "x-ti-app-id": settings.textin_app_id,
            "x-ti-secret-code": settings.textin_app_secret,
        }

    async def recognize_image(self, image_path: str, language: str = "auto") -> OCRResponse:
        """通用文字识别 / General text recognition"""
        with open(image_path, "rb") as f:
            image_data = f.read()

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.BASE_URL}/ai/service/v2/recognize/multipage",
                headers={**self._get_headers(), "Content-Type": "application/octet-stream"},
                content=image_data,
            )
            resp.raise_for_status()
            result = resp.json()

        return self._parse_response(result)

    async def recognize_table(self, image_path: str, language: str = "auto") -> OCRResponse:
        """表格识别 / Table recognition"""
        with open(image_path, "rb") as f:
            image_data = f.read()

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.BASE_URL}/ai/service/v2/recognize/table",
                headers={**self._get_headers(), "Content-Type": "application/octet-stream"},
                content=image_data,
            )
            resp.raise_for_status()
            result = resp.json()

        return self._parse_table_response(result)

    def _parse_response(self, result: dict) -> OCRResponse:
        """解析TextIn通用识别响应"""
        fields = []
        raw_lines = []

        pages = result.get("result", {}).get("pages", [])
        for page in pages:
            for line in page.get("lines", []):
                text = line.get("text", "")
                confidence = line.get("score", 0.0)
                position = line.get("position", [])
                bbox = None
                if position and len(position) >= 4:
                    bbox = [position[0], position[1], position[4], position[5]]

                fields.append(OCRField(text=text, confidence=confidence, bbox=bbox))
                raw_lines.append(text)

        return OCRResponse(fields=fields, raw_text="\n".join(raw_lines))

    def _parse_table_response(self, result: dict) -> OCRResponse:
        """解析TextIn表格识别响应"""
        fields = []
        tables = []
        raw_lines = []

        pages = result.get("result", {}).get("pages", [])
        for page in pages:
            for table in page.get("tables", []):
                rows_data: dict[int, dict[int, str]] = {}
                for cell in table.get("cells", []):
                    row = cell.get("row", 0)
                    col = cell.get("col", 0)
                    text = cell.get("text", "")
                    rows_data.setdefault(row, {})[col] = text
                    fields.append(OCRField(
                        text=text,
                        confidence=cell.get("score", 0.0),
                        field_type="text",
                    ))
                    raw_lines.append(text)

                if rows_data:
                    max_row = max(rows_data.keys()) + 1
                    max_col = max(max(cols.keys()) for cols in rows_data.values()) + 1
                    table_grid = [
                        [rows_data.get(r, {}).get(c, "") for c in range(max_col)]
                        for r in range(max_row)
                    ]
                    tables.append(table_grid)

        return OCRResponse(fields=fields, raw_text="\n".join(raw_lines), tables=tables)
