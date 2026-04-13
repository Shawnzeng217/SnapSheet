"""
智谱GLM-OCR Provider
https://docs.bigmodel.cn/cn/guide/models/vlm/glm-ocr
API: POST https://open.bigmodel.cn/api/paas/v4/layout_parsing
"""
import base64
import re
import httpx
from app.ocr_providers.base import OCRProvider, OCRResponse, OCRField
from app.config import settings


class GLMOCRProvider(OCRProvider):
    """智谱GLM-OCR实现 - 轻量高精度文档解析"""

    API_URL = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.glm_api_key}",
            "Content-Type": "application/json",
        }

    async def _call_api(self, image_path: str) -> dict:
        """调用GLM-OCR API / Call GLM-OCR layout_parsing API"""
        with open(image_path, "rb") as f:
            image_data = f.read()
        b64 = base64.b64encode(image_data).decode("utf-8")

        # 根据文件扩展名确定mime type
        ext = image_path.rsplit(".", 1)[-1].lower()
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "pdf": "application/pdf"}
        mime = mime_map.get(ext, "image/jpeg")
        file_value = f"data:{mime};base64,{b64}"

        payload = {
            "model": "glm-ocr",
            "file": file_value,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self.API_URL, headers=self._get_headers(), json=payload)
            resp.raise_for_status()
            return resp.json()

    async def recognize_image(self, image_path: str, language: str = "auto") -> OCRResponse:
        """通用文字识别 / General text recognition"""
        result = await self._call_api(image_path)
        return self._parse_response(result)

    async def recognize_table(self, image_path: str, language: str = "auto") -> OCRResponse:
        """表格识别 - GLM-OCR同一接口支持表格 / Table recognition via same endpoint"""
        result = await self._call_api(image_path)
        return self._parse_response(result)

    def _parse_response(self, result: dict) -> OCRResponse:
        """
        解析GLM-OCR响应
        响应包含 md_results (Markdown文本) 和 layout_details (结构化布局)
        """
        fields = []
        tables: list[list[list[str]]] = []
        raw_text = result.get("md_results", "")

        # 解析 layout_details 获取结构化字段
        # layout_details 是二维数组: 外层=页, 内层=元素
        for page_elements in result.get("layout_details", []):
            for element in page_elements:
                label = element.get("label", "text")
                content = element.get("content", "")
                bbox = element.get("bbox_2d")

                if label == "table":
                    # 表格内容为HTML格式，解析为二维数组
                    table_grid = self._parse_html_table(content)
                    if table_grid:
                        tables.append(table_grid)
                        # 每个单元格也作为field
                        for row in table_grid:
                            for cell_text in row:
                                if cell_text.strip():
                                    fields.append(OCRField(
                                        text=cell_text.strip(),
                                        confidence=0.95,
                                        bbox=bbox,
                                        field_type="text",
                                    ))
                elif content.strip():
                    fields.append(OCRField(
                        text=content.strip(),
                        confidence=0.95,
                        bbox=bbox,
                        field_type="text",
                    ))

        # 收集原始HTML表格 / Collect raw HTML tables
        table_html_list: list[str] = []
        for page_elements in result.get("layout_details", []):
            for element in page_elements:
                if element.get("label") == "table":
                    table_html_list.append(element.get("content", ""))

        return OCRResponse(
            fields=fields,
            raw_text=raw_text,
            tables=tables or None,
            table_html=table_html_list or None,
        )

    @staticmethod
    def _parse_html_table(html: str) -> list[list[str]]:
        """
        简易解析HTML表格为二维数组
        Parse HTML table to 2D array
        """
        rows: list[list[str]] = []
        # 匹配 <tr>...</tr>
        tr_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
        td_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)
        tag_strip = re.compile(r"<[^>]+>")

        for tr_match in tr_pattern.finditer(html):
            row_html = tr_match.group(1)
            cells = []
            for td_match in td_pattern.finditer(row_html):
                cell_text = tag_strip.sub("", td_match.group(1)).strip()
                cells.append(cell_text)
            if cells:
                rows.append(cells)
        return rows
