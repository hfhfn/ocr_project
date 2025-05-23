# marker项目文档

堆栈概述

该marker项目旨在将 PDF（图像、Office 文档、HTML 和 EPUB） 文件转换为 Markdown、JSON 或 HTML 等结构化格式。它通过一个复杂的流程实现此目标，该流程涉及多个阶段，
每个阶段都利用特定的工具和内部组件：

## 核心 PDF 处理流程和工具

### PDF 加载和初始数据提取：
- 主要工具：pypdfium2

- 该库用于基本的 PDF 交互：打开文件、将单个 PDF 页面渲染为图像以及提取低级信息，如文本字符、其边界框和任何嵌入的链接。

- 标记模块：marker.providers.pdf.PdfProvider

- 这个内部模块包装起来，pypdfium2为其余部分marker访问 PDF 内容提供了一种标准化的方式。

### 文档表示和模式：
- 主要工具：Pydantic

- Pydantic 被广泛用于定义和验证数据的结构marker。这包括主Document对象、PageGroup每个页面的对象、各个Block元素（例如段落、表格等）以及PolygonBox坐标。

- 标记模块：marker.schema.*

- 包内的代码（例如marker.schema.document.Document，，，marker.schema.groups.page.PageGroup）marker.schema.blocks.base.Block。
这些模块定义了 PDF 在处理过程中的内容和结构在内存中的表示。

### 布局检测：
- 主要工具：（surya具体来说，它的布局检测模型，例如surya.layout.LayoutPredictor）。

- surya是一个专门用于文档图像分析的库。其布局模型可以分析 PDF 页面的图像，以识别不同可视区域的边界，例如文本列、图形、表格以及页眉/页脚。

- 标记模块：marker.builders.layout.LayoutBuilder

- 该模块将surya的布局检测功能集成到marker管道中，并将其应用于页面图像。

### OCR（光学字符识别）：
- 主要工具：（surya具体来说，是其文本识别模型，例如surya.recognition.RecognitionPredictor）。

- 当 PDF 包含文本图像（扫描文档）或直接提取文本不可靠时，surya可使用 OCR 功能从这些图像中提取文本。

- 标记模块：marker.builders.ocr.OcrBuilder

- 该模块将surya的OCR结果合并到文档中。

### 行、跨度和字符聚合：
- 主要工具： 自定义算法。

- 标记模块：marker.builders.line.LineBuilder，以及其中的方法marker.schema.groups.page.PageGroup（如merge_blocks）。

- 这些组件获取原始字符数据（来自文本pypdfium2或 OCR），并根据其坐标、字体属性和接近度将其分组为有意义的文本行和跨度。这是重建可读文本的关键步骤。

### 语义块构建和内容处理：
- 主要工具：marker各种“处理器”模块中的自定义算法。如果启用了 LLM 功能，则还会涉及与这些 LLM 交互的库。

- 标记模块：该marker.processors.*软件包包含许多专用模块（例如TextProcessor，.....）。

- 如果使用 LLM，则像TableProcessor或 ListProcessor、CodeProcessor、HeaderProcessor、FootnoteProcessor、
LLMImageDescriptionProcessor、LLMTableProcessor、marker.converters.pdf.PdfConverter
这样的模块也会发挥作用。整体流程由EquationProcessor管理。

- 外部库（对于 LLM，如果使用）：
google-generativeai（适用于 **Google Gemini**）
其他类似的客户端库适用于 **OpenAI、Claude 或本地 Ollama** 实例等服务。

- 目的：**这是对文档进行更高层次理解的地方。处理器识别并格式化特定的语义元素（段落、列表、表格、代码块、数学方程式等），对内容进行排序，并可以使用
LLM 执行高级任务，例如生成图像描述或转换复杂表格。**

### 输出渲染：
- 主要工具： 自定义逻辑marker。

- 标记模块：内的类别marker.renderers.*（例如MarkdownRenderer，，，JSONRenderer）HTMLRenderer。

- 这些模块将完全处理的Document对象转换为您选择的最终输出格式。

### 通用支持库和工具
除了核心管道组件之外，marker还依赖于其他几个有用的库：

- Pillow (PIL)：用于各种图像处理任务，例如创建和修改用于调试可视化的图像，以及处理从中获得的页面图像pypdfium2。

- NumPy：为了进行高效的数值计算，通常需要处理坐标、图像数据，或者作为机器学习模型的依赖项surya。

- ftfy：帮助清理和修复 PDF 文本提取时有时产生的乱码或马赛克文本。

- click：用于构建marker的命令行界面工具。

- 标准 Python 库：包括os（用于文件系统操作）、json（用于 JSON 处理）、logging（用于内部消息）、re（用于文本处理中的正则表达式）
和typing（用于代码清晰度和稳健性）。

### 调试功能
- 主要工具：（Pillow用于在图像上绘图）。

- 标记模块：marker.processors.debug.DebugProcessor。

- 该处理器通过配置标志启用后，可以生成每个 PDF 页面的图像，并在图像上直接绘制各种元素（线条、布局块）的边界框。它还可以保存文档结构的
JSON 表示形式。


# 处理其他格式文件

处理各种文件格式，例如图像、Office 文档、HTML 和 EPUB 。以下是marker对这些文件类型的支持及其处理方法marker的总结：

## 一般方法

- 您可以PdfConverter对所有支持的文件类型（而不仅仅是 PDF）使用相同的类和非常相似的编码模式。marker旨在自动检测文件类型并在内部使用适当的“提供程序”。

- 对于许多格式（例如 DOCX、PPTX、XLSX、EPUB、HTML），marker其工作原理是首先使用外部库将输入文件转换为中间 PDF 格式。
然后，它会使用其核心 PDF 处理引擎处理此临时 PDF。对于图像，它会直接处理。

## 支持的文件格式及其使用方法：

### PDF（.pdf）：

* 支持：是（核心功能）。
* 用途：直接加工。
* 依赖项：（pypdfium2附带marker）。
### 图片.png.jpg.jpeg.bmp.tiff

* 支持：是。
* 用途：图像被视为单页。OCR 对于文本提取至关重要。
* 依赖项：（Pillow通常附带marker），surya（用于 OCR）。
* 注意：如果您的 OCR 设置强大，您将获得最佳结果。
### Microsoft Word ( .docx)：

* 支持：是。
* 工作原理：内部将 DOCX 转换为临时 PDF。
* 用法：将.docx文件路径传递给PdfConverter。
* 依赖项：您需要在 Python 环境中安装（python-mammoth）。WeasyPrintpip install python-mammoth WeasyPrint
### HTML（.html，.htm）：

* 支持：是。
* 工作原理：内部将 HTML 转换为临时 PDF。
* 用法：将.html文件路径传递给PdfConverter。
* 依赖项：您需要WeasyPrint安装（pip install WeasyPrint）。
### EPUB（.epub）：

* 支持：是。
* 工作原理：将 EPUB 转换为 HTML，然后在内部转换为临时 PDF。
* 用法：将.epub文件路径传递给PdfConverter。
* 依赖项：您需要ebooklib、、BeautifulSoup4并WeasyPrint安装（pip install ebooklib BeautifulSoup4 WeasyPrint）。
### 微软 PowerPoint ( .pptx)：

* 支持：是。
* 工作原理：将 PPTX 转换为 HTML，然后在内部转换为临时 PDF。
* 用法：将.pptx文件路径传递给PdfConverter。
* 可选配置：如果您希望幻灯片编号包含在中间 HTML 表示中，则可以将其添加"include_slide_number": True到配置字典中。marker
* 依赖项：您需要python-pptx并WeasyPrint安装（pip install python-pptx WeasyPrint）。
### Microsoft Excel（.xlsx）：

* 支持：是。
* 工作原理：将 XLSX 表转换为 HTML 表，然后在内部转换为临时 PDF。
* 用法：将.xlsx文件路径传递给PdfConverter。
* 依赖项：您需要openpyxl并WeasyPrint安装（pip install openpyxl WeasyPrint）。
### 代码示例（一般模式）：

Python 代码中marker的调用方式保持不变。只需更改文件名即可。
```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
import os

# Example for a DOCX file
pdf_filepath = "your_document.docx" # Or your_image.png, your_book.epub, etc.

my_config = {
    "output_format": "markdown",
    "output_dir": "marker_output",
    # Add any other general marker configurations or debug flags:
    # "debug": True,
    # "use_llm": True, 
    # For PPTX, you could add:
    # "include_slide_number": True, 
}

config_parser = ConfigParser(cli_options=my_config)
converter_config = config_parser.generate_config_dict()

os.makedirs(converter_config.get("output_dir", "marker_output"), exist_ok=True)

model_artifacts = create_model_dict() # Create this once

converter = PdfConverter(
    config=converter_config,
    artifact_dict=model_artifacts,
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service()
)

if not os.path.exists(pdf_filepath):
    print(f"ERROR: File not found at {pdf_filepath}")
else:
    rendered_output = converter(pdf_filepath) # The call is the same!
    
    # Save the output (example for markdown)
    output_basename = os.path.splitext(os.path.basename(pdf_filepath))[0]
    output_md_path = os.path.join(converter_config.get("output_dir", "marker_output"), output_basename + ".md")
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(rendered_output)
    print(f"Converted output saved to: {output_md_path}")
```


### 不支持的格式：

- 较旧的 Microsoft Office 格式（.doc、.ppt、.xls）：
- marker不明确支持这些较旧的二进制格式。内部转换工具（mammoth、python-pptx、openpyxl）主要适用于基于 XML 的现代格式（.docx、.pptx、.xlsx）。
尝试处理这些旧格式可能会导致错误。
### 总结： marker对于列出的现代格式来说，它功能非常丰富！关键在于确保你安装了所需文件类型的转换库，然后就可以像 PdfConverter处理 PDF 一样使用它了。