# SnapSheet (拍表) — 产品需求文档 PRD

**Product**: SnapSheet  
**Version**: 0.2.0  
**Date**: 2026-04-13  
**Author**: Shawn Zeng  
**Status**: MVP 已完成，持续迭代中

---

## 1. 产品概述 / Product Overview

### 1.1 产品定位

SnapSheet 是一款面向酒店运营部门的 OCR 工具。用户使用手机拍摄手写纸质表单（由 Excel 模板打印），系统自动识别内容并还原为结构化的 Excel 文件，消除人工二次录入。

### 1.2 核心价值

| 痛点 | 解决方案 |
|------|---------|
| 一线员工在客房/厨房/仓库手写填表，信息无法实时数字化 | 拍照即转 Excel，随时随地 |
| 手写表单回传至办公室后需人工逐项录入 | OCR 自动识别 + 模板还原，零录入 |
| 纸质表单易丢失、难以汇总和追溯 | 电子化归档，可邮件 / SharePoint 分发 |

### 1.3 目标用户

- **主要用户**: 酒店运营一线员工（客房/餐饮/工程/财务），使用个人手机 (BYOD)
- **管理用户**: 部门主管 / 行政人员，管理模板、查收结果
- **系统管理员**: IT 部门，负责部署和运维

### 1.4 产品名称

- 英文: **SnapSheet** — Snap a photo, get a spreadsheet
- 中文: **拍表** — 拍一拍，表格来

---

## 2. 功能需求 / Functional Requirements

### 2.1 OCR 识别（核心功能）

#### FR-001: 拍照/选图上传
- 支持手机相机直接拍照 (`capture="environment"`)
- 支持从相册选择图片
- 支持常见图片格式 (JPG, PNG, BMP, TIFF)
- 上传前可预览，可重新选择
- 图片自动压缩/缩放以优化传输

#### FR-002: OCR 文字识别
- 调用第三方 OCR SaaS 进行版面分析和文字识别
- 默认使用 GLM (智谱) `layout_parsing` 接口
- 支持中文、英文、中英混合语言模式
- 返回结构化内容：纯文本 + HTML 表格 + 字段列表

#### FR-003: 符号标准化
- 手写勾选符号 (✓ √ ✔) → 统一输出 `✓`
- 手写叉号 (× ✗ ✘) → 统一输出 `✗`
- 识别 "OK"/"ok" → `OK`，"NG"/"ng" → `NG`

#### FR-004: 智能模板匹配还原
- 用户可指定模板，或由系统自动检测
- **网格对齐算法 (Grid-Align)**：
  1. 将 OCR 结果解析为二维网格（处理 colspan / rowspan）
  2. 加载 Excel 模板为二维网格
  3. 以共同文本为锚点（三级匹配：精确 → 非唯一 → 子串包含）
  4. 建立行列映射（投票 + 插值），处理多表格纵向拼接
  5. 按映射关系填充模板空白单元格
  6. 未映射区域回退到标签邻接策略（左侧/上方标签识别）
- 保留模板原始格式：合并单元格、边框、字体、列宽
- 输出: `{task_id}_restored.xlsx`

#### FR-005: 原始表格导出
- 将 OCR 识别的 HTML 表格原样转换为 Excel
- 保留合并单元格结构
- 表头自动加蓝底加粗样式
- 列宽自适应（中文字符宽度 ×2）
- 输出: `{task_id}_table.xlsx`

#### FR-006: 纯数据导出
- 无模板时回退为三列表格：字段名 | 识别值 | 置信度
- 简洁样式
- 输出: `{task_id}_data.xlsx`

#### FR-007: 批量识别
- 支持一次上传多张图片
- 每张图片独立识别，返回各自的 task_id

### 2.2 模板管理

#### FR-008: 模板列表
- 展示所有已上传模板（名称 + 描述）
- 模板信息持久化于 `meta.json`

#### FR-009: 模板上传
- 支持 `.xlsx` 和 `.xls` 格式
- `.xls` 自动转换为 `.xlsx`
- 需填写模板名称，描述可选
- 上传后自动刷新模板下拉列表

#### FR-010: 模板删除
- 删除前二次确认
- 同时删除文件和 `meta.json` 中的记录

### 2.3 结果分发

#### FR-011: 文件下载
- 下载模板还原后的 Excel 文件
- 支持自定义文件名（弹窗输入）
- 支持一键下载原始识别表格（无需命名）

#### FR-012: 邮件发送
- 将识别结果 Excel 通过邮件发送至指定邮箱
- 使用 SMTP（Office 365 TLS）
- 异步发送，UI 显示发送状态

### 2.4 前端交互

#### FR-013: 移动端优先
- 响应式布局，最大宽度 560px
- 触控友好的操作区域
- 无需安装 App，浏览器直接访问

#### FR-014: 分步引导
- Step 1: 上传照片
- Step 2: 选择模板和语言
- Step 3: 查看识别结果 → 下载 / 邮件

#### FR-015: 自定义下拉选择器
- 不使用浏览器原生 `<select>` 控件
- 毛玻璃风格下拉菜单，动画过渡
- 与隐藏的原生 `<select>` 同步（保持表单兼容性）

#### FR-016: 表格预览
- HTML 表格安全渲染（标签白名单过滤）
- 支持横向滚动
- 仅作参考提示，以下载的 Excel 为准

#### FR-017: 双语界面
- 所有界面文案使用 中文 / English 双语

---

## 3. 非功能需求 / Non-Functional Requirements

### 3.1 性能

| 指标 | 目标 |
|------|------|
| 单张图片识别响应时间 | < 10s (取决于 OCR SaaS) |
| 页面首次加载 | < 2s |
| Excel 生成时间 | < 1s |
| 并发用户 | 支持 10+ 同时识别 (异步 I/O) |

### 3.2 可靠性

- OCR API 调用失败时返回明确错误信息
- 上传文件自动按 UUID 隔离，互不干扰
- 服务健康检查端点 `GET /health`

### 3.3 安全性

- API 密钥通过环境变量注入，不入代码库
- 前端 HTML 表格渲染经过标签白名单过滤（防 XSS）
- `.env` 文件在 `.gitignore` 中排除
- CORS 配置（当前为 `*`，生产环境应收窄）

### 3.4 可维护性

- OCR 提供商遵循统一 `OCRProvider` 抽象接口，可插拔替换
- 配置集中管理于 `app/config.py`，支持环境变量覆盖
- Python 全程使用 type hints
- API 响应统一格式: `{ code: 0, message: "success", data: {...} }`

---

## 4. 系统架构 / System Architecture

```
┌───────────────────────────────────────────────────┐
│                   用户手机浏览器                      │
│          HTML / CSS / Vanilla JS (BYOD)            │
└──────────────────────┬────────────────────────────┘
                       │ HTTP (REST API)
┌──────────────────────▼────────────────────────────┐
│                 FastAPI Backend                     │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ OCR API  │  │ Template API │  │ Health API  │  │
│  └────┬─────┘  └──────────────┘  └─────────────┘  │
│       │                                            │
│  ┌────▼──────────────────────────────────────────┐ │
│  │              OCR Service                       │ │
│  │  ┌─────────────┐  ┌────────────────────────┐  │ │
│  │  │ OCR Provider│  │    Excel Service       │  │ │
│  │  │  (GLM/等)   │  │  Grid-Align / Raw /   │  │ │
│  │  │             │  │  Data-Only 三种模式    │  │ │
│  │  └──────┬──────┘  └────────────────────────┘  │ │
│  └─────────┼─────────────────────────────────────┘ │
│            │                                        │
│  ┌─────────▼─────────┐  ┌──────────────────────┐  │
│  │  GLM / TextIn /   │  │   Email Service      │  │
│  │  ABBYY / Azure    │  │   (SMTP/O365)        │  │
│  │  (SaaS OCR)       │  └──────────────────────┘  │
│  └───────────────────┘                             │
└────────────────────────────────────────────────────┘
         │                        │
    uploads/                  output/
    templates/               (Excel 文件)
```

### 4.1 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python 3.11+ / FastAPI / Uvicorn |
| OCR 引擎 | GLM (智谱) layout_parsing（默认） |
| Excel 处理 | openpyxl (.xlsx), xlrd (.xls) |
| HTTP 客户端 | httpx (异步) |
| 图片处理 | Pillow |
| 前端 | HTML5 / CSS3 / Vanilla JS（无框架） |
| 部署 | Docker / Render Cloud |

### 4.2 OCR 提供商接口

```python
class OCRProvider(ABC):
    async def recognize_image(image_path, language) -> OCRResponse
    async def recognize_table(image_path, language) -> OCRResponse
```

已实现: **GLM**（完整）  
预留接口: TextIn / ABBYY / Azure（Stub）

---

## 5. 数据模型 / Data Models

### 5.1 API 统一响应

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

### 5.2 OCR 识别结果

```json
{
  "task_id": "uuid",
  "template_id": "optional",
  "items": [
    {
      "field_name": "申请人",
      "value": "张三",
      "confidence": 0.95,
      "position": [x1, y1, x2, y2]
    }
  ],
  "raw_text": "Markdown 全文",
  "table_html": ["<table>...</table>"],
  "table_count": 2,
  "output_file": "output/{task_id}_restored.xlsx",
  "raw_output_file": "output/{task_id}_table.xlsx"
}
```

### 5.3 模板信息

```json
{
  "template_id": "product_checking_list",
  "name": "客房检查表",
  "description": "Housekeeping daily checklist",
  "filename": "product_checking_list.xlsx"
}
```

---

## 6. 部署方案 / Deployment

### 6.1 Render Cloud（推荐）

| 配置 | 值 |
|------|---|
| 类型 | Web Service |
| 计划 | Starter ($7/月, 512MB RAM) |
| 运行时 | Docker |
| 持久化磁盘 | 1GB @ `/app/data` |
| 健康检查 | `GET /health` |
| 环境变量 | `GLM_API_KEY`, `DATA_DIR`, `SMTP_*` |

### 6.2 环境变量清单

| 变量 | 必填 | 说明 |
|------|------|------|
| `OCR_PROVIDER` | 否 | 默认 `glm` |
| `GLM_API_KEY` | **是** | 智谱 API Key |
| `DATA_DIR` | 否 | 持久化数据目录（Render 用 `/app/data`） |
| `APP_HOST` | 否 | 默认 `0.0.0.0` |
| `APP_PORT` | 否 | 默认 `8000` |
| `SMTP_USER` | 邮件功能需要 | Office365 邮箱 |
| `SMTP_PASSWORD` | 邮件功能需要 | SMTP 密码 |
| `SMTP_FROM` | 邮件功能需要 | 发件人地址 |

---

## 7. 已知限制 / Known Limitations

1. **OCR 提供商**: 仅 GLM 完整实现，TextIn / ABBYY / Azure 为 Stub
2. **模板匹配**: 对结构化表单效果最佳，自由格式手写场景效果有限
3. **拍摄角度**: 较大透视变形可能影响网格对齐精度
4. **嵌套合并单元格**: 复杂嵌套合并场景可能还原不完美
5. **单机存储**: 未接入云存储 / 数据库，依赖本地磁盘
6. **无用户认证**: 当前无登录体系

---

## 8. 路线图 / Roadmap

### Phase 1 — MVP ✅ (已完成)
- [x] GLM OCR 集成
- [x] HTML 表格 → Excel（保留合并单元格）
- [x] 智能模板匹配还原（Grid-Align 算法）
- [x] 原始识别导出
- [x] 符号标准化 (✓/✗)
- [x] 移动端自适应 UI
- [x] 模板 CRUD
- [x] 邮件发送
- [x] Docker + Render 部署
- [x] Hilton 品牌风格 UI

### Phase 2 — 增强 (计划中)
- [ ] 模板自动识别（无需用户选择）
- [ ] 批量结果汇总 / 合并导出
- [ ] SharePoint 自动上传
- [ ] 用户认证与权限管理
- [ ] 历史记录查询

### Phase 3 — 扩展
- [ ] 多 OCR 引擎 A/B 测试
- [ ] 识别结果在线编辑/校正
- [ ] 集成酒店 PMS 系统
- [ ] 定时任务清理历史文件
- [ ] 多酒店 / 多品牌支持

---

## 9. 设计规范 / Design Spec

### 9.1 品牌色板 (Hilton Brand)

| Token | 色值 | 用途 |
|-------|------|------|
| Hilton Blue | `#002F61` | 主色、按钮、标题 |
| Off-White | `#F0E9E6` | 页面背景 |
| Turquoise | `#007293` | 强调色、图标、链接 |
| Teal | `rgb(6,147,126)` | 成功状态 |
| Gold | `#C5A46C` | 中等置信度 |

### 9.2 UI 风格

- **Glassmorphism 毛玻璃卡片**: `backdrop-filter: blur(14px)`, 半透明白色背景, 1px 白色边框, 圆角 20px
- **字体**: Playfair Display (标题/衬线), Inter (正文/无衬线)
- **交互**: 自定义下拉选择器、模态弹窗动画、Toast 提示
- **间距**: 卡片内 28px padding, 卡片间 20px gap

---

*文档版本: v1.0 | 最后更新: 2026-04-13*
