import re
from typing import List
import nltk
from pydantic import BaseModel, Field

from lib.agents.models import ValidatedDocument, DocumentMetadata
from lib.models.agent import AgentProtocol

# Download required NLTK data
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    try:
        nltk.download("punkt_tab")
    except:
        # Fallback to older punkt tokenizer
        nltk.download("punkt")


class Paragraph(BaseModel):
    chunks: List[str] = Field(
        description="The chunks extracted from the paragraph, that when concatenated should recreate the content of the original paragraph"
    )


class DocumentChunkerResponse(BaseModel):
    paragraphs: List[Paragraph] = Field(
        description="The paragraphs extracted from the document, each with sentence-level chunks. When these chunks are all concatenated, they should recreate the content of the original document"
    )


def get_chunker_result_as_langchain_documents(
    chunker_result: DocumentChunkerResponse,
) -> List[ValidatedDocument]:
    chunks = []
    chunk_index = 0
    for paragraph_index, paragraph in enumerate(chunker_result.paragraphs):
        for index_within_paragraph, chunk in enumerate(paragraph.chunks):
            chunks.append(
                ValidatedDocument(
                    page_content=chunk,
                    metadata=DocumentMetadata(
                        paragraph_index=paragraph_index,
                        chunk_index=chunk_index,
                        chunk_index_within_paragraph=index_within_paragraph,
                    ),
                )
            )
            chunk_index += 1
    return chunks


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs based on double newlines or markdown heading patterns.
    Preserves markdown headings as separate paragraphs.
    """
    # Split on double newlines first
    paragraphs = re.split(r"\n\s*\n", text)

    # Further split paragraphs that contain markdown headings
    final_paragraphs = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Check if paragraph starts with a markdown heading
        if re.match(r"^#{1,6}\s+", paragraph):
            final_paragraphs.append(paragraph)
        else:
            # Split on single newlines that are followed by markdown headings
            parts = re.split(r"\n(?=#{1,6}\s+)", paragraph)
            for part in parts:
                part = part.strip()
                if part:
                    final_paragraphs.append(part)

    return final_paragraphs


def split_paragraph_into_sentences(paragraph: str) -> List[str]:
    """
    Split a paragraph into sentences using NLTK's sentence tokenizer.
    Handles special cases for markdown formatting.
    """
    # Check if this is a markdown heading
    if re.match(r"^#{1,6}\s+", paragraph):
        return [paragraph.strip()]

    # Check if this is a code block
    if paragraph.startswith("```"):
        return [paragraph.strip()]

    # For list items, we still want to split into sentences
    # but preserve the list marker
    if (
        paragraph.startswith("- ")
        or paragraph.startswith("* ")
        or paragraph.startswith("1. ")
    ):
        # Extract the list marker
        if paragraph.startswith("- "):
            marker = "- "
        elif paragraph.startswith("* "):
            marker = "* "
        elif paragraph.startswith("1. "):
            marker = "1. "
        else:
            marker = ""

        # Remove the marker and split into sentences
        content = paragraph[len(marker) :].strip()
        sentences = nltk.sent_tokenize(content)

        # Clean up sentences and add marker back to first sentence
        cleaned_sentences = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                if i == 0 and marker:
                    cleaned_sentences.append(f"{marker}{sentence}")
                else:
                    cleaned_sentences.append(sentence)

        return cleaned_sentences

    # Use NLTK sentence tokenizer for regular text
    sentences = nltk.sent_tokenize(paragraph)

    # Clean up sentences (remove extra whitespace)
    cleaned_sentences = [s.strip() for s in sentences if s.strip()]

    return cleaned_sentences


class DocumentChunkerAgent(AgentProtocol):
    name = "Document Chunker (NLTK)"
    description = "Chunk a document into paragraphs and each paragraph into sentence-level chunks using NLTK"

    def __init__(self):
        pass

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config=None,
    ) -> DocumentChunkerResponse:
        """
        Process a document using NLTK sentence tokenization.

        Args:
            prompt_kwargs: Dictionary containing 'full_document' key with the document text
            config: Optional configuration (not used in NLTK implementation)

        Returns:
            DocumentChunkerResponse with paragraphs and sentence chunks
        """
        full_document = prompt_kwargs.get("full_document", "")

        if not full_document.strip():
            return DocumentChunkerResponse(paragraphs=[])

        # Split document into paragraphs
        paragraphs = split_into_paragraphs(full_document)

        # Process each paragraph into sentence chunks
        paragraph_objects = []
        for paragraph_text in paragraphs:
            if not paragraph_text.strip():
                continue

            sentences = split_paragraph_into_sentences(paragraph_text)
            if sentences:  # Only add non-empty paragraphs
                paragraph_objects.append(Paragraph(chunks=sentences))

        return DocumentChunkerResponse(paragraphs=paragraph_objects)


document_chunker_agent = DocumentChunkerAgent()
