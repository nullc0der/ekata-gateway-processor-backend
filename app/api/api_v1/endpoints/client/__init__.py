from fastapi import APIRouter

from app.api.api_v1.endpoints.client.payout_address import (
    payout_address_router)
from app.api.api_v1.endpoints.client.projects import projects_router
from app.api.api_v1.endpoints.client.payout import payouts_router

clients_router = APIRouter()

clients_router.include_router(
    payout_address_router, prefix='/payout-address')
clients_router.include_router(projects_router, prefix='/projects')
clients_router.include_router(payouts_router, prefix='/payouts')
