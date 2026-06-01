from helpers.config import get_settings
from .BaseController import BaseController
from models.db_schemas import Project
from stores.vectordb import VectorDBInterface
from stores.llm import LLMInterface
from stores.llm.LLMEnums import DocumentTypeEnums
from stores.llm.system_templates import TemplateParser

import json
import uuid


class VectorStoreController(BaseController):

    def __init__(self, vectordb_client: VectorDBInterface,
                 generation_client: LLMInterface, embedding_client: LLMInterface, template_parser: TemplateParser):
        self.config = get_settings()
        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        return f'collection_{project_id}'.strip()

    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        self.vectordb_client.delete_collection(collection_name)

    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        if not self.vectordb_client.is_collection_existed(collection_name=collection_name):
            return {
                "status": "missing",
                "points_count": 0,
                "collection_name": collection_name,
            }

        collection_info = self.vectordb_client.get_collection_info(collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )

    def index_into_vector_db(self, project, chunks, chunks_ids, do_reset: bool = False):
        collection_name = self.create_collection_name(project_id=project.project_id)

        chunks_texts = [chunk.chunk_text for chunk in chunks]
        chunks_metadatas = [chunk.chunk_metadata for chunk in chunks]

        point_ids = [
            self.create_point_id(collection_name=collection_name, chunk=chunk)
            for chunk in chunks
        ]

        vectors = [
            self.embedding_client.embed_text(text=chunk_text)
            for chunk_text in chunks_texts
        ]

        if do_reset:
            self.vectordb_client.delete_collection(collection_name=collection_name)

        if not self.vectordb_client.is_collection_existed(collection_name=collection_name):
            self.vectordb_client.create_collection(
                collection_name=collection_name,
                embedding_size=len(vectors[0])
            )

        self.vectordb_client.insert_many(
            collection_name=collection_name,
            record_ids=point_ids,
            texts=chunks_texts,
            vectors=vectors,
            metadatas=chunks_metadatas
        )

        return True

    def create_point_id(self, collection_name: str, chunk):
        metadata = chunk.chunk_metadata or {}
        source = metadata.get("source") or metadata.get("file_id") or ""
        page = metadata.get("page", "")
        fingerprint = json.dumps(
            {
                "collection": collection_name,
                "source": source,
                "page": page,
                "order": chunk.chunk_order,
            },
            sort_keys=True,
            default=str,
        )

        return str(uuid.uuid5(uuid.NAMESPACE_URL, fingerprint))

    def search_vector_db_collection(self, project: Project, text: str, limit: int):
        collection_name = self.create_collection_name(project_id=project.project_id)
        
        vector = self.embedding_client.embed_text(
            text= text, document_type= DocumentTypeEnums.QUERY.value
        )
        
        if not vector or len(vector) == 0:
            return False
        
        results = self.vectordb_client.search_by_vector(
            collection_name= collection_name,
            vector= vector,
            limit= limit
        )
        if not results:
            return False
        
        return results
    
    
    def answer_rag_qs(self, project: Project, query: str, limit: int=10 ): 
        retrieved_documents = self.search_vector_db_collection(
            project= project,
            text= query,
            limit=limit
        )
        if not retrieved_documents or len(retrieved_documents) == 0:
            return None   
        
        # Construct LLM Prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")
        documents_prompts = [
            self.template_parser.get("rag", "document_prompt", {
                "doc_num": idx,
                "chunk_text": doc.text
            })
            for idx, doc in enumerate(retrieved_documents, start=1)
        ]
        
        footer_prompt = self.template_parser.get("rag", "footer_prompt", {"query": query})

        chat_history = [
            self.generation_client.construct_prompt(
                prompt= system_prompt,
                role= self.generation_client.enums.SYSTEM.value
            )
        ]
        
        full_prompt = "\n\n".join(
            [doc_prompt for doc_prompt in documents_prompts] + [footer_prompt]
        )
        
        answer = self.generation_client.generate_text(
            prompt= full_prompt,
            chat_history= chat_history
        )
        
        return answer, full_prompt, chat_history