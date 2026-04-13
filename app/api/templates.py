"""
模板管理API / Template Management API
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import json

from app.models import APIResponse, TemplateInfo
from app.services.excel_service import ExcelService
from app.config import settings

router = APIRouter()

TEMPLATE_DIR = settings.templates_dir


@router.get("/", response_model=APIResponse)
async def list_templates():
    """列出所有模板 / List all templates"""
    templates = []
    meta_path = os.path.join(TEMPLATE_DIR, "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            templates = json.load(f)
    return APIResponse(data=templates)


@router.post("/upload", response_model=APIResponse)
async def upload_template(
    file: UploadFile = File(..., description="Excel模板文件 / Excel template file"),
    name: str = Form(..., description="模板名称"),
    description: str = Form("", description="模板描述"),
):
    """
    上传Excel模板文件，用于OCR模板匹配
    Upload Excel template for OCR template matching
    """
    os.makedirs(TEMPLATE_DIR, exist_ok=True)

    template_id = name.replace(" ", "_").lower()
    file_ext = os.path.splitext(file.filename or "template.xlsx")[1].lower()

    # 先保存原始文件
    raw_path = os.path.join(TEMPLATE_DIR, f"{template_id}{file_ext}")
    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # .xls → .xlsx 自动转换 / Auto-convert legacy .xls to .xlsx
    if file_ext == ".xls":
        save_path = ExcelService.convert_xls_to_xlsx(raw_path)
        os.remove(raw_path)  # 删除原始.xls
    else:
        save_path = raw_path

    # 更新元数据 / Update metadata
    meta_path = os.path.join(TEMPLATE_DIR, "meta.json")
    templates = []
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            templates = json.load(f)

    # Remove existing entry with same id
    templates = [t for t in templates if t["template_id"] != template_id]
    templates.append({
        "template_id": template_id,
        "name": name,
        "description": description,
        "file": save_path,
    })

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

    return APIResponse(data={"template_id": template_id, "file": save_path})


@router.delete("/{template_id}", response_model=APIResponse)
async def delete_template(template_id: str):
    """删除模板 / Delete template"""
    meta_path = os.path.join(TEMPLATE_DIR, "meta.json")
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Template not found")

    with open(meta_path, "r", encoding="utf-8") as f:
        templates = json.load(f)

    target = None
    for t in templates:
        if t["template_id"] == template_id:
            target = t
            break

    if not target:
        raise HTTPException(status_code=404, detail="Template not found")

    # Remove file
    if os.path.exists(target.get("file", "")):
        os.remove(target["file"])

    templates = [t for t in templates if t["template_id"] != template_id]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

    return APIResponse(message=f"Template {template_id} deleted")
