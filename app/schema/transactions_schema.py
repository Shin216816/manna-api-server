from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TransactionData(BaseModel):
    id: int
    amount: float
    roundup_amount: float
    merchant_name: str
    merchant_category: str
    status: str
    transaction_date: datetime
    description: str

class TransactionResponseData(BaseModel):
    transactions: List[TransactionData]
    pending_roundup_total: float
    total_count: int

class PaginationData(BaseModel):
    page: int
    limit: int
    total: int
    pages: int

class TransactionResponse(BaseModel):
    success: bool
    data: TransactionResponseData
    pagination: PaginationData
