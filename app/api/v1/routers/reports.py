from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.report import BalanceSheetResponse, IncomeStatementResponse, CashFlowStatementResponse, NetWorthResponse
from app.application.services.report_service import ReportService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.report_repo import ReportRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository
from app.domain.money import MissingExchangeRatesCollectedError

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


def _make_report_service(db: AsyncSession) -> ReportService:
    return ReportService(
        report_repo=ReportRepository(db),
        journal_repo=JournalRepository(db),
        market_price_repo=MarketPriceRepository(db),
    )


@router.get(
    "/balance-sheet",
    response_model=BalanceSheetResponse,
    summary="Generate a balance sheet report",
)
async def get_balance_report(
    journal_id: UUID = Query(...),
    date: date | None = Query(default=None, description="As of date (default: today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceSheetResponse:
    """Returns a balance sheet snapshot at the given date."""
    from datetime import date as date_type
    as_of = date or date_type.today()
    try:
        return await _make_report_service(db).generate_balance_sheet(
            owner_id=current_user.id,
            journal_id=journal_id,
            as_of=as_of,
        )
    except MissingExchangeRatesCollectedError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "calculating_error",
                "message": "Report cannot be generated due to missing exchange rates.",
                "missing_rates": e.missing_rates
            }
        )


@router.get(
    "/income-statement",
    response_model=IncomeStatementResponse,
    summary="Generate an income statement report",
)
async def get_income_report(
    journal_id: UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncomeStatementResponse:
    """Returns an income statement for a specific period."""
    try:
        return await _make_report_service(db).generate_income_statement(
            owner_id=current_user.id,
            journal_id=journal_id,
            date_from=date_from,
            date_to=date_to,
        )
    except MissingExchangeRatesCollectedError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "calculating_error",
                "message": "Report cannot be generated due to missing exchange rates.",
                "missing_rates": e.missing_rates
            }
        )


@router.get("/cash-flow", response_model=CashFlowStatementResponse, summary="Generate cash-flow report",)
async def get_cash_flow(
    journal_id: UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
)->CashFlowStatementResponse:
    """Cash Flow Report-for specific period"""
    try:
        return await _make_report_service(db).generate_cash_flow(
            owner_id=current_user.id,
            journal_id=journal_id,
            date_from=date_from,
            date_to=date_to
        )
    except MissingExchangeRatesCollectedError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "calculating_error",
                "message": "Report cannot be generated due to missing exchange rates.",
                "missing_rates": e.missing_rates
            }
        )


@router.get("/net-worth", response_model=NetWorthResponse)
async def get_net_worth(
    journal_id: UUID = Query(...),
    db:AsyncSession=Depends(get_db),
    current_user: User = Depends(get_current_user),
)->NetWorthResponse:
    """For networth for display"""
    try:
        return await _make_report_service(db).get_net_worth(current_user.id, journal_id)
    except MissingExchangeRatesCollectedError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "calculating_error",
                "message": "Report cannot be generated due to missing exchange rates.",
                "missing_rates": e.missing_rates
            }
        )

from app.api.v1.schemas.report import MonthlyIncomeResponse

@router.get("/monthly-income", response_model=MonthlyIncomeResponse)
async def get_monthly_income(
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyIncomeResponse:
    """For monthly income display"""
    try:
        return await _make_report_service(db).get_monthly_income(current_user.id, journal_id)
    except MissingExchangeRatesCollectedError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "calculating_error",
                "message": "Report cannot be generated due to missing exchange rates.",
                "missing_rates": e.missing_rates
            }
        )

from app.api.v1.schemas.report import ROIReportResponse

@router.get("/roi", response_model=ROIReportResponse, summary="Generate ROI report")
async def get_roi_report(
    journal_id: UUID = Query(...),
    date: date | None = Query(default=None, description="As of date (default: today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ROIReportResponse:
    """Returns the ROI for all asset accounts with a cost basis."""
    from datetime import date as date_type
    as_of = date or date_type.today()
    return await _make_report_service(db).generate_roi_report(
        owner_id=current_user.id,
        journal_id=journal_id,
        as_of=as_of,
    )


@router.get("/roi-timeline", summary="Month-by-month ROI timeline with exchange rate")
async def get_roi_timeline(
    journal_id: UUID = Query(...),
    commodity: str = Query(..., description="The asset commodity, e.g. BTC"),
    cost_commodity: str = Query(..., description="The cost currency, e.g. USD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Returns month-by-month cumulative cost basis, current value, net return,
    and exchange rate for a specific investment commodity pair.
    Used by the dual-axis bar+line chart on the ROI page.
    """
    return await _make_report_service(db).generate_roi_timeline(
        owner_id=current_user.id,
        journal_id=journal_id,
        commodity=commodity,
        cost_commodity=cost_commodity,
    )

from fastapi.responses import HTMLResponse
import plotly.graph_objects as go

@router.get("/htmx/roi-chart", response_class=HTMLResponse, summary="HTMX ROI chart")
async def get_htmx_roi_chart(
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date
    report_service = _make_report_service(db)
    
    roi_report = await report_service.generate_roi_report(
        owner_id=current_user.id,
        journal_id=journal_id,
        as_of=date.today(),
    )
    
    if not roi_report.assets:
        return "<p class='text-xs text-gray-400 text-center mt-16'>No historical data available yet.</p>"
        
    pairs = list(dict.fromkeys((a.commodity, a.cost_commodity) for a in roi_report.assets))
    lineColors = ['#f59e0b','#6366f1','#10b981','#ef4444','#3b82f6','#ec4899','#8b5cf6','#14b8a6']
    
    fig = go.Figure()
    
    for i, (commodity, cost_commodity) in enumerate(pairs):
        timeline_data = await report_service.generate_roi_timeline(
            owner_id=current_user.id, 
            journal_id=journal_id, 
            commodity=commodity, 
            cost_commodity=cost_commodity
        )
        timeline = timeline_data.get("timeline", [])
        if not timeline:
            continue
            
        months = [d["month"] for d in timeline]
        rois = []
        for d in timeline:
            cum = float(d["cum_cost"])
            net = d["net_return"]
            if cum > 0 and net is not None:
                rois.append(float(net) / cum * 100)
            else:
                rois.append(None)
                
        color = lineColors[i % len(lineColors)]
        fig.add_trace(go.Scatter(
            x=months, y=rois,
            mode='lines+markers',
            name=f"{commodity} ROI%",
            line=dict(color=color, width=2.5, shape='spline', smoothing=1.2),
            marker=dict(size=4, color=color),
            connectgaps=True,
            hovertemplate='<b>%{x}</b><br>ROI: %{y:+.2f}%<extra>'+f"{commodity} ROI%"+'</extra>'
        ))
        
    if not fig.data:
        return "<p class='text-xs text-gray-400 text-center mt-16'>No historical data available yet.</p>"
        
    fig.update_layout(
        margin=dict(t=10, r=15, b=50, l=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=11, color='#374151'),
        legend=dict(orientation='h', y=-0.18, x=0),
        xaxis=dict(type='category', tickangle=-25, gridcolor='#f3f4f6', linecolor='#e5e7eb', tickfont=dict(size=10)),
        yaxis=dict(title='ROI %', gridcolor='#f3f4f6', linecolor='#e5e7eb', zeroline=True, zerolinecolor='#d1d5db', zerolinewidth=1, ticksuffix='%', tickfont=dict(size=10)),
        height=280
    )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)