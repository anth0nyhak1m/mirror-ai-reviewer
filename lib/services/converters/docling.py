import logging
import mimetypes
import os
from asyncio import sleep

import httpx

from lib.config.env import config
from lib.services.converters.base import FileConverterProtocol

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5


class DoclingFileConverter(FileConverterProtocol):

    async def convert_to_markdown(self, file_path: str) -> str:
        async_client = httpx.AsyncClient(timeout=60.0)
        base_url = config.DOCLING_SERVE_API_URL

        url = f"{base_url}/v1/convert/file/async"
        headers = {
            "X-Api-Key": config.DOCLING_SERVE_API_KEY,
        }
        parameters = {
            # See https://github.com/docling-project/docling-serve/blob/main/docs/usage.md for full list of parameters
            "from_formats": ["docx", "html", "pdf", "md", "txt"],
            "to_formats": ["md"],
            "pipeline": "standard",
            "image_export_mode": "placeholder",
            "include_images": False,
            "do_ocr": False,
            "force_ocr": False,
            "ocr_engine": "auto",
            "ocr_lang": ["en"],
            "table_mode": "fast",
            "abort_on_error": False,
            "document_timeout": 60 * 10,  # 10 minutes
        }
        filename = os.path.basename(file_path)
        file_type = mimetypes.guess_type(filename)[0] or "text/plain"

        with open(file_path, "rb") as file:
            files = {"files": (filename, file, file_type)}
            response = await async_client.post(
                url, files=files, params=parameters, headers=headers
            )

        if response.status_code != 200:
            raise Exception(
                f"Failed to convert file '{file_path}' using docling-serve: {response.status_code} {response.text}"
            )

        task = response.json()
        print(task)
        logger.info(
            f"Docling-serve task {task['task_id']} created for conversion of file '{filename}', polling for status"
        )

        while task["task_status"] not in ("success", "failure"):
            logger.info(
                f"Docling-serve task {task['task_id']} is {task['task_status']}, task position {task['task_position']}, polling again in {POLL_INTERVAL_SECONDS} seconds"
            )
            await sleep(POLL_INTERVAL_SECONDS)
            response = await async_client.get(
                f"{base_url}/v1/status/poll/{task['task_id']}", headers=headers
            )
            task = response.json()

        response = await async_client.get(
            f"{base_url}/v1/result/{task['task_id']}", headers=headers
        )
        data = response.json()

        return data["document"]["md_content"]


docling_converter = DoclingFileConverter()
