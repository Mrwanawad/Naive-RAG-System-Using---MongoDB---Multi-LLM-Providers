import os
from fastapi import FastAPI, APIRouter, Depends
from helpers.config import get_settings, Settings

base_router = APIRouter(
    prefix= '/api/v1',
    tags = [ 'api_v1' ]
)


@base_router.get( '/' )
async def read_root( app_settings: Settings = Depends( get_settings  ) ):
    return {
        'APP Name': get_settings().APP_NAME,
        'APP Version' : get_settings().APP_VERSION
    }