# ocr_project

## docling项目（star: 30.3k）
- docling.md文件：项目技术解读。
- docling_default文件：插入原图片在markdown文件中作为最终的输出。
- docling_gemini文件：使用gemini接口，插入图片理解内容替换图片占位符，作为最终的输出。
- docling_internvl3文件：支持LM Studio或者ollama加载本地模型，可以跟gemini一样进行图片理解。
- 
## marker项目 (star: 25.3k)
- marker.md文件：项目技术解读。
- marker_default文件：一个简单示例，直接输出嵌入图片路径的markdown文件，并输出提取的图片。
- marker_gemini文件：使用gemini接口，丰富配置，可输出嵌入图片路径或者图片理解内容的markdown文件，并输出debug文件（包含版面布局分析结果）。
- 可以调用 **VLM** 进行图片理解，以及其他如表格、公式、表单等高层次理解。

## MinerU项目 (star: 33.9k)
- mineru.md文件：项目技术解读。
- mineru_default文件：输出直接嵌入图片路径的markdown文件，并输出提取的图片和debug文件（包含版面布局分析结果）。
- 可以调用 **LLM** 进行辅助表格、文字、标题识别，默认使用`qwen2.5-7b-instruct`模型，可以在**user目录下**的`magic-pdf.json`文件中修改模型配置。
- mineru的版面分析效果最好，检测框框更准确。
- ### 注意：需要用python脚本下载模型文件：(以下是从hugging face下载模型的步骤)
  - #### Python脚本会自动下载模型文件并在配置文件（`magic-pdf.json`）中配置模型目录。
- ```python
    pip install huggingface_hub
    wget https://github.com/opendatalab/MinerU/raw/master/scripts/download_models_hf.py -O download_models_hf.py
    python download_models_hf.py
```