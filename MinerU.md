# MinerU 项目文档

技术栈

### 核心语言

* Python（支持 3.10-3.13 版本）

### 关键库/框架

- PDF 处理：
  * PyMuPDF（AGPL 许可证，计划更换）
  * pdfminer.six
- **Office 文件转换：**
  * LibreOffice（通过 `soffice` 命令使用）
- 光学字符识别 (OCR)：
  * PaddleOCR（以及 PaddleOCR2Pytorch，用于消除直接的桨依赖）
  * 快速OCR
  * 模型：`PP-OCRv4_server_rec_doc`
- 布局分析：
  * DocLayout-YOLO
  * layoutlmv3（为了解决detectron2兼容性问题而逐步淘汰）
  * layoutreader
- **表格识别：**
  * RapidTable
  * StructEqTable-InternVL2-1B
  * Paddle TableMaster
  * 模型：`rapid_table`、`slanet_plus`
* **公式识别：**
  * 模型：`yolo_v8_mfd`、`unimernet_small`、`unimernet(2503)`
- 语言检测：
  * fast-langdetect
  * 模型：`yolo_v11n_langdetect`
- 机器学习/深度学习：
  * PyTorch（版本 2.2-2.6，不包括 2.5）
  * Transformers
- RAG 集成：
  * LlamaIndex（特别是 `llama-index-vector-stores-elasticsearch`、`llama-index-embeddings-dashscope`、`llama-index-core`）
- Web/API：
  * FastAPI（可能在 `projects/web_api` 和 `projects/web_demo` 中使用）
  * Gradio（用于演示）
* **前端（用于网络演示/项目）：**
    * React（由 `projects/web` 中的 `App.tsx`、`tsconfig.json` 表示）
- **打包/依赖管理：**
  * `pip`
  * `conda`
  * `setup.py`
  * `requirements.txt`
  * `pyproject.toml`（诗歌）
- Docker：
  * 用于为全局（CPU/CUDA）和Ascend NPU部署创建可重现的环境。

### 支持的文件格式和处理方法

* **主要输入：** PDF
  - **转换为 PDF：**
    * Word（.doc、.docx）
    * PowerPoint（.ppt、.pptx）
    * 在进一步处理之前，使用 LibreOffice（“soffice”）将这些转换为 PDF。
    * `magic_pdf/utils/office_to_pdf.py` 脚本处理此转换。
* **图像格式（可能用于 OCR 或嵌入文档）：** .jpg、.png（在 Dataset 类的上下文中的 `README.md` 中提及）。
* **处理步骤（从 README 和模块名称推断）：**
    1. **（可选）将 Office 文档转换为 PDF。**
    2. **PDF 解析**：提取原始内容（文本、图像）。
    3. **布局分析**：识别页眉、页脚、段落、标题、列表、图像、表格等元素。
    4. **OCR**：适用于扫描的 PDF 或 PDF 中的图像。支持 84 种语言，并具有自动语言检测功能（`lang='auto'`）。
    5. **公式识别**：检测并将公式转换为 LaTeX。
    6. **表格识别**：检测表格并将其转换为 HTML 或 LaTeX。
    7. **内容结构**：排序内容、将标题链接到图形/表格、段落合并。
    8. **输出生成**：Markdown、JSON、中间格式。

### LLM API 集成

* **后处理任务**：LLM（兼容 OpenAI）用于各种后处理任务，以提高提取信息的质量。这些任务包括：
    * 公式修正
    * OCR文本校正
    * 标题层级优化
    * 此功能主要在“magic_pdf/post_proc/llm_aided.py”中管理。
* **RAG（检索增强生成）：** 
  * 该项目通过 LlamaIndex 与 DashScope 集成，以实现 RAG 功能。这在 `projects/llama_index_rag` 目录中可见。
* **配置：**
    * LLM API 访问通常通过初始化期间传递的配置字典或通过环境变量进行配置。
    * 必备参数包括 `api_key`、`base_url`、以及具体的 `model` 名称。
    * 这些配置存储在用户目录下的“magic-pdf.json”这样的中央文件中，或者在应用程序内以编程方式设置。

### 设备配置选项

* **可用模式：**
    * `cpu`（默认模式，在中央处理器上运行）
    * `cuda`（对于 NVIDIA GPU，需要适当的 NVIDIA 驱动程序）
    * `npu`（适用于华为 Ascend NPU，需要 CANN 工具包）
    * `mps`（适用于 Apple Silicon GPU）
* **配置方法：**
    * 设置设备模式的主要方法是修改位于用户目录中的“magic-pdf.json”文件（例如，“~/magic-pdf.json”）。
    * 在此 JSON 文件中，将 `"device-mode"` 键设置为可用模式之一（例如，`"device-mode": "cuda"`）。
* **要求：**
    * **CUDA：**需要安装 NVIDIA 驱动程序。
    * **NPU：**需要华为的 CANN（神经网络计算架构）工具包。