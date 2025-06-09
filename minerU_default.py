import glob
import os
from pathlib import Path
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod


def process_single_pdf(name_without_suff, pdf_file_path, output_dir):
    # prepare env
    local_image_dir, local_md_dir = os.path.join(output_dir, name_without_suff, "images"), os.path.join(output_dir,
                                                                                                        name_without_suff)
    image_dir = str(os.path.basename(local_image_dir))

    os.makedirs(local_image_dir, exist_ok=True)

    # prepare writer
    image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)

    # read bytes
    reader1 = FileBasedDataReader("")
    pdf_bytes = reader1.read(pdf_file_path)  # read the pdf content

    # proc
    ## Create Dataset Instance
    ds = PymuDocDataset(pdf_bytes)

    ## inference
    if ds.classify() == SupportedPdfParseMethod.OCR:
        infer_result = ds.apply(doc_analyze, ocr=True)
        ## pipeline
        pipe_result = infer_result.pipe_ocr_mode(image_writer)
    else:
        infer_result = ds.apply(doc_analyze, ocr=False)
        ## pipeline
        pipe_result = infer_result.pipe_txt_mode(image_writer)

    ### draw model result on each page
    infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))

    ### get model inference result
    model_inference_result = infer_result.get_infer_res()
    ### draw layout result on each page
    pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))
    ### draw spans result on each page
    pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))

    ### get markdown content
    md_content = pipe_result.get_markdown(image_dir)
    ### dump markdown
    pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)

    ### get content list content
    content_list_content = pipe_result.get_content_list(image_dir)
    ### dump content list
    pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)

    ### get middle json
    middle_json_content = pipe_result.get_middle_json()
    ### dump middle json
    pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')


def process_pdf_folder(input_dir, output_dir):
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))  # 获取所有PDF文件列表
    print(f"找到 {len(pdf_files)} 个PDF文件待处理")

    for pdf_path in pdf_files:  # 遍历所有PDF文件
        fname_base = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = Path(os.path.join(output_dir, fname_base, fname_base + ".md"))  # 目标输出路径

        # 🔍 新增检查逻辑
        if output_path.exists():
            print(f"跳过已处理文件: {pdf_path} (输出目录已存在)")
            continue  # 跳过已处理文件
        try:
            process_single_pdf(fname_base, pdf_path, output_dir)
            print(f"成功处理文件: {pdf_path}")
        except Exception as e:
            print(f"转换失败 {pdf_path}: {str(e)}")


if __name__ == '__main__':
    input_dir = "./input"
    output_dir = "./output/minerU"

    process_pdf_folder(input_dir, output_dir)