# app/application/services/report_service.py
from datetime import date
from uuid import UUID
from decimal import Decimal
import logging
from collections import defaultdict

from app.api.v1.schemas.report import BalanceSheetResponse, IncomeStatementResponse, CashFlowStatementResponse
from app.domain.models.account import AccountType
from app.domain.money import MissingExchangeRateError, MissingExchangeRatesCollectedError
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.report_repo import ReportRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository

logger = logging.getLogger(__name__)

def _deduplicate(missing: list[dict]) -> list[dict]:
    grouped: dict[tuple, int] = defaultdict(int)
    for r in missing:
        grouped[(r["from"], r["to"], r["date"])] += 1
    return [
        {"from": k[0], "to": k[1], "date": k[2], "transaction_count": v}
        for k, v in grouped.items()
    ]

class ReportService:
    """Business logic for generating financial reports."""

    def __init__(
        self,
        report_repo: ReportRepository,
        journal_repo: JournalRepository,
        market_price_repo: MarketPriceRepository,
    ) -> None:
        self.report_repo = report_repo
        self.journal_repo = journal_repo
        self.market_price_repo = market_price_repo

    async def _convert_amount(
        self, amount: Decimal, from_currency: str, to_currency: str, as_of: date
    ) -> Decimal:
        if from_currency.upper() == to_currency.upper():
            return amount
        
        rate = await self.market_price_repo.get_rate(from_currency, to_currency, as_of)
        
        if rate is None:
            logger.error(
                "Missing exchange rate: %s -> %s on %s for amount %s",
                from_currency, to_currency, as_of, amount
            )
            raise MissingExchangeRateError(from_currency, to_currency, as_of, amount)
            
        return amount * rate

    async def generate_balance_sheet(
        self, owner_id: UUID, journal_id: UUID, as_of: date
    ) -> BalanceSheetResponse:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Journal not found.")

        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_account_balances(journal_id, date_to=as_of)

        assets = {}
        liabilities = {}
        equity = {}
        missing_rates: list[dict] = []

        for name, acc_type, commodity, balance in balances:
            if balance == 0:
                continue

            try:
                converted_balance = await self._convert_amount(balance, commodity, base_currency, as_of)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if acc_type == AccountType.ASSET:
                assets[name] = assets.get(name, Decimal("0.0")) + converted_balance
            elif acc_type == AccountType.LIABILITY:
                liabilities[name] = liabilities.get(name, Decimal("0.0")) - converted_balance
            elif acc_type == AccountType.EQUITY:
                equity[name] = equity.get(name, Decimal("0.0")) - converted_balance

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=_deduplicate(missing_rates))

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
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Journal not found.")

        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_account_balances(
            journal_id, date_to=date_to, date_from=date_from
        )

        income = {}
        expenses = {}
        missing_rates: list[dict] = []

        for name, acc_type, commodity, balance in balances:
            if balance == 0:
                continue

            try:
                converted_balance = await self._convert_amount(balance, commodity, base_currency, date_to)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if acc_type == AccountType.INCOME:
                income[name] = income.get(name, Decimal("0.0")) - converted_balance
            elif acc_type == AccountType.EXPENSE:
                expenses[name] = expenses.get(name, Decimal("0.0")) + converted_balance

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=_deduplicate(missing_rates))

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
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Journal Not Found")

        base_currency = getattr(journal, "base_currency", "USD")
        missing_rates: list[dict] = []

        beginning_balances = await self.report_repo.get_cash_balances(journal_id, date_from)
        beginning_balance = Decimal("0.0")
        for commodity, bal in beginning_balances:
            try:
                converted = await self._convert_amount(bal, commodity, base_currency, date_from)
                beginning_balance += converted
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

        movements = await self.report_repo.get_cash_movements(journal_id, date_from, date_to)

        inflows = {}
        outflows = {}
        net_cash_flow = Decimal("0.0")

        for name, commodity, movement in movements:
            if movement == 0:
                continue

            try:
                converted_movement = await self._convert_amount(movement, commodity, base_currency, date_to)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if converted_movement > 0:
                inflows[name] = inflows.get(name, Decimal("0.0")) + converted_movement
            elif converted_movement < 0:
                outflows[name] = outflows.get(name, Decimal("0.0")) + abs(converted_movement)

            net_cash_flow += converted_movement

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=_deduplicate(missing_rates))

        ending_balance = beginning_balance + net_cash_flow

        return CashFlowStatementResponse(
            date_from=date_from,
            date_to=date_to,
            beginning_balance=beginning_balance,
            inflows=inflows,
            outflows=outflows,
            net_cash_flow=net_cash_flow,
            ending_balance=ending_balance,
        )

    async def get_net_worth(
        self,
        owner_id: UUID,
        journal_id: UUID,
    ):
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Journal Not Found")

        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_net_worth_balances(journal_id)

        assets = Decimal("0.0")
        liabilities = Decimal("0.0")
        missing_rates: list[dict] = []

        today = date.today()
        for acc_type, commodity, bal in balances:
            try:
                converted = await self._convert_amount(bal, commodity, base_currency, today)
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

            if acc_type == AccountType.ASSET:
                assets += converted
            elif acc_type == AccountType.LIABILITY:
                liabilities += converted

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=_deduplicate(missing_rates))

        net_worth = assets + liabilities
        from app.api.v1.schemas.report import NetWorthResponse
        return NetWorthResponse(
            assets=assets,
            liabilities=abs(liabilities),
            net_worth=net_worth,
        )

    async def get_monthly_income(
        self,
        owner_id: UUID,
        journal_id: UUID,
    ):
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Journal Not Found")

        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_monthly_income_balances(journal_id)

        monthly_income = Decimal("0.0")
        missing_rates: list[dict] = []
        today = date.today()
        for commodity, bal in balances:
            try:
                converted = await self._convert_amount(bal, commodity, base_currency, today)
                monthly_income -= converted
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())
                continue

        if missing_rates:
            raise MissingExchangeRatesCollectedError(missing_rates=_deduplicate(missing_rates))

        from app.api.v1.schemas.report import MonthlyIncomeResponse
        return MonthlyIncomeResponse(
            monthly_income=monthly_income,
        )

    async def generate_roi_report(
        self,
        owner_id: UUID,
        journal_id: UUID,
        as_of: date
    ):
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Journal Not Found")

        balances = await self.report_repo.get_roi_balances(journal_id, as_of)

        assets = []
        missing_rates: list[dict] = []

        from app.api.v1.schemas.report import ROIAssetResponse, ROIReportResponse

        for name, commodity, quantity, cost_amount, cost_commodity in balances:
            if quantity == Decimal("0.0") or cost_amount == Decimal("0.0"):
                continue

            try:
                current_value = await self._convert_amount(quantity, commodity, cost_commodity, as_of)
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
                    roi_percent=roi_percent
                )
            )

        if missing_rates:
            missing_rates = _deduplicate(missing_rates)

        return ROIReportResponse(
            date=as_of,
            assets=assets,
            is_complete=len(missing_rates) == 0,
            missing_rates=missing_rates if missing_rates else None
        )

    async def generate_roi_timeline(
        self,
        owner_id: UUID,
        journal_id: UUID,
        commodity: str,
        cost_commodity: str,
    ) -> dict:
        """
        Return month-by-month cumulative cost basis, net return, and exchange rate
        for a specific commodity/cost_commodity investment pair.
        """
        from datetime import date as date_cls
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Journal Not Found")

        timeline = await self.report_repo.get_roi_monthly_timeline(
            journal_id, commodity.upper(), cost_commodity.upper()
        )

        # For each month fetch exchange rate (commodity → cost_commodity)
        for point in timeline:
            month_date = date_cls.fromisoformat(point["month"])
            rate = await self.market_price_repo.get_rate(
                commodity.upper(), cost_commodity.upper(), month_date
            )
            # current_value = quantity * rate
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

