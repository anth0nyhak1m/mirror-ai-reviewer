AI Reviewer is an automated document analysis system designed to assist in academic peer review by systematically evaluating the relationship between claims and their supporting evidence in research documents. The project goal is to employ most recent LLMs, agent-based workflows and techniques found the most recent literature to help researchers, reviewers, and academics improve the rigor and quality of their work.

## Objectives

The system addresses these primary research questions:

1. **Claim-Reference Alignment**: Does each cited reference provide evidence that substantiates the associated claim?
2. **Missing Substantiation**: Which claims require citation but lack appropriate references?
3. **Citation Recommendations**: What additional references could strengthen the document's evidentiary foundation?
4. **Literature Review**: Is there any other related published work that could be referenced to strengthen or counter the arguments presented?
5. **Live Reports** (for past published documents): Is there any newer related work that supports, strengthens, contradicts, or brings newer information that should be considered to expand the document's arguments?

## Methodology

### Document Processing Pipeline

The system processes documents through a multi-stage pipeline implemented using LangGraph, which orchestrates a series of specialized AI agents:

1. **Document Conversion**: Input documents (PDF, DOCX, Markdown) are converted to structured markdown format while preserving semantic structure.

2. **Document Chunking**: Documents are segmented into semantically coherent chunks using recursive character text splitting. Chunks maintain paragraph boundaries and are sized to preserve context while enabling granular analysis.

3. **Claim Extraction**: An LLM-based agent extracts factual claims from each chunk. Claims are defined as decontextualized propositions—assertions that can be understood and verified independently of their surrounding context. The extraction process considers:

   - Full document context
   - Paragraph-level context
   - Domain-specific knowledge requirements
   - Target audience expectations

4. **Citation Detection**: Citations are identified and mapped to their corresponding references in the document's bibliography. The system handles various citation formats and associates citations with claims based on proximity and paragraph-level context.

5. **Reference Extraction**: Bibliographic references are extracted and structured, enabling mapping between in-text citations and their full reference entries.

6. **Claim Categorization**: Extracted claims are classified into six categories:

   - Established/reported knowledge
   - Methodological/procedural statements
   - Empirical/analytical results
   - Inferential/interpretive claims
   - Meta/structural/evaluative statements
   - Other

   Each category determination includes an assessment of whether external verification is required, filtering out common knowledge claims that do not necessitate citation.

7. **Claim Verification**: Claims are verified against supporting documents using one of two strategies:

   **Citation-Based Verification**: When citations are present, the system retrieves the full text of cited references and evaluates whether they substantiate the claim. The verification considers:

   - Evidence alignment levels: supported, partially supported, unsupported, or unverifiable
   - Scope matching between claim and evidence
   - Tone and strength of language alignment
   - Factual accuracy of numerical or metric claims

   **RAG-Based Verification**: When citations are absent or incomplete, the system employs retrieval-augmented generation:

   - Supporting documents are indexed in a vector store using OpenAI's `text-embedding-3-large` embeddings
   - Documents are chunked (2000 characters with 400-character overlap) and embedded
   - For each claim, an enriched query is constructed combining the claim text, chunk context, and relevant backing information
   - Semantic similarity search retrieves the top-k most relevant passages (k=20) from all supporting documents
   - Retrieved passages are filtered by cosine distance threshold (≤1.0) and presented to the verification agent
   - The LLM evaluates whether retrieved passages substantiate the claim

8. **Inference Validation**: Claims identified as inferential or interpretive are analyzed to detect potential logical fallacies, unsupported leaps, or missing intermediate reasoning steps.

9. **Literature Review** (optional): The system can conduct automated literature reviews by:

   - Searching external sources for supporting or conflicting evidence
   - Identifying newer publications relevant to the claims
   - Evaluating reference quality and source credibility
   - Recommending citation additions, replacements, or discussions

10. **Citation Suggestion** (optional): For claims lacking citations, the system suggests relevant references from the document's bibliography or external sources, considering:
    - Relevance to the claim
    - Source quality and credibility
    - Publication recency
    - Domain appropriateness

### Technical Architecture

**Agent-Based Design**: The system employs a registry-based agent architecture where specialized agents handle distinct tasks:

- Claim extraction agent
- Citation detection agent
- Claim categorization agent
- Claim verification agent (with citation-based and RAG-based variants)
- Reference extraction agent
- Literature review agent
- Citation suggestion agent
- Evidence weighting agent

Each agent implements a common protocol, enabling dynamic composition and replacement of components.

**Workflow Orchestration**: LangGraph manages the execution flow, supporting:

- Conditional node execution based on configuration
- Parallel processing of independent operations
- State persistence and checkpointing for resumable workflows
- Error handling and graceful degradation

**Vector Storage**: Supporting documents are indexed in PostgreSQL with pgvector extension:

- Each document maintains its own collection for efficient retrieval
- Embeddings are generated using OpenAI's text-embedding-3-large model
- Similarity search uses cosine distance metric
- Collections are cached and reused across workflow runs

**State Management**: The workflow maintains a comprehensive state object (`ClaimSubstantiatorState`) that tracks:

- Original documents and their markdown representations
- Extracted chunks with associated metadata
- Claims, citations, and references per chunk
- Verification results and evidence alignments
- Error conditions and recovery information
- Configuration parameters

### LLM Configuration

The system uses GPT-5 (via LangChain) for all agent operations, configured with:

- Temperature: 0.0-0.5 (depending on task determinism requirements)
- Structured output enforcement via Pydantic models
- Timeout handling for reliability
- Langfuse integration for observability and tracing

### Evaluation Framework

The system includes evaluation capabilities for:

- Claim extraction accuracy
- Citation detection precision and recall
- Verification alignment classification
- End-to-end workflow performance

Evaluation datasets are maintained in YAML format with ground truth annotations for systematic testing.

## Limitations and Considerations

1. **LLM Dependencies**: Verification quality depends on the underlying LLM's reasoning capabilities and may exhibit biases or errors inherent to the model.

2. **Reference Availability**: Citation-based verification requires access to full-text versions of cited references. When unavailable, the system falls back to RAG-based verification or marks claims as unverifiable.

3. **Semantic Retrieval**: RAG-based verification relies on semantic similarity, which may retrieve passages that are topically related but do not substantiate specific claims. The verification agent filters these, but false positives are possible.

4. **Common Knowledge Boundaries**: The distinction between claims requiring citation and common knowledge is domain- and audience-dependent. The system's categorization may not align with all disciplinary conventions.

5. **Citation Proximity**: The system associates citations with claims based on paragraph-level proximity. In cases where citations are distant from their claims, associations may be incorrect.

6. **Processing Scale**: Large documents with many claims require significant computational resources. The system supports selective re-evaluation of specific chunks to optimize resource usage.

## Implementation Details

**Technology Stack**:

- Python 3.13+ with FastAPI backend
- LangChain/LangGraph for agent orchestration
- PostgreSQL with pgvector for vector storage
- OpenAI embeddings and chat models
- Next.js frontend for user interface

**Deployment**: The system supports containerized deployment via Docker and includes database migration management through Alembic.

---

_This documentation describes the system's scientific and technical approach. For development setup and usage instructions, see the main [README](../README.md) and [DEVELOPMENT.md](../DEVELOPMENT.md) files._
