from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.investigation_service import InvestigationService
from packages.persistence.database import get_session

router = APIRouter(prefix="/investigations", tags=["investigations"])


class CreateInvestigationRequest(BaseModel):
    seed_url: str
    objective: str
    config: dict = {}


class InvestigationStatusResponse(BaseModel):
    id: str
    status: str
    progress: dict


class InvestigationResultsResponse(BaseModel):
    summary: str
    completion_status: str
    coverage: dict
    matches: list[dict]
    ambiguous: list[dict]


@router.post("", response_model=InvestigationStatusResponse, status_code=201)
async def create_investigation(
    body: CreateInvestigationRequest,
    session: AsyncSession = Depends(get_session),
):
    svc = InvestigationService(session)
    inv = await svc.create(body.seed_url, body.objective)
    return InvestigationStatusResponse(
        id=inv.id,
        status=inv.status,
        progress={},
    )


@router.get("/{investigation_id}", response_model=InvestigationStatusResponse)
async def get_investigation(
    investigation_id: str,
    session: AsyncSession = Depends(get_session),
):
    svc = InvestigationService(session)
    result = await svc.get_progress(investigation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return result


@router.get("/{investigation_id}/results", response_model=InvestigationResultsResponse)
async def get_results(
    investigation_id: str,
    session: AsyncSession = Depends(get_session),
):
    svc = InvestigationService(session)
    result = await svc.get_results(investigation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return result
