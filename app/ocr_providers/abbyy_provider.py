"""
ABBYY Cloud OCR Provider
https://www.abbyy.com/cloud-ocr-sdk/
"""
import httpx
import time
import xml.etree.ElementTree as ET
from app.ocr_providers.base import OCRProvider, OCRResponse, OCRField
from app.config import settings


class ABBYYProvider(OCRProvider):
    """ABBYY Cloud OCR实现"""

    def _get_auth(self) -> tuple:
        return (settings.abbyy_app_id, settings.abbyy_password)

    async def recognize_image(self, image_path: str, language: str = "auto") -> OCRResponse:
        """通用文字识别"""
        lang_map = {"zh": "ChinesePRC", "en": "English", "mixed": "ChinesePRC,English", "auto": "ChinesePRC,English"}
        abbyy_lang = lang_map.get(language, "ChinesePRC,English")

        with open(image_path, "rb") as f:
            image_data = f.read()

        async with httpx.AsyncClient(timeout=120) as client:
            # Submit task
            resp = await client.post(
                f"{settings.abbyy_service_url}/v2/processImage",
                auth=self._get_auth(),
                params={"language": abbyy_lang, "exportFormat": "xml"},
                content=image_data,
                headers={"Content-Type": "application/octet-stream"},
            )
            resp.raise_for_status()
            task = resp.json()
            task_id = task.get("taskId")

            # Poll for result
            result_url = await self._wait_for_result(client, task_id)

            # Download result
            result_resp = await client.get(result_url, auth=self._get_auth())
            result_resp.raise_for_status()

        return self._parse_xml_response(result_resp.text)

    async def recognize_table(self, image_path: str, language: str = "auto") -> OCRResponse:
        """表格识别 - ABBYY uses same endpoint with table export"""
        lang_map = {"zh": "ChinesePRC", "en": "English", "mixed": "ChinesePRC,English", "auto": "ChinesePRC,English"}
        abbyy_lang = lang_map.get(language, "ChinesePRC,English")

        with open(image_path, "rb") as f:
            image_data = f.read()

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.abbyy_service_url}/v2/processImage",
                auth=self._get_auth(),
                params={"language": abbyy_lang, "exportFormat": "xlsx"},
                content=image_data,
                headers={"Content-Type": "application/octet-stream"},
            )
            resp.raise_for_status()
            task = resp.json()
            task_id = task.get("taskId")

            result_url = await self._wait_for_result(client, task_id)

            # For table mode, return raw_text summary
            result_resp = await client.get(result_url, auth=self._get_auth())
            result_resp.raise_for_status()

        return OCRResponse(fields=[], raw_text="[ABBYY table result - xlsx binary]")

    async def _wait_for_result(self, client: httpx.AsyncClient, task_id: str) -> str:
        """轮询等待ABBYY处理完成"""
        import asyncio

        for _ in range(60):
            resp = await client.get(
                f"{settings.abbyy_service_url}/v2/getTaskStatus",
                auth=self._get_auth(),
                params={"taskId": task_id},
            )
            resp.raise_for_status()
            status = resp.json()

            if status.get("status") == "Completed":
                return status.get("resultUrls", [""])[0]
            elif status.get("status") in ("ProcessingFailed", "NotEnoughCredits"):
                raise RuntimeError(f"ABBYY task failed: {status.get('status')}")

            await asyncio.sleep(2)

        raise TimeoutError("ABBYY OCR task timed out")

    def _parse_xml_response(self, xml_text: str) -> OCRResponse:
        """解析ABBYY XML响应"""
        fields = []
        raw_lines = []

        try:
            root = ET.fromstring(xml_text)
            ns = {"a": "http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml"}

            for line in root.iter("{%s}line" % ns["a"]):
                text_parts = []
                for char_params in line.iter("{%s}charParams" % ns["a"]):
                    text_parts.append(char_params.text or "")
                line_text = "".join(text_parts).strip()
                if line_text:
                    fields.append(OCRField(text=line_text, confidence=0.9))
                    raw_lines.append(line_text)
        except ET.ParseError:
            raw_lines.append(xml_text[:500])

        return OCRResponse(fields=fields, raw_text="\n".join(raw_lines))
