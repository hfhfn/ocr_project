import os

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converter = PdfConverter(
    artifact_dict=create_model_dict(),  # 可传入参数device："cpu", "mps"（mac m系列）, "cuda", "xla"（GPU/CPU/TPU跨平台加速）
)

source = "./input"  # document per local path or URL
document_path = [os.path.join(source, file) for file in os.listdir(source) if file.endswith(".pdf")][0]

rendered = converter(document_path)
text, ext, images = text_from_rendered(rendered)

print(text[:100], ext, images.keys())
