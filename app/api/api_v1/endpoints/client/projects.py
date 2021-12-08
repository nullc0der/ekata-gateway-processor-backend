from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends, Query
from pydantic.types import UUID4
from starlette.exceptions import HTTPException
from starlette import status

from app.db import get_default_database
from app.models.projects import (
    Project, ProjectCreate, ProjectCreateResponse, ProjectStats, ProjectUpdate)
from app.models.users import User
from app.crud import projects, payments
from app.api.api_v1.dependencies.auth import current_active_verified_user
from app.permissions import auth as auth_permissions
from app.utils.projects import check_payout_address_added

projects_router = APIRouter()


@projects_router.get('', response_model=List[Project])
async def get_projects(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    clients_projects = await projects.get_clients_projects(db, user.id)
    return clients_projects


@projects_router.post('', response_model=ProjectCreateResponse)
async def create_project(
        project_data: ProjectCreate,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    await check_payout_address_added(db, user, project_data)
    project = await projects.create_clients_project(db, project_data, user.id)
    return project


@projects_router.patch('/{project_id}', response_model=Project)
async def update_project(
        project_id: UUID4,
        project_update_data: ProjectUpdate,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    await check_payout_address_added(db, user, project_update_data)
    project = await projects.get_clients_project(db, project_id, user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested project not found'
        )
    auth_permissions.is_user_is_owner_of_obj(user, project)
    project = await projects.update_clients_project(
        db, project_id, project_update_data)
    return project


@projects_router.delete('/{project_id}')
async def delete_project(
        project_id: UUID4,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    project = await projects.get_clients_project(db, project_id, user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested project not found'
        )
    auth_permissions.is_user_is_owner_of_obj(user, project)
    await projects.delete_clients_project(db, project_id)


@projects_router.get('/{project_id}/payments')
async def get_projects_payments(
        project_id: UUID4,
        limit: int = 5,
        page_number: Optional[int] = Query(
            None, alias='page-number'),
        search: str = '',
        currency_name: str = '',
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    project = await projects.get_clients_project(
        db, project_id, user_id=user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested project not found'
        )
    auth_permissions.is_user_is_owner_of_obj(user, project)
    projects_payments = await payments.get_projects_payments(
        db, project_id, limit, page_number, search, currency_name)
    return projects_payments


@projects_router.get('/stats', response_model=ProjectStats)
async def get_projects_stats(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    clients_projects = await projects.get_clients_projects(db, user_id=user.id)
    response_data = {
        'total_project': len(clients_projects),
        'verified_domain': 0,
        'active_project': 0,
    }
    for clients_project in clients_projects:
        if clients_project.enabled_currency and\
                len(clients_project.enabled_currency):
            response_data['active_project'] += 1
    return response_data


@projects_router.get('/{project_id}/new-api-key')
async def get_new_api_key(
        project_id: UUID4,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    project = await projects.get_clients_project(db, project_id, user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested project not found'
        )
    auth_permissions.is_user_is_owner_of_obj(user, project)
    api_key = await projects.get_new_api_key(db, project)
    return api_key


@projects_router.get('/{project_id}/new-payment-signature-secret')
async def get_new_payment_signature_secret(
        project_id: UUID4,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    project = await projects.get_clients_project(db, project_id, user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested project not found'
        )
    auth_permissions.is_user_is_owner_of_obj(user, project)
    return await projects.get_new_payment_signature_secret(db, project)
