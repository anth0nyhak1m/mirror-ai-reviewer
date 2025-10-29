import mimetypes
import os

from pydantic import BaseModel, Field

from lib.services.converters.base import convert_to_markdown


class FileDocument(BaseModel):
    file_name: str = Field(
        description="The original name of the uploaded file, as saved in the user file system"
    )
    file_path: str = Field(
        description="The path to the uploaded file, as saved in the file system"
    )
    file_type: str = Field(description="The MIME type of the uploaded file")
    markdown: str = Field(description="The uploaded file content converted to markdown")


async def create_file_document_from_path(
    file_path: str, original_file_name: str = None
) -> FileDocument:
    # Verify file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")

    file_name = original_file_name or os.path.basename(file_path)
    file_type = mimetypes.guess_type(file_name)[0] or "text/plain"

    file_document = FileDocument(
        file_path=str(file_path),
        file_name=file_name,
        file_type=file_type,
        markdown=convert_to_markdown(file_path),
    )

    return file_document
