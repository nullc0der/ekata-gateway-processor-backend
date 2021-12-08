from fastapi import APIRouter

from app.api.api_v1.endpoints.payment_form.payment_form import (
    payment_form_router)
from app.api.api_v1.endpoints.payment_form.payment import (
    payment_router)
from app.api.api_v1.endpoints.payment_form.project import (
    project_router
)

router = APIRouter()

router.include_router(payment_form_router)
router.include_router(payment_router, prefix='/payment')
router.include_router(project_router, prefix='/project')
