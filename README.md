# mini-rag

mini-rag is a FastAPI-based RAG backend that ingests files, stores project assets in MongoDB, splits documents into chunks, and indexes those chunks into a local Qdrant vector database. The generation and embedding layer is provider-driven, so the same application can run against OpenAI, Cohere, or OpenRouter-backed models through a common interface.

## What Changed From The Earlier README

The previous README only covered Docker commands. The current project now has:

- a full API surface for upload, processing, indexing, and search
- MongoDB-backed persistence for projects, assets, and chunks
- a vector-store abstraction with a Qdrant implementation
- an LLM abstraction with factory-based provider selection
- file processing for TXT and PDF inputs

## Architecture

The project follows a layered design:

- `routes` expose HTTP endpoints and validate request payloads.
- `controllers` contain workflow logic and coordinate storage, parsing, and indexing.
- `models` encapsulate MongoDB access and domain schemas.
- `stores` hold provider abstractions and concrete adapters for LLM and vector DB backends.
- `helpers` centralize application settings and environment configuration.

The main pattern choices are:

- Factory pattern for provider creation
- Interface/adapter pattern for LLM and vector DB backends
- Controller/service style orchestration for request workflows
- FastAPI lifespan hooks for application bootstrap and shutdown

## Request Flow

1. A client uploads a file to a project.
2. The file is written to the project asset directory and registered in MongoDB.
3. The processing endpoint loads the file with the correct loader based on extension.
4. The text is chunked with `RecursiveCharacterTextSplitter`.
5. Chunks are stored in MongoDB.
6. The vector-store endpoint embeds each chunk and pushes vectors to Qdrant.
7. The search endpoint embeds the query and retrieves the closest matches from Qdrant.

## Project Structure

```text
src/
  main.py
  helpers/
    config.py
  routes/
    base.py
    data.py
    vector_store.py
    schemas/
  controllers/
    BaseController.py
    DataController.py
    ProcessController.py
    ProjectCntroller.py
    VectorStoreController.py
  models/
    BaseDataModel.py
    ProjectModel.py
    AssetModel.py
    ChunkModel.py
    db_schemas/
    enums/
  stores/
    llm/
      LLMInterface.py
      LLMProviderFactory.py
      providers/
    vectordb/
      VectorDBInterface.py
      VectorDBProviderFactory.py
      providers/
```

## Core Modules

### `src/main.py`

Bootstraps the application, initializes external clients in a FastAPI lifespan handler, and registers the routers.

### Controllers

- `DataController` validates uploads and generates unique file names.
- `ProcessController` resolves the file loader and builds chunk documents.
- `VectorStoreController` handles collection naming, indexing, reset, and similarity search.
- `ProjectController` resolves the filesystem location for project data.

### Storage Layer

MongoDB stores the application data model:

- projects
- assets
- document chunks

Qdrant stores vector embeddings and supports similarity search by collection.

### LLM Layer

The LLM layer is provider-agnostic:

- `LLMInterface` defines the contract
- `LLMProviderFactory` chooses the concrete provider
- `OpenAIProvider`, `CoHereProvider`, and `OpenRouterProvider` implement generation and embeddings

The generation and embedding clients are configured separately, so the app can mix providers if needed.

### Vector DB Layer

The vector database abstraction is also provider-based:

- `VectorDBInterface` defines collection and query operations
- `VectorDBProviderFactory` creates the configured backend
- `QdrantDBProvider` implements collection management, bulk insert, and search

## API Endpoints

### Data

- `POST /api/v1/data/upload{project_id}`: upload a file into a project
- `POST /api/v1/data/process/{project_id}`: load, split, and store chunks

### Vector Store

- `POST /api/v1/vector-store/index/push/{project_id}`: embed stored chunks and push them into Qdrant
- `GET /api/v1/vector-store/index/push/{project_id}`: return collection information
- `POST /api/v1/vector-store/index/search/{project_id}`: run similarity search against the project collection

## Configuration

Settings are loaded through `pydantic-settings` from the project `.env` file.

Required groups of settings include:

- application identity: `APP_NAME`, `APP_VERSION`
- file controls: `FILE_ALLOWED_TYPES`, `FILE_MAX_SIZE`, `FILE_DEFAULT_CHUNK_SIZE`
- MongoDB: `MONGODB_URL`, `MONGODB_DATABASE`
- LLM selection: `GENERATION_BACKEND`, `EMBEDDING_BACKEND`
- model configuration: `GENERATION_MODEL_ID`, `EMBEDDING_MODEL_ID`, `EMBEDDING_MODEL_SIZE`
- provider credentials: `OPENAI_API_KEY`, `COHERE_API_KEY`, `OPENROUTER_API_KEY`
- vector DB configuration: `VECTOR_DB_BACKEND`, `VECTOR_DB_PATH`, `VECTOR_DB_DISTANCE_METHOD`

## Dependencies

The current stack uses:

- `fastapi`
- `uvicorn`
- `motor`
- `aiofiles`
- `pymupdf`
- `langchain`
- `langchain-community`
- `openai`
- `cohere`
- `qdrant-client`
- `pydantic-settings`

## Development Notes

- Text files are loaded with `TextLoader`.
- PDFs are loaded with `PyMuPDFLoader`.
- Chunk metadata is preserved and enriched with `file_id`.
- Vector point IDs are generated deterministically from collection and chunk metadata.
- Collection reset is supported both at processing time and indexing time.

## Docker

The repository includes Docker-related assets, but the current README does not assume one fixed deployment path. Use the environment file that matches your runtime target and make sure MongoDB and Qdrant are reachable before starting the API.

