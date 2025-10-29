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
    Split text into paragraphs based on single newlines.
    Each line becomes its own paragraph.
    """
    # Split on single newlines - each line becomes a paragraph
    return [line.strip() for line in text.split("\n") if line.strip()]


def split_paragraph_into_sentences(paragraph: str) -> List[str]:
    """
    Split a paragraph into sentences using NLTK's sentence tokenizer.
    Handles special cases for markdown formatting.
    """
    # Check if this is a markdown heading (standalone)
    if re.match(r"^#{1,6}\s+", paragraph):
        return [paragraph.strip()]

    # Check if this is a code block
    if paragraph.startswith("```"):
        return [paragraph.strip()]

    # Reference-style numbered entries: split multiple references into separate chunks
    lines = [ln.strip() for ln in paragraph.split("\n") if ln.strip()]
    if any(re.match(r"^\d+\.\s+", ln) for ln in lines):
        # This paragraph contains numbered references
        chunks = []
        for line in lines:
            if re.match(r"^\d+\.\s+", line):
                # This is a numbered reference item - keep as one chunk
                chunks.append(line)
            else:
                # Continuation line - attach to previous chunk
                if chunks:
                    chunks[-1] = f"{chunks[-1]} {line}"
                else:
                    chunks.append(line)
        return chunks

    # Detect unnumbered citations/references
    # Must start VERY specifically like a citation
    has_year = re.search(r"\b(19|20)\d{2}\b", paragraph)
    starts_like_citation = (
        # Author format: "LastName, FirstInitial."
        re.match(r"^[A-Z][a-z]+,\s+[A-Z]\.", paragraph)
        or
        # Organization with year early: "Org Name (Acronym). (Year)"
        (
            re.match(r"^[A-Z].*\(.*\)\.\s*\(", paragraph)
            and len(paragraph.split()[0]) > 2
        )
    )

    if has_year and starts_like_citation:
        return [paragraph.strip()]

    # For list items (-, *) we want sentence-level chunks, while preserving marker on first sentence
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

    # Post-process: merge author with adjacent year in parentheses
    merged: List[str] = []
    for s in cleaned_sentences:
        if merged and re.match(r"^\(\d{4}\)$", s):
            merged[-1] = f"{merged[-1]} {s}"
        else:
            merged.append(s)

    return merged


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
