import base64
import logging
from abc import ABC, abstractmethod
from io import BytesIO

from celery.result import AsyncResult
from fastapi import HTTPException
from src.Shared.ConversionModels import (BatchConversionJobResult,
                                         ConversationJobResult,
                                         ConversionResult, ImageData)

logging.basicConfig(level=logging.INFO)
IMAGE_RESOLUTION_SCALE = 4


class DocumentConversionBase(ABC):
    @abstractmethod
    def convert(
        self,
        document: tuple[str, BytesIO],
        extract_tables: bool = True,
        image_resolution_scale: int = IMAGE_RESOLUTION_SCALE,
    ) -> ConversionResult:
        pass

    @abstractmethod
    def convert_batch(
        self, documents: list[tuple[str, BytesIO]], **kwargs
    ) -> list[ConversionResult]:
        pass


class DoclingDocumentConversion(DocumentConversionBase):
    def _setup_pipeline_options(
        self, extract_tables: bool, image_resolution_scale: int
    ):
        # Lazy import pipeline options and OCR options
        from docling.datamodel.pipeline_options import (EasyOcrOptions,
                                                        PdfPipelineOptions)

        artifacts_path = "/Users/Z0084K9/Downloads/docling-models"
        pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path)
        pipeline_options.images_scale = image_resolution_scale
        pipeline_options.generate_page_images = False
        pipeline_options.generate_table_images = extract_tables
        pipeline_options.generate_picture_images = True
        pipeline_options.ocr_options = EasyOcrOptions(lang=["fr", "de", "es", "en", "it", "pt"])
        return pipeline_options

    @staticmethod
    def _process_document_images(conv_res) -> tuple[str, list[ImageData]]:
        # Lazy imports for image processing (base64, BytesIO are already imported)
        from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

        images = []
        table_counter = 0
        picture_counter = 0
        content_md = conv_res.document.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)

        for element, _level in conv_res.document.iterate_items():
            # Use tuple for union check
            if isinstance(element, (TableItem, PictureItem)) and element.image:
                img_buffer = BytesIO()
                element.image.pil_image.save(img_buffer, format="PNG")

                if isinstance(element, TableItem):
                    table_counter += 1
                    image_name = f"table-{table_counter}.png"
                    image_type = "table"
                else:
                    picture_counter += 1
                    image_name = f"picture-{picture_counter}.png"
                    image_type = "picture"
                    content_md = content_md.replace("<!-- image -->", image_name, 1)

                image_bytes = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
                images.append(ImageData(type=image_type, filename=image_name, image=image_bytes))

        return content_md, images

    def convert(
        self,
        document: tuple[str, BytesIO],
        extract_tables: bool = True,
        image_resolution_scale: int = IMAGE_RESOLUTION_SCALE,
        **kwargs,
    ) -> ConversionResult:
        filename, file = document

        # If the file is a .txt file, read and return its content directly.
        if filename.lower().endswith(".txt"):
            content = file.read().decode("utf-8")
            return ConversionResult(filename=filename, markdown=content, images=[])

        # Lazy import the document converter and related classes
        from docling.datamodel.base_models import DocumentStream, InputFormat
        from docling.document_converter import (DocumentConverter,
                                                PdfFormatOption)

        pipeline_options = self._setup_pipeline_options(
            extract_tables=extract_tables, image_resolution_scale=image_resolution_scale
        )
        doc_converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )

        conv_res = doc_converter.convert(DocumentStream(name=filename, stream=file), raises_on_error=False)
        doc_filename = conv_res.input.file.stem

        if conv_res.errors:
            logging.error(f"Failed to convert {filename}: {conv_res.errors[0].error_message}")
            return ConversionResult(filename=doc_filename, error=conv_res.errors[0].error_message)

        content_md, images = self._process_document_images(conv_res)
        return ConversionResult(filename=doc_filename, markdown=content_md, images=images)

    def convert_batch(
        self, documents: list[tuple[str, BytesIO]], **kwargs
    ) -> list[ConversionResult]:
        extract_tables = kwargs.get("extract_tables", False)
        image_resolution_scale = kwargs.get("image_resolution_scale", IMAGE_RESOLUTION_SCALE)
        results = []
        for filename, file in documents:
            if filename.lower().endswith(".txt"):
                content = file.read().decode("utf-8")
                results.append(ConversionResult(filename=filename, markdown=content, images=[]))
            else:
                pipeline_options = self._setup_pipeline_options(extract_tables, image_resolution_scale)
                from docling.datamodel.base_models import (DocumentStream,
                                                           InputFormat)
                from docling.document_converter import (DocumentConverter,
                                                        PdfFormatOption)

                doc_converter = DocumentConverter(
                    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
                )

                conv_res = doc_converter.convert(DocumentStream(name=filename, stream=file), raises_on_error=False)
                doc_filename = conv_res.input.file.stem

                if conv_res.errors:
                    logging.error(f"Failed to convert {filename}: {conv_res.errors[0].error_message}")
                    results.append(ConversionResult(filename=doc_filename, error=conv_res.errors[0].error_message))
                    continue

                content_md, images = self._process_document_images(conv_res)
                results.append(ConversionResult(filename=doc_filename, markdown=content_md, images=images))
        return results


class DocumentConverterService:
    def __init__(self, document_converter: DocumentConversionBase):
        self.document_converter = document_converter

    def convert_document(self, document: tuple[str, BytesIO], **kwargs) -> ConversionResult:
        result = self.document_converter.convert(document, **kwargs)
        if result.error:
            logging.error(f"Failed to convert {document[0]}: {result.error}")
            raise HTTPException(status_code=500, detail=result.error)
        return result

    def convert_documents(self, documents: list[tuple[str, BytesIO]], **kwargs) -> list[ConversionResult]:
        documents = [(filename, BytesIO(file)) for filename, file in documents]
        return self.document_converter.convert_batch(documents, **kwargs)

    def convert_document_task(self, document: tuple[str, BytesIO], **kwargs) -> ConversionResult:
        if not isinstance(document[1], BytesIO):
            document = (document[0], BytesIO(document[1]))
        return self.document_converter.convert(document, **kwargs)

    def convert_documents_task(self, documents: list[tuple[str, bytes]], **kwargs) -> list[ConversionResult]:
        documents = [(filename, BytesIO(file)) for filename, file in documents]
        return self.document_converter.convert_batch(documents, **kwargs)

    def get_single_document_task_result(self, job_id: str) -> ConversationJobResult:
        """Get the status and result of a document conversion job.
        Returns:
            - IN_PROGRESS: When task is still running
            - SUCCESS: When conversion completed successfully
            - FAILURE: When task failed or conversion had errors
        """
        task = AsyncResult(job_id)
        if task.state == "PENDING":
            return ConversationJobResult(job_id=job_id, status="IN_PROGRESS")
        elif task.state == "SUCCESS":
            result = task.get()
            if result.get("error"):
                return ConversationJobResult(job_id=job_id, status="FAILURE", error=result["error"])
            return ConversationJobResult(job_id=job_id, status="SUCCESS", result=ConversionResult(**result))
        else:
            return ConversationJobResult(job_id=job_id, status="FAILURE", error=str(task.result))

    def get_batch_conversion_task_result(self, job_id: str) -> BatchConversionJobResult:
        """Get the status and results of a batch conversion job.
        Returns:
            - IN_PROGRESS: When task is still running
            - SUCCESS: A batch is successful as long as the task is successful
            - FAILURE: When the task fails for any reason
        """
        task = AsyncResult(job_id)
        if task.state == "PENDING":
            return BatchConversionJobResult(job_id=job_id, status="IN_PROGRESS")
        if task.state == "SUCCESS":
            conversion_results = task.get()
            job_results = []
            for result in conversion_results:
                if result.get("error"):
                    job_result = ConversationJobResult(status="FAILURE", error=result["error"])
                else:
                    job_result = ConversationJobResult(
                        status="SUCCESS", result=ConversionResult(**result).model_dump(exclude_unset=True)
                    )
                job_results.append(job_result)
            return BatchConversionJobResult(job_id=job_id, status="SUCCESS", conversion_results=job_results)
        return BatchConversionJobResult(job_id=job_id, status="FAILURE", error=str(task.result))
