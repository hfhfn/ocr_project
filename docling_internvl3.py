import logging
import os
from pathlib import Path
import requests
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    ApiVlmOptions,
    ResponseFormat,
    VlmPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

def check_lm_studio_connection(url="http://127.0.0.1:1234", timeout=5):
    """检查LM Studio是否正常运行"""
    try:
        response = requests.get(f"{url}/v1/models", timeout=timeout)
        if response.status_code == 200:
            models = response.json()
            logging.info("LM Studio连接成功")
            return True, models
        else:
            logging.error(f"LM Studio响应异常，状态码: {response.status_code}")
            return False, None
    except Exception as e:
        logging.error(f"无法连接到LM Studio: {e}")
        return False, None

def lm_studio_vlm_options(model: str, prompt: str, timeout: int = 300):
    """配置LM Studio的VLM选项"""
    options = ApiVlmOptions(
        url="http://localhost:1234/v1/chat/completions",
        params=dict(
            model=model,
            max_tokens=8192,
            temperature=0.1,
        ),
        prompt=prompt,
        timeout=timeout,
        scale=0.5,  # 可以调整图片缩放比例
        response_format=ResponseFormat.MARKDOWN,
    )
    return options

def process_single_pdf(pdf_path: Path, output_dir: Path, model_name: str = "internvl3-9b"):
    """处理单个PDF文件"""
    logging.info(f"正在处理: {pdf_path.name}")

    # 配置VLM流水线
    pipeline_options = VlmPipelineOptions(
        enable_remote_services=True
    )

    pipeline_options.vlm_options = lm_studio_vlm_options(
        model=model_name,
        prompt="OCR the full page to markdown.",

        #         prompt="""Please accurately extract all text content from this page, including:
# 1. Text content
# 2. Mathematical formulas (in LaTeX format if possible)
# 3. Figure captions and references
# 4. Table content
# 5. Any other relevant information
#
# Format the output in markdown.""",
        timeout=300
    )

    # 创建文档转换器
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                pipeline_cls=VlmPipeline,
            )
        }
    )

    try:
        # 执行转换
        result = doc_converter.convert(pdf_path)

        # 保存结果
        markdown_content = result.document.export_to_markdown()
        output_file = output_dir / f"{pdf_path.stem}_content.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logging.info(f"转换完成，结果已保存到: {output_file}")
        return True, output_file

    except Exception as e:
        logging.error(f"处理 {pdf_path.name} 时出错: {e}")
        return False, None

def process_pdf_folder(input_folder: str, output_folder: str = "./output", model_name: str = "internvl3-2b"):
    """处理指定文件夹中的所有PDF文件"""

    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 检查输入文件夹
    input_path = Path(input_folder)
    if not input_path.exists():
        logging.error(f"输入文件夹不存在: {input_folder}")
        return

    # 创建输出文件夹
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # 检查LM Studio连接
    logging.info("=== 检查LM Studio连接 ===")
    success, models = check_lm_studio_connection()
    if not success:
        logging.error("无法连接到LM Studio，请确保：")
        logging.error("1. LM Studio已启动")
        logging.error("2. API服务器已启用")
        logging.error("3. internvl3-2b模型已加载")
        return

    # 查找所有PDF文件
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        logging.warning(f"在 {input_folder} 中未找到PDF文件")
        return

    logging.info(f"找到 {len(pdf_files)} 个PDF文件")

    # 处理每个PDF文件
    success_count = 0
    failed_files = []

    for i, pdf_file in enumerate(pdf_files, 1):
        logging.info(f"\n=== 处理第 {i}/{len(pdf_files)} 个文件 ===")
        success, output_file = process_single_pdf(pdf_file, output_path, model_name)

        if success:
            success_count += 1
            # 显示部分内容预览
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n--- {pdf_file.name} 转换结果预览 ---")
                print(content[:200] + "..." if len(content) > 200 else content)
        else:
            failed_files.append(pdf_file.name)

    # 输出处理结果统计
    logging.info(f"\n=== 处理完成 ===")
    logging.info(f"成功处理: {success_count}/{len(pdf_files)} 个文件")
    if failed_files:
        logging.warning(f"失败文件: {', '.join(failed_files)}")

def main():
    """主函数"""
    # 设置输入文件夹 - 修改这里指定你的PDF文件所在位置
    input_folder = "./pdf_files"  # 修改为你的PDF文件夹路径

    # 设置输出文件夹
    output_folder = "./output"  # 结果保存位置

    # 设置模型名称
    model_name = "internvl3-9b"  # 或者其他你在LM Studio中使用的模型名称

    # 处理指定文件夹中的所有PDF
    process_pdf_folder(input_folder, output_folder, model_name)

if __name__ == "__main__":
    main()
