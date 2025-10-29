from markitdown import MarkItDown

from lib.services.converters.base import FileConverterProtocol


class MarkitdownFileConverter(FileConverterProtocol):
    def __init__(self):
        self.converter = MarkItDown(enable_plugins=False)

    def convert_to_markdown(self, file_path: str) -> str:
        result = self.converter.convert(file_path)
        return result.markdown


markitdown_converter = MarkitdownFileConverter()
