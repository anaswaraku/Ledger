# app/application/services/report_service.py
from datetime import date
from uuid import UUID
from decimal import Decimal
import logging

from fastapi import HTTPException

from app.api.v1.schemas.report import BalanceSheetResponse, IncomeStatementResponse, CashFlowStatementResponse
from app.application._utils import convert_amount, deduplicate_rates, get_journal_or_404
from app.domain.models.account import AccountType
from app.domain.money import MissingExchangeRateError, MissingExchangeRatesCollectedError
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.report_repo import ReportRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository

logger = logging.getLogger(__name__)


class ReportService:
    """Logic for generating financial reports."""

    def __init__(
        self,
        report_repo: ReportRepository,
        journal_repo: JournalRepository,
        market_price_repo: MarketPriceRepository,
    ) -> None:
        self.report_repo = report_repo
        self.journal_repo = journal_repo
        self.market_price_repo = market_price_repo

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _convert(self, amount: Decimal, from_currency: str, to_currency: str, as_of: date) -> Decimal:
        """Thin wrapper so callers don't have to pass market_price_repo each time."""
        return await convert_amount(self.market_price_repo, amount, from_currency, to_currency, as_of)

    # ── Reports ───────────────────────────────────────────────────────────────

    async def generate_balance_sheet(
        self, owner_id: UUID, journal_id: UUID, as_of: date
    ) -> BalanceSheetResponse:
        journal = await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_account_balances(journal_id, date_to=as_of)

        assets: dict[str, Decimal] = {}
        liabilities: dict[str, Decimal] = {}
        equity: dict[str, Decimal] = {}
        missing_rates: list[dict] = []

        for name, acc_type, commodity, balance in balances:
            if balance == 0:
                continue
            try:
                converted = await self._convert(balance, commodity, base_currency, as_of)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if acc_type == AccountType.ASSET:
                assets[name] = assets.get(name, Decimal("0.0")) + converted
            elif acc_type == AccountType.LIABILITY:
                liabilities[name] = liabilities.get(name, Decimal("0.0")) - converted
            elif acc_type == AccountType.EQUITY:
                equity[name] = equity.get(name, Decimal("0.0")) - converted

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=deduplicate_rates(missing_rates))

        net_assets = sum(assets.values()) - sum(liabilities.values())

        return BalanceSheetResponse(
            date=as_of,
            assets=assets,
            liabilities=liabilities,
            equity=equity,
            net=net_assets,
        )

    async def generate_income_statement(
        self, owner_id: UUID, journal_id: UUID, date_from: date, date_to: date
    ) -> IncomeStatementResponse:
        journal = await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_account_balances(
            journal_id, date_to=date_to, date_from=date_from
        )

        income: dict[str, Decimal] = {}
        expenses: dict[str, Decimal] = {}
        missing_rates: list[dict] = []

        for name, acc_type, commodity, balance in balances:
            if balance == 0:
                continue
            try:
                converted = await self._convert(balance, commodity, base_currency, date_to)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if acc_type == AccountType.INCOME:
                income[name] = income.get(name, Decimal("0.0")) - converted
            elif acc_type == AccountType.EXPENSE:
                expenses[name] = expenses.get(name, Decimal("0.0")) + converted

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=deduplicate_rates(missing_rates))

        total_income = sum(income.values())
        total_expenses = sum(expenses.values())
        net_income = total_income - total_expenses

        return IncomeStatementResponse(
            date_from=date_from,
            date_to=date_to,
            income=income,
            expenses=expenses,
            total_income=total_income,
            total_expenses=total_expenses,
            net_income=net_income,
        )

    async def generate_cash_flow(
        self, owner_id: UUID, journal_id: UUID, date_from: date, date_to: date
    ) -> CashFlowStatementResponse:
        journal = await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        base_currency = getattr(journal, "base_currency", "USD")
        missing_rates: list[dict] = []

        beginning_balance = Decimal("0.0")
        for commodity, bal in await self.report_repo.get_cash_balances(journal_id, date_from):
            try:
                beginning_balance += await self._convert(bal, commodity, base_currency, date_from)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())

        inflows: dict[str, Decimal] = {}
        outflows: dict[str, Decimal] = {}
        net_cash_flow = Decimal("0.0")

        for name, commodity, movement in await self.report_repo.get_cash_movements(journal_id, date_from, date_to):
            if movement == 0:
                continue
            try:
                converted = await self._convert(movement, commodity, base_currency, date_to)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if converted > 0:
                inflows[name] = inflows.get(name, Decimal("0.0")) + converted
            elif converted < 0:
                outflows[name] = outflows.get(name, Decimal("0.0")) + abs(converted)
            net_cash_flow += converted

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=deduplicate_rates(missing_rates))

        return CashFlowStatementResponse(
            date_from=date_from,
            date_to=date_to,
            beginning_balance=beginning_balance,
            inflows=inflows,
            outflows=outflows,
            net_cash_flow=net_cash_flow,
            ending_balance=beginning_balance + net_cash_flow,
        )

    async def get_net_worth(self, owner_id: UUID, journal_id: UUID):
        journal = await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        base_currency = getattr(journal, "base_currency", "USD")
        today = date.today()
        missing_rates: list[dict] = []

        assets = Decimal("0.0")
        liabilities = Decimal("0.0")

        for acc_type, commodity, bal in await self.report_repo.get_net_worth_balances(journal_id):
            try:
                converted = await self._convert(bal, commodity, base_currency, today)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if acc_type == AccountType.ASSET:
                assets += converted
            elif acc_type == AccountType.LIABILITY:
                liabilities += converted

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=deduplicate_rates(missing_rates))

        from app.api.v1.schemas.report import NetWorthResponse
        return NetWorthResponse(
            assets=assets,
            liabilities=abs(liabilities),
            net_worth=assets + liabilities,
        )

    async def get_monthly_income(self, owner_id: UUID, journal_id: UUID):
        journal = await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        base_currency = getattr(journal, "base_currency", "USD")
        today = date.today()
        missing_rates: list[dict] = []
        monthly_income = Decimal("0.0")

        for commodity, bal in await self.report_repo.get_monthly_income_balances(journal_id):
            try:
                monthly_income -= await self._convert(bal, commodity, base_currency, today)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=deduplicate_rates(missing_rates))

        from app.api.v1.schemas.report import MonthlyIncomeResponse
        return MonthlyIncomeResponse(monthly_income=monthly_income)

    async def generate_roi_report(self, owner_id: UUID, journal_id: UUID, as_of: date):
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        balances = await self.report_repo.get_roi_balances(journal_id, as_of)

        from app.api.v1.schemas.report import ROIAssetResponse, ROIReportResponse

        assets = []
        missing_rates: list[dict] = []

        for name, commodity, quantity, cost_amount, cost_commodity in balances:
            if quantity == Decimal("0.0") or cost_amount == Decimal("0.0"):
                continue
            try:
                current_value = await self._convert(quantity, commodity, cost_commodity, as_of)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            gain = current_value - cost_amount
            roi_percent = (gain / abs(cost_amount)) * 100
            assets.append(
                ROIAssetResponse(
                    account_name=name,
                    commodity=commodity,
                    cost_commodity=cost_commodity,
                    quantity=quantity,
                    cost_basis=cost_amount,
                    current_value=current_value,
                    gain=gain,
                    roi_percent=roi_percent,
                )
            )

        if missing_rates:
            missing_rates = deduplicate_rates(missing_rates)

        return ROIReportResponse(
            date=as_of,
            assets=assets,
            is_complete=len(missing_rates) == 0,
            missing_rates=missing_rates if missing_rates else None,
        )

    async def generate_roi_timeline(
        self, owner_id: UUID, journal_id: UUID, commodity: str, cost_commodity: str
    ) -> dict:
        """Month-by-month cumulative cost basis, net return, and exchange rate."""
        from datetime import date as date_cls
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)

        timeline = await self.report_repo.get_roi_monthly_timeline(
            journal_id, commodity.upper(), cost_commodity.upper()
        )

        for point in timeline:
            month_date = date_cls.fromisoformat(point["month"])
            rate = await self.market_price_repo.get_rate(
                commodity.upper(), cost_commodity.upper(), month_date
            )
            if rate is not None:
                point["exchange_rate"] = float(rate)
                point["current_value"] = round(point["cum_qty"] * float(rate), 4)
                point["net_return"] = round(point["current_value"] - point["cum_cost"], 4)
            else:
                point["exchange_rate"] = None
                point["current_value"] = None
                point["net_return"] = None

        return {
            "commodity": commodity.upper(),
            "cost_commodity": cost_commodity.upper(),
            "timeline": timeline,
        }
