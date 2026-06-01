from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from models.enums import ResponseSignal
from controllers import VectorStoreController
from .schemas.vector_store import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from bson import ObjectId


vector_store_router = APIRouter(
    prefix='/api/v1/vector-store',
    tags=['api_v1', 'vector-store']
)


@vector_store_router.post('/index/push/{project_id}')
async def index_project(request: Request, project_id: str, push_request: PushRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'Signal': ResponseSignal.PROJECT_NOT_FOUND.value}
        )

    vector_store_controller = VectorStoreController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser = request.app.template_parser
        
        
    )

    collection_name = vector_store_controller.create_collection_name(project_id=project.project_id)
    if push_request.do_reset:
        is_deleted = vector_store_controller.vectordb_client.delete_collection(collection_name=collection_name)
        if not is_deleted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'signal': 'vector db collection reset failed'}
            )

    has_records = True
    page_no = 1
    inserted_items_counts = 0
    is_inserted = True

    while has_records:
        page_chunks = await chunk_model.get_project_chunks(
            project_id=ObjectId(project.id),
            page_no=page_no
        )
        if len(page_chunks):
            page_no += 1

        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        is_inserted = vector_store_controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            chunks_ids=None
        )

        inserted_items_counts += len(page_chunks)

    if not is_inserted:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'signal': ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value}
        )

    return JSONResponse(
        content={
            'Signal': ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value,
            'Inserted Items Count': inserted_items_counts
        }
    )


@vector_store_router.get('/index/push/{project_id}')
async def get_project_index_info(request: Request, project_id: str):
    project_model = await ProjectModel.create_instance(request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id)

    vector_store_controller = VectorStoreController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser = request.app.template_parser
        
    )
    collection_info = vector_store_controller.get_vector_db_collection_info(project)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "Signal": ResponseSignal.VECTOR_DB_RETRIERVAL_SUCCESS.value,
            'Collection Info.': collection_info
        }
    )


@vector_store_router.post('/index/search/{project_id}')
async def search_index(request: Request, project_id: str, search_request: SearchRequest):

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )


    project = await project_model.get_project_or_create_one(project_id=project_id)

    vector_store_controller = VectorStoreController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser = request.app.template_parser
        
    )
    
    results = vector_store_controller.search_vector_db_collection(
        project= project, text= search_request.text,
        limit= search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'signal': ResponseSignal.VECTOR_DB_SEARCH_ERROR.value}
        )
        
    return JSONResponse(
        content= {
            'Signal': ResponseSignal.VECTOR_DB_SEARCH_SUCCESS.value,           
            'Results': [ result.dict() for result in results  ]
        }
        
    )    
    
    
        
@vector_store_router.post('/index/answer/{project_id}')
async def answer_rag_qs(request: Request, project_id: str, search_request: SearchRequest):

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )


    project = await project_model.get_project_or_create_one(project_id=project_id)

    vector_store_controller = VectorStoreController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser = request.app.template_parser
    )
    

    answer, full_prompt, chat_history = vector_store_controller.answer_rag_qs(
        project= project,  query = search_request.text,
        limit= search_request.limit
    )
    
    if not answer:
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content= {
                'Signal': ResponseSignal.RAG_ANSWER_ERROR.value
            }
        )
        
    return JSONResponse(
        content= {
            'Signal': ResponseSignal.RAG_ANSWER_sUCCESS.value,
            'answer': answer,
            'full_prompt': full_prompt,
            'chat_history': chat_history
        }
    )            