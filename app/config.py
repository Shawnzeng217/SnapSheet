from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置 / Application settings"""

    app_env: str = "development"
    app_port: int = 8000
    app_host: str = "0.0.0.0"

    # OCR provider: glm / textin / abbyy / azure
    ocr_provider: str = "glm"

    # ABBYY Cloud OCR
    abbyy_app_id: str = ""
    abbyy_password: str = ""
    abbyy_service_url: str = "https://cloud-westus.ocrsdk.com"

    # 合合信息 TextIn
    textin_app_id: str = ""
    textin_app_secret: str = ""

    # 智谱GLM-OCR
    glm_api_key: str = ""

    # Azure Document Intelligence
    azure_doc_endpoint: str = ""
    azure_doc_key: str = ""

    # Email (SMTP)
    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # SharePoint
    sharepoint_site_url: str = ""
    sharepoint_client_id: str = ""
    sharepoint_client_secret: str = ""
    sharepoint_tenant_id: str = ""

    # 数据目录 (Render 持久化磁盘挂载到 /app/data)
    # Data directory (Render persistent disk mounts to /app/data)
    data_dir: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def uploads_dir(self) -> str:
        if self.data_dir:
            return f"{self.data_dir}/uploads"
        return "uploads"

    @property
    def output_dir(self) -> str:
        if self.data_dir:
            return f"{self.data_dir}/output"
        return "output"

    @property
    def templates_dir(self) -> str:
        if self.data_dir:
            return f"{self.data_dir}/templates"
        return "templates"


settings = Settings()
