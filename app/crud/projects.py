import secrets
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic.types import UUID4

from app.models.projects import (
    ProjectCreate, ProjectCreateResponse, ProjectDB, Project,
    ProjectUpdate
)
from app.utils.api_key import hash_api_key


async def get_clients_project(
        db: AsyncIOMotorDatabase,
        project_id: UUID4, user_id: UUID4) -> Optional[ProjectDB]:
    project = await db.projects.find_one(
        {'id': project_id, 'owner_id': user_id})
    if project:
        return ProjectDB(**project)


async def get_clients_projects(
        db: AsyncIOMotorDatabase, user_id: UUID4) -> List[Project]:
    projects: List[Project] = []
    projects_cur = db.projects.find({'owner_id': user_id})
    async for project in projects_cur:
        projects.append(
            Project(
                **project,
                date_created=ObjectId(project['_id']).generation_time
            )
        )
    return projects


async def create_clients_project(
        db: AsyncIOMotorDatabase,
        project_data: ProjectCreate, user_id: UUID4) -> ProjectCreateResponse:
    api_key = secrets.token_urlsafe(32)
    payment_signature_secret = secrets.token_urlsafe(32)
    project_data = project_data.dict()
    project_data['owner_id'] = user_id
    project_data['api_key_hashed'] = hash_api_key(api_key)
    project_data['payment_signature_secret'] = payment_signature_secret
    result = await db.projects.insert_one(ProjectDB(**project_data).dict())
    project = await db.projects.find_one(result.inserted_id)
    return ProjectCreateResponse(
        **project,
        date_created=ObjectId(project['_id']).generation_time,
        api_key=api_key
    )


async def update_clients_project(
        db: AsyncIOMotorDatabase,
        project_id: UUID4,
        update_data: ProjectUpdate) -> Project:
    await db.projects.update_one(
        {'id': project_id}, {'$set': update_data.dict()})
    project = await db.projects.find_one({'id': project_id})
    return Project(
        **project,
        date_created=ObjectId(project['_id']).generation_time
    )


async def delete_clients_project(
        db: AsyncIOMotorDatabase, project_id: UUID4
) -> None:
    await db.projects.delete_one({'id': project_id})


async def get_new_api_key(db: AsyncIOMotorDatabase, project: ProjectDB) -> str:
    api_key = secrets.token_urlsafe(32)
    await db.projects.update_one(
        {'id': project.id},
        {'$set': {'api_key_hashed': hash_api_key(api_key)}}
    )
    return api_key


async def get_new_payment_signature_secret(
        db: AsyncIOMotorDatabase, project: ProjectDB) -> str:
    payment_signature_secret = secrets.token_urlsafe(32)
    await db.projects.update_one(
        {'id': project.id},
        {'$set': {'payment_signature_secret': payment_signature_secret}}
    )
    return payment_signature_secret
