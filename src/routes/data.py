import os
from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models.enums import ResponseSignal
import logging;         logger = logging.getLogger( 'uvicorn.error' )
from .schemas.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemas import DataChunk, Asset
from models.enums.AssetTypeEnum import AssetTypeEnum

from bson import ObjectId

data_router = APIRouter(
    prefix = '/api/v1/data',
    tags = [ 'api_v1', 'data' ]
)

@data_router.post( '/upload{project_id}' )
async def upload_data( request: Request, project_id: str, file: UploadFile, app_settings= Depends( get_settings ) ):
    
    
    project_model = await ProjectModel.create_instance(
        db_client= request.app.db_client
    )
    
    project = await project_model.get_project_or_create_one( project_id= project_id )
    
    is_valid, res_signal = DataController().validate_uploaded_file( file= file )
    if not is_valid:
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content= {
                'signal': res_signal,
                'file ID': file_id,
                'Project ID':str(  project.id )
            }
        )
        
    project_dir_path = ProjectController().get_project_path( project_id = project_id )
    file_path, file_id = DataController().gen_unique_filename(
        orig_file_name= file.filename,
        project_id= project_id
    )
    
    try:
        async with aiofiles.open( file_path, 'wb' ) as f:
            while chunk := await file.read( get_settings().FILE_DEFAULT_CHUNK_SIZE ):
                await f.write( chunk )
            
    except Exception as e: 
        logger.error( f'Error while uploading file: {e}' )
        return JSONResponse(
            status_code= status.HTTP_400_BAD_REQUEST,
            content = { "signal": ResponseSignal.FILE_UPLOAD_FAILED.value }
        )            
    
    # Store the Assets into the Database
    
    asset_model = await AssetModel.create_instance( db_client= request.app.db_client )
    
    asset_resource = Asset(
        asset_project_id= ObjectId( project.id ),
        asset_type= AssetTypeEnum.FILE.value,
        asset_name= file_id,
        asset_size= os.path.getsize( file_path )
    )
    
    asset_record = await asset_model.create_asset( asset= asset_resource )
            
    return JSONResponse(
        content= { 'signal': ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                   'File ID': file_id,
                   'Project ID': str( project.id ),
                   'Asset ID': str( asset_record.id )}
    )        
    
    
@data_router.post( '/process/{project_id}' )
async def process_endpoint( request: Request, project_id: str, process_request: ProcessRequest ):
        

        chunk_size = process_request.chunk_size
        chunk_overlap = process_request.chunk_overlap
        
        do_reset = process_request.do_reset
        project = await ProjectModel.create_instance( db_client= request.app.db_client )
        project = await project.get_project_or_create_one(project_id=project_id)
        
        project_files_ids = []
        if process_request.file_id:
            project_files_ids = [ process_request.file_id ]
            
        else:
            asset_model = AssetModel( db_client= request.app.db_client )
                
            project_files = await asset_model.get_all_project_assets(
                asset_project_id= ObjectId(project.id),
                asset_type= AssetTypeEnum.FILE.value
            )
            
            project_files_ids = [
                
                record['asset_name']
                for record in project_files
            ]
            
            if len( project_files_ids ) == 0:
                return JSONResponse(
                    content= {
                        'signal': ResponseSignal.NO_FILES_ERROR.value
                    },
                    status_code= status.HTTP_400_BAD_REQUEST
                )
            
        process_controller = ProcessController( project_id= project_id )

        no_of_records = 0
        no_of_files = 0
        
        chunk_model = await ChunkModel.create_instance(
                db_client= request.app.db_client
            )
                    
        if do_reset == 1:
            _ = await chunk_model.delete_chunks_by_project_id(
                project_id= ObjectId(project.id)
            )
            collection_name = f'collection_{project.project_id}'.strip()
            is_deleted = request.app.vector_db_client.delete_collection(collection_name=collection_name)
            if not is_deleted:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'signal': 'vector db collection reset failed'}
                )
        
        for file_id in project_files_ids:
        
            file_content =  process_controller.get_file_content( file_id= file_id )
            
            # IF there was an empty file, do not stop the text loading `Only log the file name havingb the issue`
            if file_content is None:
                logger.error( f'Error while processing file: {file_id}' )
                continue
            
            chunks = process_controller.process_file_content(
                file_content= file_content,
                file_id= file_id,
                chunk_size= chunk_size,
                overlap_size= chunk_overlap
            )
            
            '''            if chunks is None or len( chunks ) == 0:
                return JSONResponse(
                    status_code= status.HTTP_400_BAD_REQUEST,
                    content= { 'Signal': ResponseSignal.PROCESSING_FAILED.value }
                )'''
                

                
            file_chunk_records = [
                DataChunk(
                    chunk_text= chunk.page_content,
                    chunk_metadata= chunk.metadata,
                    chunk_order= i+1,
                    chunk_project_id= ObjectId( project.id )
                    
                    )
            
                for i, chunk in enumerate( chunks )
            ]    
            

            
            no_of_records += await chunk_model.insert_many_chunks(
                chunks= file_chunk_records
            )  
            no_of_files += 1
        
        return JSONResponse(
            content = {
                'Signal': ResponseSignal.PROCESSING_SUCCESS.value,
                'Inserted Chunks': no_of_records,
                'Processd Files': no_of_files
            }
        )
