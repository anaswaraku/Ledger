from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.domain.models.account import AccountType

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from enum import Enum


#  Base Schema (shared fields) 
class AccountBase(BaseModel):
    name: str
    account_type: AccountType


#  Create Schema (input) 
class AccountCreate(AccountBase):
    journal_id: UUID


#  Update Schema (partial input) 
class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: AccountType | None = None


#  Response Schema (output) 
class AccountResponse(AccountBase):
    id: UUID
    journal_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
