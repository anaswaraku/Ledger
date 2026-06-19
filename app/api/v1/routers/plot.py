# app/api/v1/routers/accounts.py
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user,get_plot_service
from app.domain.models import User
from app.domain.models.account import AccountType
from app.application.services.plot_service import PlotService
from pydantic import BaseModel
from decimal import Decimal
from fastapi.responses import HTMLResponse
import plotly.express as px
from datetime import datetime as datetimetype
import pandas as pd

class PlotDataResponse(BaseModel):
    name:str
    count:int
    amount:Decimal

class MarketPriceResponse(BaseModel):
    date:datetimetype
    currency_from:str
    currency_to:str
    rate: Decimal

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

@router.get("/htmx-activity", response_class=HTMLResponse)
async def get_htmx_activity(
    journal_id: UUID,
    account_type: AccountType = Query(...),
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
):
    counts = await plot_service.get_account_entry(
        current_user.id,
        journal_id,
        account_type
    )
    
    if not counts:
        return """
        <div class="p-8 text-center bg-white border border-gray-200 rounded-xl shadow-sm">
            <p class="text-gray-500">No data available.</p>
        </div>
        """
        
    names = [c["name"] for c in counts]
    cnts = [c["count"] for c in counts]
    amounts = [abs(float(c["amount"])) for c in counts]
    
    # Palette matching the frontend
    palette = ['#6366f1','#8b5cf6','#ec4899','#f59e0b','#10b981','#3b82f6','#ef4444','#14b8a6']
    
    bar_fig = px.bar(
        x=names, y=cnts, 
        labels={"x": "", "y": "No. of entries"},
        color=names, color_discrete_sequence=palette
    )
    bar_fig.update_layout(
        margin=dict(t=10, r=10, b=80, l=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        font=dict(family='Inter, sans-serif', size=12, color='#374151'),
        xaxis=dict(tickangle=-35, gridcolor='#f3f4f6', linecolor='#e5e7eb'),
        yaxis=dict(gridcolor='#f3f4f6', linecolor='#e5e7eb'),
        bargap=0.35,
        height=300
    )
    
    pie_fig = px.pie(
        names=names, values=amounts, hole=0.42,
        color=names, color_discrete_sequence=palette
    )
    pie_fig.update_layout(
        margin=dict(t=10, r=10, b=10, l=10),
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation='v', x=1.02, y=0.5, font=dict(family='Inter, sans-serif', size=11, color='#374151')),
        font=dict(family='Inter, sans-serif', size=12, color='#374151'),
        height=300
    )
    
    bar_html = bar_fig.to_html(full_html=False, include_plotlyjs=False)
    pie_html = pie_fig.to_html(full_html=False, include_plotlyjs=False)
    
    html = f'''
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
            <h3 class="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">Transaction Count by Account</h3>
            {bar_html}
        </div>
        <div class="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
            <h3 class="text-sm font-semibold text-gray-600 mb-3 uppercase tracking-wide">Amount Distribution by Account</h3>
            {pie_html}
        </div>
    </div>
    '''
    return html

@router.get("/htmx-market-price",
            response_class=HTMLResponse,
            summary="Market Price Chart")
async def get_market_price_chart(
    current_user: User = Depends(get_current_user),
    plot_service: PlotService = Depends(get_plot_service)
):
    prices = await plot_service.get_market_price(skip=0,limit=500)

    if not prices:
        return """
        <div class="p-8 text-center bg-white border border-gray-200 rounded-xl shadow-sm">
            <p class="text-gray-500">No Market Price data available.</p>
        </div>
        """
    data=[]
    for p in prices:
        data.append(
            {
                "Pair":f"{p.currency_from}/{p.currency_to}",
                "Date":p.date,
                "Price": float(p.price)
            }
        )
    df = pd.DataFrame(data)
    df = df.sort_values(by="Date")

    fig = px.line(
        df,
        x="Date",
        y="Price",
        color="Pair",
        markers=True
    )
    fig.update_layout(
        margin = dict(t=10,r=20,b=40,l=40),
        paper_bgcolor = 'rgba(0,0,0,0)',
        plot_bgcolor = 'rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=12, color='#374151'),
        xaxis=dict(gridcolor='#f3f4f6', linecolor='#e5e7eb'),
        yaxis=dict(gridcolor='#f3f4f6', linecolor='#e5e7eb'),
        height=400,
        legend=dict(orientation='h', yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
 
    return fig.to_html(full_html=False, include_plotlyjs=False)
