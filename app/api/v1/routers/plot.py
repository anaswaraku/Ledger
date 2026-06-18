# app/api/v1/routers/accounts.py
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user,get_plot_service
from app.domain.models import User
from app.domain.models.account import AccountType
from app.application.services.plot_service import PlotService
from pydantic import BaseModel
from decimal import Decimal

class PlotDataResponse(BaseModel):
    name:str
    count:int
    amount:Decimal

router = APIRouter(prefix="/api/v1/name", tags=["Plots"])

@router.get("/",response_model=list[str])
async def get_names_by_type(
    journal_id:UUID,
    account_type: AccountType = Query(...),
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
):
    return await plot_service.get_names_by_type(
        current_user.id,
        journal_id,
        account_type
    )

@router.get("/count", response_model=list[PlotDataResponse])
async def get_counts_by_acc(
    journal_id:UUID,
    account_type: AccountType = Query(...),
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
):
    return await plot_service.get_account_entry(
        current_user.id,
        journal_id,
        account_type
    )