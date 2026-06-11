# app/application/use_cases/create_transaction.py
"""
CreateTransaction use case.

Orchestrates the flow:
  Router → CreateTransactionUseCase → TransactionService → TransactionRepository

Keeping the use case as a thin orchestrator preserves the Clean Architecture
separation: routers are ignorant of service internals, and services are
ignorant of HTTP concerns.
"""
import uuid

from app.api.v1.schemas.transaction import TransactionCreate
from app.application.services.transaction_service import TransactionService
from app.domain.models.transaction import Transaction


class CreateTransactionUseCase:
    """
    Encapsulates the 'create a double-entry transaction' workflow.

    Usage (inside a router):
        use_case = CreateTransactionUseCase(transaction_service)
        transaction = await use_case.execute(data, current_user.id)
    """

    def __init__(self, transaction_service: TransactionService) -> None:
        self.transaction_service = transaction_service

    async def execute(
        self, data: TransactionCreate, owner_id: uuid.UUID
    ) -> Transaction:
        return await self.transaction_service.create(data=data, owner_id=owner_id)
