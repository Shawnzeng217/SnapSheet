"""
OCR识别API / OCR Recognition API
处理图片上传、OCR识别、Excel生成的核心接口
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import uuid
import os
import shutil
import logging

logger = logging.getLogger(__name__)

from app.models import APIResponse
from app.config import settings
from app.services.ocr_service import OCRService
from app.services.excel_service import ExcelService
from app.services.email_service import EmailService

router = APIRouter()
ocr_service = OCRService()
excel_service = ExcelService()
email_service = EmailService()


@router.post("/recognize", response_model=APIResponse)
async def recognize(
    image: UploadFile = File(..., description="手写表单照片 / Photo of handwritten form"),
    template_id: Optional[str] = Form(None, description="模板ID（可选）/ Template ID (optional)"),
    output_mode: str = Form("data_only", description="输出模式: data_only / template_restore"),
    language: str = Form("auto", description="语言: auto / zh / en / mixed"),
):
    """
    上传表单照片进行OCR识别并生成Excel
    Upload form photo for OCR recognition and Excel generation
    """
    task_id = str(uuid.uuid4())

    # 保存上传图片 / Save uploaded image
    upload_dir = os.path.join(settings.uploads_dir, task_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(image.filename or "photo.jpg")[1] or ".jpg"
    image_path = os.path.join(upload_dir, f"original{file_ext}")
    with open(image_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    # OCR识别 / Run OCR
    ocr_result = await ocr_service.recognize(
        image_path=image_path,
        template_id=template_id,
        language=language,
    )
    ocr_result.task_id = task_id

    # 生成Excel / Generate Excel
    output_path = await excel_service.generate(
        ocr_result=ocr_result,
        template_id=template_id,
        output_mode=output_mode,
    )
    ocr_result.output_file = output_path

    # 同时生成原始识别版本(不套用模板) / Also generate raw version without template
    raw_output_path = None
    if ocr_result.table_html:
        try:
            raw_output_path = await excel_service.generate_raw(ocr_result)
            logger.info(f"Raw file generated: {raw_output_path}")
        except Exception as e:
            logger.warning(f"Failed to generate raw file: {e}")
    

    return APIResponse(
        data={
            "task_id": task_id,
            "items": [item.model_dump() for item in ocr_result.items],
            "raw_text": ocr_result.raw_text,
            "table_html": ocr_result.table_html,
            "table_count": len(ocr_result.table_html),
            "output_file": output_path,
            "raw_output_file": raw_output_path,
        }
    )


@router.post("/recognize/batch", response_model=APIResponse)
async def recognize_batch(
    images: list[UploadFile] = File(..., description="多张表单照片 / Multiple form photos"),
    template_id: Optional[str] = Form(None),
    output_mode: str = Form("data_only"),
    language: str = Form("auto"),
):
    """
    批量上传表单照片进行OCR识别
    Batch upload form photos for OCR recognition
    """
    results = []
    for image in images:
        task_id = str(uuid.uuid4())
        upload_dir = os.path.join(settings.uploads_dir, task_id)
        os.makedirs(upload_dir, exist_ok=True)

        file_ext = os.path.splitext(image.filename or "photo.jpg")[1] or ".jpg"
        image_path = os.path.join(upload_dir, f"original{file_ext}")
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)

        ocr_result = await ocr_service.recognize(
            image_path=image_path,
            template_id=template_id,
            language=language,
        )
        ocr_result.task_id = task_id

        output_path = await excel_service.generate(
            ocr_result=ocr_result,
            template_id=template_id,
            output_mode=output_mode,
        )
        results.append({
            "task_id": task_id,
            "items": [item.model_dump() for item in ocr_result.items],
            "output_file": output_path,
        })

    return APIResponse(data={"results": results, "total": len(results)})


@router.get("/result/{task_id}", response_model=APIResponse)
async def get_result(task_id: str):
    """获取识别结果 / Get recognition result"""
    output_dir = "output"
    for f in os.listdir(output_dir):
        if f.startswith(task_id):
            return APIResponse(data={"task_id": task_id, "output_file": os.path.join(output_dir, f)})
    raise HTTPException(status_code=404, detail="Result not found")


@router.get("/download/{task_id}")
async def download_result(task_id: str, filename: str | None = None, raw: bool = False):
    """下载Excel结果 / Download Excel result. raw=true下载原始识别版本"""
    from fastapi.responses import FileResponse

    output_dir = settings.output_dir
    # 查找匹配文件：raw版本 = _table/_data, 模板版本 = _restored
    candidates = [f for f in os.listdir(output_dir) if f.startswith(task_id)]
    if not candidates:
        raise HTTPException(status_code=404, detail="File not found")

    if raw:
        # 优先找 _table 或 _data 文件
        target = next((f for f in candidates if "_table." in f or "_data." in f), None)
        if not target:
            raise HTTPException(status_code=404, detail="Raw file not found")
    else:
        # 优先找 _restored 文件，否则取第一个
        target = next((f for f in candidates if "_restored." in f), None)
        if not target:
            target = candidates[0]

    filepath = os.path.join(output_dir, target)
    dl_name = target
    if filename:
        if not filename.endswith(".xlsx"):
            filename += ".xlsx"
        dl_name = filename
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=dl_name,
    )


@router.post("/send-email", response_model=APIResponse)
async def send_result_email(
    task_id: str = Form(...),
    to_email: str = Form(..., description="收件人邮箱 / Recipient email"),
):
    """
    通过邮件发送识别结果Excel
    Send recognition result Excel via email
    """
    output_dir = "output"
    filepath = None
    for f in os.listdir(output_dir):
        if f.startswith(task_id):
            filepath = os.path.join(output_dir, f)
            break

    if not filepath:
        raise HTTPException(status_code=404, detail="Result not found")

    try:
        await email_service.send_result(to_email=to_email, file_path=filepath)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")

    return APIResponse(message=f"Email sent to {to_email}")
