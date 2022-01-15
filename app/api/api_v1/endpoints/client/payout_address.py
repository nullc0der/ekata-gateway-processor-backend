from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends
from pydantic.types import UUID4
from starlette.exceptions import HTTPException
from starlette import status

from app.db import get_default_database
from app.models.clients_payout_address import (
    PayoutAddress, PayoutAddressCreate, PayoutAddressUpdate
)
from app.models.projects import ProjectUpdate
from app.models.users import UserDB
from app.crud import clients_payout_address, projects
from app.api.api_v1.dependencies.auth.auth import current_active_verified_user
from app.permissions import auth as auth_permissions
from app.worker import arq_manager

payout_address_router = APIRouter()


@payout_address_router.get('', response_model=List[PayoutAddress])
async def get_payout_addresses(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    payout_addresses = \
        await clients_payout_address.get_clients_payout_addresses(
            db, user.id)
    return payout_addresses


@payout_address_router.post('', response_model=PayoutAddress)
async def create_payout_address(
        payout_address_create_data: PayoutAddressCreate,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    payout_addresses = \
        await clients_payout_address.get_clients_payout_addresses(
            db, user.id)
    for payout_address in payout_addresses:
        if payout_address.currency_name\
                == payout_address_create_data.currency_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Payout address for '
                f'{payout_address_create_data.currency_name} already exists'
            )
    payout_address = \
        await clients_payout_address.create_clients_payout_address(
            db, user.id, payout_address_create_data)
    if payout_address.payout_address:
        await arq_manager.pool.enqueue_job(
            'task_create_clients_payout_queue',
            user.id, payout_address.currency_name)
    return payout_address


@payout_address_router.patch(
    '/{payout_address_id}', response_model=PayoutAddress)
async def update_payout_address(
        payout_address_id: UUID4,
        payout_address_update_data: PayoutAddressUpdate,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    payout_address = \
        await clients_payout_address.get_clients_payout_address(
            db, user.id, payout_address_id)
    if not payout_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested payout address not found'
        )
    auth_permissions.is_user_is_owner_of_obj(user, payout_address)
    payout_address = \
        await clients_payout_address.update_clients_payout_address(
            db, payout_address_id, payout_address_update_data)
    return payout_address


@payout_address_router.delete('/{payout_address_id}')
async def delete_payout_address(
        payout_address_id: UUID4,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    payout_address = \
        await clients_payout_address.get_clients_payout_address(
            db, user.id, payout_address_id)
    if not payout_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested payout address not found'
        )
    auth_permissions.is_user_is_owner_of_obj(user, payout_address)
    currency_name =\
        await clients_payout_address.delete_clients_payout_address(
            db, payout_address_id)
    clients_projects = await projects.get_clients_projects(db, user.id)
    for clients_project in clients_projects:
        if clients_project.enabled_currency \
                and currency_name in clients_project.enabled_currency:
            clients_project.enabled_currency.remove(currency_name)
            await projects.update_clients_project(
                db, clients_project.id,
                ProjectUpdate(**clients_project.dict()))
