from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from models.db_schemas import RetrievelDocument
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import uuid

class QdrantDBProvider(VectorDBInterface):
    
    def __init__(self, db_path: str, distance_method: str):
        self.client = None
        self.db_path = db_path
        self.distance_method = None
        
        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = Distance.DOT
            
        self.logger = logging.getLogger(__name__)       
        
    def connect(self):
        self.client = QdrantClient(path = self.db_path)
        
    def disconnect(self):
        self.client = None
        
    def is_collection_existed(self, collection_name) -> bool:
        return self.client.collection_exists(collection_name= collection_name) 
    
    def list_all_collections(self, collection_name) -> List:
        return self.client.get_collections()           
    
    def get_collection_info(self, collection_name: str) -> Dict:
        return self.client.get_collection(collection_name= collection_name)    
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name= collection_name):
            if not self.delete_all_points(collection_name=collection_name):
                return False

            is_deleted = self.client.delete_collection(collection_name= collection_name)
            if self.is_collection_existed(collection_name= collection_name):
                self.logger.error(f'Failed to delete vector DB collection: {collection_name}')
                return False
            return is_deleted

        return True

    def delete_all_points(self, collection_name: str, batch_size: int = 100):
        next_page_offset = None

        while True:
            records, next_page_offset = self.client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=next_page_offset,
                with_payload=False,
                with_vectors=False
            )

            point_ids = [record.id for record in records]
            if point_ids:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=point_ids,
                    wait=True
                )

            if next_page_offset is None:
                break

        collection_info = self.client.get_collection(collection_name=collection_name)
        return collection_info.points_count == 0
        
    def create_collection(self, collection_name, embedding_size, do_reset = False):
        if do_reset:
            _ = self.delete_collection(collection_name= collection_name)
            
        if not self.is_collection_existed(collection_name= collection_name):
            _ = self.client.create_collection(
                collection_name= collection_name,
                vectors_config= VectorParams(
                    size= embedding_size,
                    distance= self.distance_method
                )
            )
            return True
        
        return False
    
    
    def insert_one(self, collection_name, text, vector, metadata = None, record_id = None):
        if not self.is_collection_existed(collection_name):
            self.logger.error(f'Can not insert new record to non-existed collection: {collection_name}')
            return False
        
        if record_id is None:
            record_id = str(  uuid.uuid4()  )
        
        _ = self.client.upsert(
            collection_name= collection_name,
            points= [
                PointStruct(
                    id= record_id,
                    vector= vector,
                    payload= { 'text': text, 'metadata': metadata }
                )
            ]
        )
        return True
    
    def insert_many(self, collection_name: str, texts: List[List], vectors: List[List], metadatas = None, record_ids = None, batch_size = 50):
        
        if metadatas is None:
            metadatas = [None] * len(texts)
            
        if record_ids is None:
            record_ids = [str(uuid.uuid4()) for _ in texts]
            
        for i in range( 0, len(texts), batch_size ):
            batch_end = i + batch_size
            batch_ids = record_ids[ i : batch_end ]
            batch_texts = texts[ i : batch_end ]
            batch_vectors = vectors[ i : batch_end ]    
            batch_metadatas = metadatas[ i : batch_end ]
            
            batch_records = [
                PointStruct(
                    id= batch_ids[x],
                    vector= batch_vectors[x],
                    payload= { 'text': batch_texts[x], 'metadata': batch_metadatas[x] }
                )
                
                for x in range(  len(batch_texts)  )
            ]
            
            try:
                self.client.upsert(
                    collection_name= collection_name,
                    points= batch_records,
                    wait=True
                )
            except Exception as e:
                self.logger.error(f'Error while Inserting record with number: {i} | Error: {e}')    
                return False
                
        return True    
    
    
    def search_by_vector(self, collection_name, vector, limit: int = 5):
        results =  self.client.query_points(
            collection_name= collection_name,
            query= vector,
            limit= limit
        )

        if not results or len( results.model_dump() ) == 0:
            return None
        
        return [
            RetrievelDocument( **{
                "score": result.score,
                "text": result.payload.get("text")
            } )
            for result in results.points
        ]