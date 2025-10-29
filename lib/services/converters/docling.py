import logging
from docling.document_converter import DocumentConverter
from lib.services.converters.base import FileConverterProtocol


logger = logging.getLogger(__name__)


class DoclingFileConverter(FileConverterProtocol):

    def __init__(self):
        self.converter = DocumentConverter()

    def convert_to_markdown(self, file_path: str) -> str:
        result = self.converter.convert(file_path)

        logger.info(
            f"Docling conversion confidence for file '{file_path}' (mean grade: {result.confidence.mean_grade}, low grade: {result.confidence.low_grade})"
        )

        doc = result.document
        markdown = doc.export_to_markdown()
        return markdown


docling_converter = DoclingFileConverter()
