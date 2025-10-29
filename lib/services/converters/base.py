from typing import Protocol
import logging
from lib.config.env import config

logger = logging.getLogger(__name__)


class FileConverterProtocol(Protocol):

    def convert_to_markdown(self, file_path: str) -> str: ...


def convert_to_markdown(file_path: str) -> str:
    logger.info(
        f"Converting file '{file_path}' to markdown using converter: '{config.FILE_CONVERTER}'"
    )

    if config.FILE_CONVERTER == "markitdown":
        from lib.services.converters.markitdown import markitdown_converter

        return markitdown_converter.convert_to_markdown(file_path)

    elif config.FILE_CONVERTER == "docling":
        from lib.services.converters.docling import docling_converter

        return docling_converter.convert_to_markdown(file_path)

    else:
        raise ValueError(f"Invalid file converter: {config.FILE_CONVERTER}")
