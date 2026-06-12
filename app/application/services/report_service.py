# app/application/services/report_service.py
from datetime import date
from uuid import UUID

from fastapi import HTTPException

from app.api.v1.schemas.report import BalanceSheetResponse, IncomeStatementResponse, CashFlowStatementResponse
from app.domain.models.account import AccountType
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.report_repo import ReportRepository

from decimal import Decimal

class ReportService:
    """Business logic for generating financial reports."""

    def __init__(
        self, report_repo: ReportRepository, journal_repo: JournalRepository
    ) -> None:
        self.report_repo = report_repo
        self.journal_repo = journal_repo

    async def generate_balance_sheet(
        self, owner_id: UUID, journal_id: UUID, as_of: date
    ) -> BalanceSheetResponse:
        # 1. Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")

        # 2. Get all balances up to the given date
        balances = await self.report_repo.get_account_balances(journal_id, date_to=as_of)

        assets = {}
        liabilities = {}
        equity = {}

        # 3. Categorize and flip signs for credit-normal accounts
        for name, acc_type, balance in balances:
            if balance == 0:
                continue

            if acc_type == AccountType.ASSET:
                assets[name] = balance
            elif acc_type == AccountType.LIABILITY:
                # Liabilities are naturally negative (credits), flip to positive for display
                liabilities[name] = -balance
            elif acc_type == AccountType.EQUITY:
                # Equity is naturally negative (credits), flip to positive for display
                equity[name] = -balance

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

        # 2. Get balances for the specific period
        balances = await self.report_repo.get_account_balances(
            journal_id, date_to=date_to, date_from=date_from
        )

        income = {}
        expenses = {}

        # 3. Categorize and flip signs for credit-normal accounts
        for name, acc_type, balance in balances:
            if balance == 0:
                continue

            if acc_type == AccountType.INCOME:
                # Income is naturally negative (credits), flip to positive for display
                income[name] = -balance
            elif acc_type == AccountType.EXPENSE:
                expenses[name] = balance

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
            self, owner_id:UUID, journal_id: UUID, date_from:date, date_to:date
    )->CashFlowStatementResponse:
        #verify journal
        journal = await self.journal_repo.get_by_id_and_owner(journal_id,owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal Not Found")
        
        #get beginning cash balance
        beginning_balance = await self.report_repo.get_cash_balance(journal_id,date_from)
        #get movements during the period
        movements =  await self.report_repo.get_cash_movements(journal_id,date_from,date_to)

        inflows={}
        outflows={}
        net_cash_flow = Decimal("0.0")

        for name, movement in movements:
            if movement==0:
                continue
            if movement>0:
                inflows[name]=movement
            else:
                outflows[name]=abs(movement)

            net_cash_flow+=movement
        
        ending_balance = beginning_balance+net_cash_flow

        return CashFlowStatementResponse(
            date_from=date_from,
            date_to=date_to,
            beginning_balance=beginning_balance,
            inflows=inflows,
            outflows=outflows,
            net_cash_flow=net_cash_flow,
            ending_balance=ending_balance
        )