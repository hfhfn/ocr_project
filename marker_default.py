import glob
import os
from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker_gemini import save_results


converter = PdfConverter(
    artifact_dict=create_model_dict(),  # 可传入参数device："cpu", "mps"（mac m系列）, "cuda", "xla"（GPU/CPU/TPU跨平台加速）
)

source = "./input"  # document per local path or URL
output_dir = "./output/default"

# pdf_files = [os.path.join(source, file) for file in os.listdir(source) if file.endswith(".pdf")]
pdf_files = glob.glob(os.path.join(source, "*.pdf"))  # 获取所有PDF文件列表
print(f"找到 {len(pdf_files)} 个PDF文件待处理")

for pdf_path in pdf_files:  # 遍历所有PDF文件

    fname_base = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = Path(os.path.join(output_dir, fname_base  + ".md"))  # 目标输出路径, 默认转换markdown

    # 🔍 新增检查逻辑
    if output_path.exists():
        print(f"跳过已处理文件: {pdf_path} (输出目录已存在)")
        continue  # 跳过已处理文件
    try:
        # 执行转换
        rendered_output = converter(pdf_path)
        # 保存结果到本地
        save_results(rendered_output, output_dir=output_dir, fname_base=fname_base)
        print(f"成功处理文件: {pdf_path}")
    except Exception as e:
        print(f"转换失败 {pdf_path}: {str(e)}")