import base64
import os
import re

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling_core.types.doc import ImageRefMode
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions

source = "./input"  # document per local path or URL
output_dir = "./output/default"  # 修改为你希望保存的路径

document_path_list = [os.path.join(source, file) for file in os.listdir(source) if file.endswith(".pdf")]
# print(document_path)

pipeline_options = PdfPipelineOptions(
    generate_picture_images=True,
    images_scale=2.0,
    accelerator_options=AcceleratorOptions(device="cpu", num_threads=8)  # 配置device为cpu，线程数为8
)

# 默认支持直接传入各种格式 参考：InputFormat类
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
        ),
        # InputFormat.DOCX: WordFormatOption()  # 除PDF外，其他格式参数默认就行，不需要显示配置
    }
)

def save_images_and_update_markdown(markdown_text, output_dir):
    # 创建图片保存目录
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    # 匹配Base64图片的正则表达式
    pattern = r"!\[Image\]\(data:image/(.*?);base64,(.*?)\)"

    # 查找所有Base64图片
    matches = re.findall(pattern, markdown_text, re.DOTALL)

    # 替换图片路径并保存图片
    for i, (img_type, data) in enumerate(matches, start=1):
        # 生成文件名
        filename = f"image_{i}.{img_type.split('/')[0]}"
        img_path = os.path.join("images", filename)

        # 解码并保存图片
        try:
            img_data = base64.b64decode(data)
            with open(os.path.join(output_dir, img_path), "wb") as img_file:
                img_file.write(img_data)
        except Exception as e:
            print(f"图片保存失败：{str(e)}")
            continue

        # 替换Markdown中的Base64为相对路径
        markdown_text = markdown_text.replace(
            f"data:image/{img_type};base64,{data}",
            img_path,
            1
        )

    return markdown_text

def process_single_pdf(converter, document_path, output_dir):
    result = converter.convert(document_path)

    markdown_text = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)


    output_basename = str(os.path.splitext(os.path.basename(document_path))[0])
    output_subdir = os.path.join(output_dir, output_basename)
    output_path = os.path.join(output_subdir, output_basename + ".md")

    markdown_text = save_images_and_update_markdown(markdown_text, output_subdir)

    # 保存到本地 Markdown 文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    print(f"Markdown 已保存到：{output_path}")
    print(f"图片已保存到：{os.path.join(output_subdir, 'images')}")

def process_pdf_folder(converter, document_path_list, output_dir):
    for document_path in document_path_list:
        process_single_pdf(converter, document_path, output_dir)


if __name__ == '__main__':
    process_pdf_folder(converter, document_path_list, output_dir)