# Docling 项目技术概览

本文档提供Docling项目的技术概览，包括技术栈、支持的文件格式、LLM API集成和设备配置信息。

## 技术栈

Docling项目主要使用Python构建，并利用了丰富的库和工具生态系统：

* **主要语言：** Python (^3.9)
* **包管理 & 构建：** Poetry
* **核心功能库：**
    * `pydantic`：数据验证、解析和设置管理
    * `docling-core`, `docling-ibm-models`, `docling-parse`：Docling生态系统的核心模块
    * `filetype`：用于稳健的文件类型检测
    * `pypdfium2`：PDF处理、渲染和文本提取
    * `huggingface_hub`, `transformers`：Hugging Face模型集成（VLMs, LLMs）
    * `requests`：用于向外部API发起HTTP请求
    * OCR引擎：支持`easyocr`、`tesserocr`（可选）、`ocrmac`（可选，macOS）、`rapidocr-onnxruntime`（可选）和`onnxruntime`（可选），用于图像和扫描文档的文本识别
    * Microsoft Office格式处理：
        * `python-docx`：处理`.docx`（Word）文件
        * `python-pptx`：处理`.pptx`（PowerPoint）文件
        * `openpyxl`：处理`.xlsx`（Excel）文件
    * 标记语言解析：
        * `beautifulsoup4` / `lxml`：用于HTML和通用XML处理
        * `marko`：处理Markdown（`.md`）文件
    * 图像处理：`pillow`
    * 数值和数据处理：`scipy`, `pandas`, `numpy`
    * 命令行界面（CLI）：`typer`, `click`
    * 模型优化：`accelerate`（可选，用于PyTorch模型）
    * LaTeX处理：`pylatexenc`（也用于DOCX上下文）
* **开发与质量保障工具：**
    * 代码格式化 & 检查：`black`, `isort`, `flake8`, `pylint`, `ruff`
    * 测试：`pytest`, `pytest-cov`, `coverage`
    * 静态类型检查：`mypy`
    * 预提交钩子：`pre-commit`用于维护代码质量
* **文档：** `mkdocs-material`及相关插件

## 支持的文件格式

Docling可以处理多种文件格式，将其转换为统一的文档表示形式。主要方法是为每种格式定制特定后端：

- ### 除PDF外，其他格式参数默认支持直接传入，不需要显式配置

* **PDF（.pdf）：** 使用`pypdfium2`进行文本和布局提取。对图像型PDF可应用OCR
* **Microsoft Word（.docx）：** 使用`python-docx`解析。支持文本、表格和结构元素。包含处理DOCX中嵌入LaTeX的能力
* **HTML（.html, .htm）：** 使用`beautifulsoup4`或`lxml`解析
* **Markdown（.md）：** 使用`marko`解析
* **CSV（.csv）：** 可能使用`pandas`或原生`csv`模块提取数据
* **Microsoft Excel（.xlsx）：** 使用`openpyxl`或`pandas`提取数据
* **Microsoft PowerPoint（.pptx）：** 使用`python-pptx`解析幻灯片内容
* **XML（.xml）：** 通过`lxml`进行通用XML解析。特定后端支持：
    * JATS（期刊文章标签套件）XML
    * USPTO（美国专利商标局）专利XML
* **JSON（.json）：** 支持特定的"Docling JSON"模式用于内部表示，不支持任意JSON文件
* **Asciidoc（.asciidoc, .adoc）：** 专用的Asciidoc格式后端
* **内部Docling格式：** 项目有自己的内部序列化文档格式（`docling_parse_vX`）用于存储和重新加载处理后的文档

## LLM API集成与配置

Docling可与大型语言模型（LLMs）和视觉语言模型（VLMs）集成，用于高级文档理解任务。

**前提条件：**
* 必须将`PipelineOptions`中的`enable_remote_services`标志设为`True`以允许任何外部API调用（例如通过CLI：`--enable-remote-services`）

**配置方法：**

1. **通用API端点（例如Ollama、自定义VLM/LLM服务器）：**
    * 通过`VlmPipelineOptions`中的`ApiVlmOptions`配置
    * **关键参数：**
        * `url`（str）：API端点（例如`http://localhost:11434/v1/chat/completions`）
        * `headers`（dict）：自定义头部，常用于API密钥（例如`{"Authorization": "Bearer YOUR_API_KEY"}`）
        * `params`（dict）：额外的API特定参数（例如`{"model": "name-of-your-model"}`）
        * `prompt`（str）：发送给模型的提示
        * `scale`（float）：VLM的图像缩放因子
        * `timeout`（float）：请求超时（秒）
        * `concurrency`（int）：并发API请求数
        * `response_format`（str）：预期响应格式（例如`doctags`, `markdown`）

2. **Hugging Face模型（本地或远程）：**
    * 通过`VlmPipelineOptions`中的`HuggingFaceVlmOptions`配置
    * **关键参数：**
        * `repo_id`（str）：Hugging Face模型仓库ID（例如`"ds4sd/SmolDocling-256M-preview"`）
        * `prompt`（str）：模型提示
        * `inference_framework`（str）：模型运行方式。选项：
            * `"transformers"`：用于本地Hugging Face模型
            * `"mlx"`：用于Apple Silicon优化的模型（MLX）
            * `"openai"`：如果模型通过OpenAI兼容API服务
        * `load_in_8bit`（bool），`quantized`（bool）：模型加载优化
        * `response_format`（str）：预期响应格式

**相关代码：**
* `docling/models/api_vlm_model.py`（`ApiVlmModel`类）
* `docling/datamodel/pipeline_options.py`（`ApiVlmOptions`, `HuggingFaceVlmOptions`）
* `docling/utils/api_image_request.py`（底层API请求工具）

## 设备配置

Docling允许指定模型推理（例如OCR、VLM处理）的计算设备。

**配置类：**
* 设备设置由`docling/datamodel/pipeline_options.py`中的`AcceleratorOptions`管理，这些选项是主`PipelineOptions`的一部分

**`AcceleratorOptions`中的关键设备选项：**
* `device`（str）：
    * `"auto"`（默认）：自动选择CUDA > MPS > CPU
    * `"cpu"`：强制使用CPU
    * `"cuda"`或`"cuda:N"`：使用NVIDIA CUDA GPU（例如`"cuda:0"`表示第一个GPU）
    * `"mps"`：在Apple Silicon上使用Metal Performance Shaders
* `num_threads`（int）：并行任务的CPU线程数（默认：4）。也可以通过`OMP_NUM_THREADS`或`DOCLING_NUM_THREADS`环境变量设置
* `cuda_use_flash_attention2`（bool）：在CUDA上启用FlashAttention v2（兼容模型默认：`False`）

**配置方法：**

1. **代码配置（通过`PipelineOptions`）：**
    ```python
    from docling.datamodel.pipeline_options import AcceleratorOptions, PdfPipelineOptions

    # 示例：强制使用8线程CPU
    accel_opts = AcceleratorOptions(device="cpu", num_threads=8)
    # pipeline_config = PdfPipelineOptions(accelerator_options=accel_opts)
    ```
2. **环境变量：**
    * `DOCLING_ACCELERATOR_DEVICE`：（例如`cuda`, `cpu`）
    * `DOCLING_ACCELERATOR_NUM_THREADS`：（例如`8`）
    * `DOCLING_ACCELERATOR_CUDA_USE_FLASH_ATTENTION2`：（例如`true`）

**相关代码：**
* `docling/utils/accelerator_utils.py`（`decide_device`函数）
* `docling/datamodel/pipeline_options.py`（`AcceleratorOptions`类）

本文档可作为Docling项目技术方面的实用指南。