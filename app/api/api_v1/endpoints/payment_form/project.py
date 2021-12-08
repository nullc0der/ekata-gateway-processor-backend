from fastapi import APIRouter, status, Depends, HTTPException, Query
from pydantic import UUID4
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.payment_form import ProjectInfo
from app.db import get_default_database

project_router = APIRouter()


@project_router.get('/get-project-info', response_model=ProjectInfo)
async def get_project_info(
        project_id: UUID4 = Query(..., alias='project-id'),
        db: AsyncIOMotorDatabase = Depends(get_default_database)):
    project = await db.projects.find_one({'id': project_id})
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested project not found'
        )
    return project
