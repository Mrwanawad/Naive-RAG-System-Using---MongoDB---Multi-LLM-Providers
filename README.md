# mini-RAG

`mini-RAG` is a modular Retrieval-Augmented Generation backend built with FastAPI. It ingests local documents, stores metadata in MongoDB, chunks and persists text, indexes embeddings in a vector database, and answers queries through pluggable LLM providers.

## What This Project Does

The application is designed around a simple RAG pipeline:

1. Upload a document to a project.
2. Store the original file on disk and record its metadata in MongoDB.
3. Process the file into chunks.
4. Push the chunks into a vector database with embeddings.
5. Search the indexed content or generate an answer with retrieved context.

## Tech Stack

- Python 3.12+
- FastAPI for the HTTP API
- Uvicorn for the ASGI server
- MongoDB via `motor` for project, asset, and chunk metadata
- PostgreSQL support is initialized through `sqlalchemy` and `asyncpg`
- Qdrant for vector storage
- LangChain document loaders and text splitters
- OpenAI, Cohere, and OpenRouter as LLM/embedding backends

## Architecture

This codebase follows a layered, provider-driven architecture:

- API layer: `src/routes/*`
- Controller layer: `src/controllers/*`
- Data/model layer: `src/models/*`
- Infrastructure layer: `src/stores/*`
- Configuration layer: `src/helpers/config.py`

### Request Flow

1. `src/main.py` creates the FastAPI app and initializes services in `lifespan`.
2. Route handlers accept requests and call controllers.
3. Controllers handle file validation, project paths, document processing, vector indexing, and RAG prompt assembly.
4. Models encapsulate MongoDB collections and schema validation.
5. Store providers abstract LLM and vector DB vendors behind interfaces and factories.

### Design Patterns Used

- Factory pattern
  - `LLMProviderFactory` selects OpenAI, Cohere, or OpenRouter providers.
  - `VectorDBProviderFactory` selects the vector database implementation.
- Strategy pattern
  - LLM and vector DB providers are swappable implementations behind shared interfaces.
- Layered architecture
  - Routes do not talk directly to databases or providers.
- Adapter-style abstraction
  - Provider classes normalize different vendor APIs behind one internal contract.
- Template-driven prompting
  - `TemplateParser` resolves multilingual prompt templates for RAG generation.

## Supported Capabilities

- Upload documents per project
- Validate file type and file size before storage
- Process `.txt` and `.pdf` files
- Chunk document content with configurable chunk size and overlap
- Store file and chunk metadata in MongoDB
- Index chunks into Qdrant with embeddings
- Search the vector index by semantic similarity
- Generate RAG answers from retrieved chunks
- Switch LLM and embedding providers without changing the route layer
- Support English and Arabic prompt templates

## Repository Structure

```text
.
├── main.py
├── src
│   ├── main.py
│   ├── controllers
│   ├── helpers
│   ├── models
│   ├── routes
│   └── stores
├── docker
├── pyproject.toml
├── uv.lock
└── .env.example
```

### Key Modules

- `src/main.py`
  - Application startup, dependency wiring, and service lifecycle management.
- `src/routes/data.py`
  - File upload and document processing endpoints.
- `src/routes/vector_store.py`
  - Indexing, search, and RAG answer endpoints.
- `src/controllers/ProcessController.py`
  - Loads documents and splits them into chunks.
- `src/controllers/VectorStoreController.py`
  - Embeds text, stores vectors, searches, and builds RAG prompts.
- `src/models/*`
  - MongoDB schemas and collection access helpers.
- `src/stores/llm/*`
  - Vendor-neutral LLM abstraction and provider implementations.
- `src/stores/vectordb/*`
  - Vector database abstraction and Qdrant implementation.

## Prerequisites

Before running the project, install:

- Python 3.12 or newer
- `uv`
- MongoDB
- PostgreSQL
- Qdrant
- API keys for the LLM provider you want to use

## Configuration

Create a `.env` file at the project root. Use `.env.example` as the starting point.

Minimum required settings depend on the backend you select, but the application expects values such as:

- `APP_NAME`
- `APP_VERSION`
- `MONGODB_URL`
- `MONGODB_DATABASE`
- `POSTGRES_USERNAME`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_MAIN_DATABASE`
- `GENERATION_BACKEND`
- `EMBEDDING_BACKEND`
- `VECTOR_DB_BACKEND`

Provider-specific settings may also be required:

- OpenAI
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
- Cohere
  - `COHERE_API_KEY`
- OpenRouter
  - `OPENROUTER_API_KEY`
  - `OPENROUTER_GENERATION_API_URL`
  - `OPENROUTER_EMBEDDING_API_URL`

Vector DB settings:

- `VECTOR_DB_PATH`
- `VECTOR_DB_DISTANCE_METHOD`

Document processing settings:

- `FILE_ALLOWED_TYPES`
- `FILE_MAX_SIZE`
- `FILE_DEFAULT_CHUNK_SIZE`

Language settings:

- `PRIMARY_LANG`
- `DEFAULT_LANG`

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd mini-RAG
```

### 2. Install `uv`

If `uv` is not already installed:

```bash
pip install uv
```

### 3. Create and sync the environment

```bash
uv sync
```

This installs the dependencies from `pyproject.toml` and `uv.lock` into a managed virtual environment.

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in the required values for your local services and provider keys.

## Running the Project

Start the API with:

```bash
cd src
uv run uvicorn main:app --reload
```

The FastAPI application is defined in `main.py`.

## API Overview

Base prefix: `/api/v1`

### `GET /api/v1/`

Returns application name and version.

### `POST /api/v1/data/upload/{project_id}`

Uploads a file for a project, validates it, stores it on disk, and records the asset in MongoDB.

### `POST /api/v1/data/process/{project_id}`

Processes uploaded project files into chunks and stores them in MongoDB.

Parameters:

- `file_id` to process a single file
- `chunk_size`
- `chunk_overlap`
- `do_reset` to clear existing chunks and vector data

### `POST /api/v1/vector-store/index/push/{project_id}`

Embeds stored chunks and pushes them into the vector database.

### `GET /api/v1/vector-store/index/push/{project_id}`

Returns collection information for the project vector index.

### `POST /api/v1/vector-store/index/search/{project_id}`

Runs semantic search over the project vector collection.

### `POST /api/v1/vector-store/index/answer/{project_id}`

Runs the full RAG pipeline and returns the answer, assembled prompt, and chat history.

## Data Flow Details

### Upload

- Files are validated by content type and size.
- The file is saved under `src/assets/files/{project_id}`.
- A generated file name is used to avoid collisions.
- A record is created in the `assets` collection.

### Processing

- `.txt` files are loaded with `TextLoader`.
- `.pdf` files are loaded with `PyMuPDFLoader`.
- Text is split with `RecursiveCharacterTextSplitter`.
- Chunk metadata is preserved and augmented with `file_id`.
- Chunks are saved in the `chunks` collection.

### Indexing

- Each chunk is embedded through the configured LLM provider.
- Vector points are written to the configured Qdrant collection.
- Collection names follow the pattern `collection_{project_id}`.

### Answering

- The query is embedded.
- Similar chunks are retrieved from Qdrant.
- Prompt templates are resolved from the locale system.
- The final prompt is sent to the generation provider.

## Provider Support

### LLM Providers

- OpenAI
- Cohere
- OpenRouter

### Vector Database

- Qdrant




