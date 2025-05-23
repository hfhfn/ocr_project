import glob
import json
import os
from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import text_from_rendered, convert_if_not_rgb
from marker.services.gemini import GoogleGeminiService
from marker.settings import settings
from dotenv import load_dotenv
load_dotenv()


def save_results(rendered_output, output_dir="output", fname_base=None):
    """
    终极优化版 save_results：
    1. 生成文本内容并直接替换图片路径
    2. 文本和元数据只写入一次
    3. 图片直接保存到 fname_base 子目录
    4. Markdown 文件一次性写入最终结果
    """
    # 默认文件名
    fname_base = fname_base or "document"
    image_subdir = Path(os.path.join(output_dir, fname_base, "images"))

    # 1️⃣ 生成原始文本内容和图片字典
    raw_text, ext, images = text_from_rendered(rendered_output)

    # 2️⃣ 创建子目录并直接保存图片（同时构建路径映射）
    image_subdir.mkdir(parents=True, exist_ok=True)
    path_mapping = {}

    for img_name, img in images.items():
        img = convert_if_not_rgb(img)  # 确保图片格式为 RGB
        img_path = os.path.join(image_subdir, img_name)  # 🔥 直接定位到子目录
        img.save(img_path, settings.OUTPUT_IMAGE_FORMAT)
        path_mapping[img_name] = os.path.join("images", img_name)  # 构建相对路径映射

    # 3️⃣ 替换原始文本中的图片路径（内存中一次性完成）
    updated_text = raw_text
    for old, new in path_mapping.items():
        updated_text = updated_text.replace(f"]({old})", f"]({new})")

    # 4️⃣ 处理文本编码并一次性保存 Markdown 文件
    encoded_text = updated_text.encode(settings.OUTPUT_ENCODING, errors="replace").decode(settings.OUTPUT_ENCODING)
    markdown_path = Path(os.path.join(output_dir, fname_base, f"{fname_base}.{ext}"))
    with open(markdown_path, "w+", encoding=settings.OUTPUT_ENCODING) as f:
        f.write(encoded_text)

    # 5️⃣ 保存元数据到 JSON 文件（仅一次写入）
    meta_path = Path(os.path.join(output_dir, fname_base, f"{fname_base}_meta.json"))
    with open(meta_path, "w+", encoding=settings.OUTPUT_ENCODING) as f:
        f.write(json.dumps(rendered_output.metadata, indent=2))


def main():
    # PDF路径处理
    # pdf_path = "https://arxiv.org/pdf/2101.03961.pdf"  # url应该先请求文件，再处理
    pdf_dir = "./input"  # 支持URL或本地路径
    output_dir = "./output"

    # 配置参数
    config = {
        "output_format": "markdown",  # 支持markdown/json/html等
        "output_dir": output_dir,

        # 生成版面分析结果，蓝色框表示文本行，红色框表示较大的布局块（段落、表格、图片等）
        "debug": True,  # Master debug flag
        # This will automatically set:
        # "debug_pdf_images": True,
        # "debug_layout_images": True,
        # "debug_json": True,
        # "debug_data_folder": "marker_output" (same as output_dir by default when debug=True)
        #
        # If you want a different folder for debug images:
        # "debug_data_folder": "marker_debug_visuals", # Uncomment and set your preferred path
        # "debug_pdf_images": True, # Then you'd set this explicitly if not using "debug": True

        # 使用指定的LLM服务
        "use_llm": True,
        "gemini_model_name": "gemini-2.5-flash-preview-05-20",
        "llm_service": "marker.services.gemini.GoogleGeminiService",  # 默认值，LLM类
        "gemini_api_key": os.environ.get("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY",
        # "disable_image_extraction": True,  # 禁用图片提取，会填充LLM理解内容，默认False
    }

    # 初始化配置解析器
    config_parser = ConfigParser(config)
    converter_config = config_parser.generate_config_dict()

    # 创建模型字典
    artifact_dict = create_model_dict()

    # 初始化转换器
    converter = PdfConverter(
        config=converter_config,
        artifact_dict=artifact_dict,
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service()
    )

    # 5. Verification (Important!)
    # Check the instantiated LLM service within the converter
    if hasattr(converter, 'llm_service') and converter.llm_service is not None:
        print(f"Successfully initialized LLM service: {converter.llm_service.__class__.__name__}")
        if isinstance(converter.llm_service, GoogleGeminiService):
            print(f"  Using Gemini model: {converter.llm_service.gemini_model_name}")
            print(
                f"  Using Gemini API key (first 5 chars): {converter.llm_service.gemini_api_key[:5]}...")  # Avoid printing full key
            # You can also check other parameters if you set them, e.g.:
            # print(f"  Max retries: {converter.llm_service.max_retries}")
        else:
            print(f"  LLM service is not GoogleGeminiService, it is: {type(converter.llm_service)}")
    else:
        print("LLM service was not initialized in PdfConverter.")
        if not converter_config.get("use_llm"):
            print("  Reason: 'use_llm' was not set to True in the config.")
        if not config_parser.get_llm_service():
            print("  Reason: 'llm_service' was not specified or found.")


    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))  # 获取所有PDF文件列表
    print(f"找到 {len(pdf_files)} 个PDF文件待处理")

    for pdf_path in pdf_files:  # 遍历所有PDF文件
        fname_base = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = Path(os.path.join(output_dir, fname_base))  # 目标输出路径

        # 🔍 新增检查逻辑
        if output_path.exists():
            print(f"跳过已处理文件: {pdf_path} (输出目录已存在)")
            continue  # 跳过已处理文件
        try:
            # 执行转换
            rendered_output = converter(pdf_path)
            # 保存结果到本地
            save_results(rendered_output, output_dir="output", fname_base=fname_base)
            print(f"成功处理文件: {pdf_path}")
        except Exception as e:
            print(f"转换失败 {pdf_path}: {str(e)}")


if __name__ == "__main__":
    main()