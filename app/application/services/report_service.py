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

    async def generate_roi_report(
        self, owner_id: UUID, journal_id: UUID, account_id: UUID | None = None, as_of: date | None = None
    ) -> list:
        # 1. Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")

        target_date = as_of or date.today()

        # 2. Get transaction entries
        entries = await self.report_repo.get_investment_transactions_entries(
            journal_id, account_id=account_id, date_to=target_date
        )

        if not entries:
            return []

        # 3. Group entries by transaction ID to identify costs in the same transaction
        from collections import defaultdict
        txn_groups = defaultdict(list)
        for e in entries:
            txn_groups[e["txn_id"]].append(e)

        # 4. Group transactions chronologically per account
        from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository
        price_repo = MarketPriceRepository(self.report_repo.db)

        # Key: (account_id, commodity) -> {"units": Decimal, "total_cost": Decimal, "name": str}
        portfolios = defaultdict(lambda: {"units": Decimal("0.0"), "total_cost": Decimal("0.0"), "name": ""})

        seen_txns = set()
        for e in entries:
            txn_id = e["txn_id"]
            if txn_id in seen_txns:
                continue
            seen_txns.add(txn_id)

            txn_entries = txn_groups[txn_id]
            # Sum of USD postings in this transaction (represents cash flow cost)
            usd_sum = sum(x["amount"] for x in txn_entries if x["commodity"] == "USD")

            # Check if there are non-USD postings
            non_usd_postings = [x for x in txn_entries if x["commodity"] != "USD"]

            if not non_usd_postings:
                continue

            for posting in non_usd_postings:
                acc_id = posting["account_id"]
                commodity = posting["commodity"]
                amount = posting["amount"]
                acc_name = posting["account_name"]

                portfolio = portfolios[(acc_id, commodity)]
                portfolio["name"] = acc_name

                # Determine cost of this specific posting
                if usd_sum != Decimal("0.0"):
                    total_non_usd_abs = sum(abs(x["amount"]) for x in non_usd_postings)
                    if total_non_usd_abs > 0:
                        proportion = abs(amount) / total_non_usd_abs
                        posting_cost = -usd_sum * proportion
                    else:
                        posting_cost = Decimal("0.0")
                else:
                    # No USD posting in transaction, use market rate on transaction date
                    rate = await price_repo.get_rate(commodity, "USD", posting["txn_date"])
                    if rate is not None:
                        posting_cost = amount * rate
                    else:
                        posting_cost = Decimal("0.0")

                if amount > 0:
                    portfolio["units"] += amount
                    portfolio["total_cost"] += posting_cost
                elif amount < 0:
                    if portfolio["units"] > 0:
                        avg_cost = portfolio["total_cost"] / portfolio["units"]
                        sold_units = min(abs(amount), portfolio["units"])
                        portfolio["units"] -= sold_units
                        portfolio["total_cost"] -= sold_units * avg_cost

        # 5. Build responses for each portfolio holding
        from app.api.v1.schemas.investment import ROIResponse
        results = []
        for (acc_id, commodity), portfolio in portfolios.items():
            units = portfolio["units"]
            cost_basis = portfolio["total_cost"]

            if units <= 0:
                continue

            # Fetch current price on target_date
            current_price = await price_repo.get_rate(commodity, "USD", target_date)
            if current_price is None:
                current_price = Decimal("1.0")

            current_value = units * current_price
            net_gain = current_value - cost_basis
            
            roi = Decimal("0.0")
            if cost_basis > 0:
                roi = net_gain / cost_basis

            avg_cost = cost_basis / units if units > 0 else Decimal("0.0")

            results.append(
                ROIResponse(
                    account_id=acc_id,
                    account_name=portfolio["name"],
                    commodity=commodity,
                    units=units,
                    average_cost_basis=avg_cost,
                    current_price=current_price,
                    cost_basis=cost_basis,
                    current_value=current_value,
                    net_gain=net_gain,
                    roi=roi,
                )
            )

        return results