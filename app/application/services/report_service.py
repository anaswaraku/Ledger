# app/application/services/report_service.py
from datetime import date
from uuid import UUID
from decimal import Decimal
import logging

from fastapi import HTTPException

from app.api.v1.schemas.report import BalanceSheetResponse, IncomeStatementResponse, CashFlowStatementResponse
from app.domain.models.account import AccountType
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.report_repo import ReportRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository

logger = logging.getLogger(__name__)


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
            logger.warning(
                f"Exchange rate from {from_currency} to {to_currency} not found on/before {as_of}. Using 1.0 rate fallback."
            )
            return amount
        return amount * rate

    async def generate_balance_sheet(
        self, owner_id: UUID, journal_id: UUID, as_of: date
    ) -> BalanceSheetResponse:
        # 1. Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")

        base_currency = getattr(journal, "base_currency", "USD")

        # 2. Get all balances up to the given date
        balances = await self.report_repo.get_account_balances(journal_id, date_to=as_of)

        assets = {}
        liabilities = {}
        equity = {}

        # 3. Categorize, convert to base_currency, and flip signs for credit-normal accounts
        for name, acc_type, commodity, balance in balances:
            if balance == 0:
                continue

            converted_balance = await self._convert_amount(balance, commodity, base_currency, as_of)

            if acc_type == AccountType.ASSET:
                assets[name] = assets.get(name, Decimal("0.0")) + converted_balance
            elif acc_type == AccountType.LIABILITY:
                # Liabilities are naturally negative (credits), flip to positive for display
                liabilities[name] = liabilities.get(name, Decimal("0.0")) - converted_balance
            elif acc_type == AccountType.EQUITY:
                # Equity is naturally negative (credits), flip to positive for display
                equity[name] = equity.get(name, Decimal("0.0")) - converted_balance

        # 4. Calculate Net Assets (Assets - Liabilities)
        # We use the flipped positive values from our dicts for the calculation
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
        # 1. Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")

        base_currency = getattr(journal, "base_currency", "USD")

        # 2. Get balances for the specific period
        balances = await self.report_repo.get_account_balances(
            journal_id, date_to=date_to, date_from=date_from
        )

        income = {}
        expenses = {}

        # 3. Categorize, convert to base_currency, and flip signs for credit-normal accounts
        for name, acc_type, commodity, balance in balances:
            if balance == 0:
                continue

            converted_balance = await self._convert_amount(balance, commodity, base_currency, date_to)

            if acc_type == AccountType.INCOME:
                # Income is naturally negative (credits), flip to positive for display
                income[name] = income.get(name, Decimal("0.0")) - converted_balance
            elif acc_type == AccountType.EXPENSE:
                expenses[name] = expenses.get(name, Decimal("0.0")) + converted_balance

        # 4. Calculate Net Income (Income - Expenses)
        # We use the flipped positive values
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
        # verify journal
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal Not Found")

        base_currency = getattr(journal, "base_currency", "USD")

        # get beginning cash balance
        beginning_balances = await self.report_repo.get_cash_balances(journal_id, date_from)
        beginning_balance = Decimal("0.0")
        for commodity, bal in beginning_balances:
            converted = await self._convert_amount(bal, commodity, base_currency, date_from)
            beginning_balance += converted

        # get movements during the period
        movements = await self.report_repo.get_cash_movements(journal_id, date_from, date_to)

        inflows = {}
        outflows = {}
        net_cash_flow = Decimal("0.0")

        for name, commodity, movement in movements:
            if movement == 0:
                continue

            converted_movement = await self._convert_amount(movement, commodity, base_currency, date_to)

            if converted_movement > 0:
                inflows[name] = inflows.get(name, Decimal("0.0")) + converted_movement
            elif converted_movement < 0:
                outflows[name] = outflows.get(name, Decimal("0.0")) + abs(converted_movement)

            net_cash_flow += converted_movement

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
        # verify journal
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal Not Found")

        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_net_worth_balances(journal_id)

        assets = Decimal("0.0")
        liabilities = Decimal("0.0")

        today = date.today()
        for acc_type, commodity, bal in balances:
            converted = await self._convert_amount(bal, commodity, base_currency, today)
            if acc_type == AccountType.ASSET:
                assets += converted
            elif acc_type == AccountType.LIABILITY:
                liabilities += converted

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
        # verify journal
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal Not Found")

        base_currency = getattr(journal, "base_currency", "USD")
        balances = await self.report_repo.get_monthly_income_balances(journal_id)

        monthly_income = Decimal("0.0")
        today = date.today()
        for commodity, bal in balances:
            # Income is naturally negative in double entry (credit), flip to positive for display
            converted = await self._convert_amount(bal, commodity, base_currency, today)
            monthly_income -= converted

        from app.api.v1.schemas.report import MonthlyIncomeResponse
        return MonthlyIncomeResponse(
            monthly_income=monthly_income,
        )
