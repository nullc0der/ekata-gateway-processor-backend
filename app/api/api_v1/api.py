from fastapi import APIRouter

from app.api.api_v1.endpoints import (auth, users, client, payment_form)

api_router = APIRouter()

api_router.include_router(auth.auth_router, prefix='/auth', tags=['auth'])
api_router.include_router(users.users_router, prefix='/users', tags=['users'])
api_router.include_router(
    client.clients_router, prefix='/client', tags=['client'])
api_router.include_router(
    payment_form.router, prefix='/payment-form',
    tags=['payment-form'])
