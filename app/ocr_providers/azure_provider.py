"""
Azure Document Intelligence (Form Recognizer) OCR Provider
https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/
"""
import httpx
import asyncio
from app.ocr_providers.base import OCRProvider, OCRResponse, OCRField
from app.config import settings


class AzureDocProvider(OCRProvider):
    """Azure Document Intelligence OCR实现"""

    def _get_headers(self) -> dict:
        return {
            "Ocp-Apim-Subscription-Key": settings.azure_doc_key,
            "Content-Type": "application/octet-stream",
        }

    async def recognize_image(self, image_path: str, language: str = "auto") -> OCRResponse:
        """通用文字识别 - prebuilt-read model"""
        with open(image_path, "rb") as f:
            image_data = f.read()

        endpoint = settings.azure_doc_endpoint.rstrip("/")
        url = f"{endpoint}/documentintelligence/documentModels/prebuilt-read:analyze?api-version=2024-11-30"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=self._get_headers(), content=image_data)
            resp.raise_for_status()

            operation_url = resp.headers.get("Operation-Location", "")
            result = await self._poll_result(client, operation_url)

        return self._parse_read_response(result)

    async def recognize_table(self, image_path: str, language: str = "auto") -> OCRResponse:
        """表格识别 - prebuilt-layout model"""
        with open(image_path, "rb") as f:
            image_data = f.read()

        endpoint = settings.azure_doc_endpoint.rstrip("/")
        url = f"{endpoint}/documentintelligence/documentModels/prebuilt-layout:analyze?api-version=2024-11-30"

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=self._get_headers(), content=image_data)
            resp.raise_for_status()

            operation_url = resp.headers.get("Operation-Location", "")
            result = await self._poll_result(client, operation_url)

        return self._parse_layout_response(result)

    async def _poll_result(self, client: httpx.AsyncClient, operation_url: str) -> dict:
        """轮询等待Azure分析完成"""
        headers = {"Ocp-Apim-Subscription-Key": settings.azure_doc_key}

        for _ in range(60):
            resp = await client.get(operation_url, headers=headers)
            resp.raise_for_status()
            body = resp.json()

            status = body.get("status")
            if status == "succeeded":
                return body.get("analyzeResult", {})
            elif status == "failed":
                raise RuntimeError(f"Azure analysis failed: {body}")

            await asyncio.sleep(2)

        raise TimeoutError("Azure Document Intelligence timed out")

    def _parse_read_response(self, result: dict) -> OCRResponse:
        """解析Azure read模型响应"""
        fields = []
        raw_lines = []

        for page in result.get("pages", []):
            for line in page.get("lines", []):
                text = line.get("content", "")
                confidence = line.get("confidence", 0.0)
                polygon = line.get("polygon", [])
                bbox = None
                if len(polygon) >= 8:
                    bbox = [polygon[0], polygon[1], polygon[4], polygon[5]]

                fields.append(OCRField(text=text, confidence=confidence, bbox=bbox))
                raw_lines.append(text)

        return OCRResponse(fields=fields, raw_text="\n".join(raw_lines))

    def _parse_layout_response(self, result: dict) -> OCRResponse:
        """解析Azure layout模型响应（含表格）"""
        fields = []
        tables = []
        raw_lines = []

        # Extract text lines
        for page in result.get("pages", []):
            for line in page.get("lines", []):
                text = line.get("content", "")
                fields.append(OCRField(text=text, confidence=line.get("confidence", 0.0)))
                raw_lines.append(text)

        # Extract tables
        for table in result.get("tables", []):
            row_count = table.get("rowCount", 0)
            col_count = table.get("columnCount", 0)
            grid = [[""] * col_count for _ in range(row_count)]

            for cell in table.get("cells", []):
                r = cell.get("rowIndex", 0)
                c = cell.get("columnIndex", 0)
                if r < row_count and c < col_count:
                    grid[r][c] = cell.get("content", "")

            tables.append(grid)

        return OCRResponse(fields=fields, raw_text="\n".join(raw_lines), tables=tables)
