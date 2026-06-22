from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.report import (
    BalanceSheetResponse,
    CashFlowStatementResponse,
    IncomeStatementResponse,
    MonthlyIncomeResponse,
    NetWorthResponse,
    ROIReportResponse,
)
from app.application.services.report_service import ReportService
from app.dependencies import get_current_user, get_report_service
from app.domain.models.user import User
from app.domain.money import MissingExchangeRatesCollectedError

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


def _exchange_rate_error(e: MissingExchangeRatesCollectedError) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail={
            "error": "calculating_error",
            "message": "Report cannot be generated due to missing exchange rates.",
            "missing_rates": e.missing_rates,
        },
    )


@router.get(
    "/balance-sheet",
    response_model=BalanceSheetResponse,
    summary="Generate a balance sheet report",
)
async def get_balance_report(
    journal_id: UUID = Query(...),
    date: date | None = Query(default=None, description="As of date (default: today)"),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
) -> BalanceSheetResponse:
    from datetime import date as date_type
    as_of = date or date_type.today()
    try:
        return await service.generate_balance_sheet(
            owner_id=current_user.id, journal_id=journal_id, as_of=as_of
        )
    except MissingExchangeRatesCollectedError as e:
        raise _exchange_rate_error(e)


@router.get(
    "/income-statement",
    response_model=IncomeStatementResponse,
    summary="Generate an income statement report",
)
async def get_income_report(
    journal_id: UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
) -> IncomeStatementResponse:
    try:
        return await service.generate_income_statement(
            owner_id=current_user.id, journal_id=journal_id, date_from=date_from, date_to=date_to
        )
    except MissingExchangeRatesCollectedError as e:
        raise _exchange_rate_error(e)


@router.get(
    "/cash-flow",
    response_model=CashFlowStatementResponse,
    summary="Generate cash-flow report",
)
async def get_cash_flow(
    journal_id: UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
) -> CashFlowStatementResponse:
    try:
        return await service.generate_cash_flow(
            owner_id=current_user.id, journal_id=journal_id, date_from=date_from, date_to=date_to
        )
    except MissingExchangeRatesCollectedError as e:
        raise _exchange_rate_error(e)


@router.get(
    "/net-worth",
    response_model=NetWorthResponse,
    summary="Get current net worth",
)
async def get_net_worth(
    journal_id: UUID = Query(...),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
) -> NetWorthResponse:
    try:
        return await service.get_net_worth(current_user.id, journal_id)
    except MissingExchangeRatesCollectedError as e:
        raise _exchange_rate_error(e)


@router.get(
    "/monthly-income",
    response_model=MonthlyIncomeResponse,
    summary="Get current month income total",
)
async def get_monthly_income(
    journal_id: UUID = Query(...),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
) -> MonthlyIncomeResponse:
    try:
        return await service.get_monthly_income(current_user.id, journal_id)
    except MissingExchangeRatesCollectedError as e:
        raise _exchange_rate_error(e)


@router.get("/roi", response_model=ROIReportResponse, summary="Generate ROI report")
async def get_roi_report(
    journal_id: UUID = Query(...),
    date: date | None = Query(default=None, description="As of date (default: today)"),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
) -> ROIReportResponse:
    from datetime import date as date_type
    as_of = date or date_type.today()
    return await service.generate_roi_report(
        owner_id=current_user.id, journal_id=journal_id, as_of=as_of
    )


@router.get("/roi-timeline", summary="Month-by-month ROI timeline with exchange rate")
async def get_roi_timeline(
    journal_id: UUID = Query(...),
    commodity: str = Query(..., description="The asset commodity, e.g. BTC"),
    cost_commodity: str = Query(..., description="The cost currency, e.g. USD"),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
) -> dict:
    return await service.generate_roi_timeline(
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
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(get_current_user),
):
    roi_report = await service.generate_roi_report(
        owner_id=current_user.id,
        journal_id=journal_id,
        as_of=date.today(),
    )

    if not roi_report.assets:
        return "<p class='text-xs text-gray-400 text-center mt-16'>No historical data available yet.</p>"

    pairs = list(dict.fromkeys((a.commodity, a.cost_commodity) for a in roi_report.assets))
    line_colors = ["#f59e0b", "#6366f1", "#10b981", "#ef4444", "#3b82f6", "#ec4899", "#8b5cf6", "#14b8a6"]

    fig = go.Figure()

    for i, (commodity, cost_commodity) in enumerate(pairs):
        timeline_data = await service.generate_roi_timeline(
            owner_id=current_user.id,
            journal_id=journal_id,
            commodity=commodity,
            cost_commodity=cost_commodity,
        )
        timeline = timeline_data.get("timeline", [])
        if not timeline:
            continue

        months = [d["month"] for d in timeline]
        rois = []
        for d in timeline:
            cum = float(d["cum_cost"])
            net = d["net_return"]
            rois.append(float(net) / cum * 100 if cum > 0 and net is not None else None)

        color = line_colors[i % len(line_colors)]
        fig.add_trace(
            go.Scatter(
                x=months,
                y=rois,
                mode="lines+markers",
                name=f"{commodity} ROI%",
                line=dict(color=color, width=2.5, shape="spline", smoothing=1.2),
                marker=dict(size=4, color=color),
                connectgaps=True,
                hovertemplate=f"<b>%{{x}}</b><br>ROI: %{{y:+.2f}}%<extra>{commodity} ROI%</extra>",
            )
        )

    if not fig.data:
        return "<p class='text-xs text-gray-400 text-center mt-16'>No historical data available yet.</p>"

    fig.update_layout(
        margin=dict(t=10, r=15, b=50, l=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="#374151"),
        legend=dict(orientation="h", y=-0.18, x=0),
        xaxis=dict(type="category", tickangle=-25, gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(size=10)),
        yaxis=dict(title="ROI %", gridcolor="#f3f4f6", linecolor="#e5e7eb", zeroline=True, zerolinecolor="#d1d5db", zerolinewidth=1, ticksuffix="%", tickfont=dict(size=10)),
        height=280,
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)