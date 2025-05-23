import logging
import os
from pathlib import Path
import litellm
import threading
import time
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    ApiVlmOptions,
    ResponseFormat,
    VlmPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
import traceback
from dotenv import load_dotenv
load_dotenv()

# 本地 Gemini API 服务器
class GeminiAPIServer:
    def __init__(self):
        self.is_running = False
        self.server_thread = None

    def start(self):
        import http.server
        import socketserver
        import json

        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/v1/chat/completions':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    try:
                        request_data = json.loads(post_data.decode('utf-8'))
                        model = request_data.get("model", "gemini-2.5-flash-preview-05-20")
                        messages = request_data.get("messages", [])
                        response = litellm.completion(
                            model=f"gemini/{model}",
                            messages=messages,
                            temperature=request_data.get("temperature", 0.1),
                            max_tokens=request_data.get("max_tokens", 8192)
                        )
                        result = {
                            "id": response.id,
                            "object": "chat.completion",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "message": {
                                        "role": "assistant",
                                        "content": response.choices[0].message.content
                                    },
                                    "finish_reason": "stop"
                                }
                            ],
                            "usage": response.usage.dict() if response.usage else {}
                        }
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        tb = traceback.format_exc()
                        error_response = {"error": str(e), "traceback": tb}
                        self.wfile.write(json.dumps(error_response).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            def log_message(self, format, *args):
                pass

        def run_server():
            with socketserver.TCPServer(("", 4000), CustomHandler) as httpd:
                httpd.timeout = 1
                self.httpd = httpd
                while self.is_running:
                    httpd.handle_request()

        self.is_running = True
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.start()
        time.sleep(2)

    def stop(self):
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=5)
        logging.info("API 服务器已停止")

api_server = GeminiAPIServer()

def gemini_vlm_options(model: str, prompt: str, timeout: int = 300):
    """配置 Gemini 的 VLM 选项"""
    return ApiVlmOptions(
        url="http://localhost:4000/v1/chat/completions",
        params=dict(
            model=model,
            max_tokens=8192,
            temperature=0.1,
        ),
        prompt=prompt,
        timeout=timeout,
        scale=1.0,
        response_format=ResponseFormat.MARKDOWN,
    )

def process_single_pdf(pdf_path: Path, output_dir: Path, model_name: str = "gemini-2.5-flash-preview-05-20"):
    logging.info(f"正在处理: {pdf_path.name}")
    pipeline_options = VlmPipelineOptions(
        enable_remote_services=True
    )
    pipeline_options.vlm_options = gemini_vlm_options(
        model=model_name,
        prompt="请将以下文档转换为Markdown格式，包含：1. 完整文本内容 2. 数学公式（LaTeX格式） 3. 图表标题及引用 4. 表格内容 5. 其他重要信息",
        timeout=300
    )
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                pipeline_cls=VlmPipeline,
            )
        }
    )
    try:
        result = doc_converter.convert(pdf_path)
        output_file = output_dir / f"{pdf_path.stem}_content.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.document.export_to_markdown())
        logging.info(f"转换完成，结果已保存到: {output_file}")
        return True, output_file
    except Exception as e:
        logging.error(f"处理 {pdf_path.name} 时出错: {e}")
        return False, None

def process_pdf_folder(input_folder: str, output_folder: str = "./output", model_name: str = "gemini-2.5-flash-preview-05-20"):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if not os.getenv("GEMINI_API_KEY"):
        logging.error("未设置 GEMINI_API_KEY 环境变量")
        return
    os.environ["LITELLM_LOG"] = "ERROR"
    logging.info("=== 启动本地 API 服务器 ===")
    try:
        api_server.start()
        logging.info("API 服务器启动成功")
    except Exception as e:
        logging.error(f"无法启动 API 服务器: {e}")
        return
    input_path = Path(input_folder)
    if not input_path.exists():
        logging.error(f"输入文件夹不存在: {input_folder}")
        api_server.stop()
        return
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    try:
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            logging.warning(f"在 {input_folder} 中未找到PDF文件")
            return
        logging.info(f"找到 {len(pdf_files)} 个PDF文件")
        success_count = 0
        failed_files = []
        for i, pdf_file in enumerate(pdf_files, 1):
            logging.info(f"\n=== 处理第 {i}/{len(pdf_files)} 个文件 ===")
            success, output_file = process_single_pdf(pdf_file, output_path, model_name)
            if success:
                success_count += 1
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"\n--- {pdf_file.name} 转换结果预览 ---")
                    print(content[:200] + "..." if len(content) > 200 else content)
            else:
                failed_files.append(pdf_file.name)
        logging.info(f"\n=== 处理完成 ===")
        logging.info(f"成功处理: {success_count}/{len(pdf_files)} 个文件")
        if failed_files:
            logging.warning(f"失败文件: {', '.join(failed_files)}")
    finally:
        api_server.stop()

def main():
    input_folder = "./input"
    output_folder = "./output"
    model_name = "gemini-2.5-flash-preview-05-20"
    process_pdf_folder(input_folder, output_folder, model_name)

if __name__ == "__main__":
    main()