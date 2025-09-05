import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(Enum):
    CREDIT_CARD = "CREDIT_CARD"
    UPI = "UPI"
    WALLET = "WALLET"


@dataclass
class Payment:
    """
    Payment entity - core business domain object

    Should be in domain/entities because:
    1. Has identity (payment_id)
    2. Contains business rules
    3. Core concept in e-commerce domain
    4. Independent of external payment providers
    """
    payment_id: str
    order_id: str
    customer_id: str
    amount: 'Money'  # Reference to our Money value object
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    transaction_id: Optional[str] = None  # External gateway reference
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @classmethod
    def create_for_order(cls, order_id: str, customer_id: str,
                         amount: 'Money', method: PaymentMethod) -> 'Payment':
        """Factory method for creating payments"""
        return cls(
            payment_id=str(uuid.uuid4()),
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            method=method
        )

    def mark_successful(self, transaction_id: str) -> None:
        """Business method - payment processing succeeded"""
        if self.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot mark {self.status} payment as successful")

        self.status = PaymentStatus.SUCCESS
        self.processed_at = datetime.now()
        self.transaction_id = transaction_id

    def mark_failed(self, error_message: str) -> None:
        """Business method - payment processing failed"""
        if self.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot mark {self.status} payment as failed")

        self.status = PaymentStatus.FAILED
        self.processed_at = datetime.now()
        self.error_message = error_message

    def can_be_refunded(self) -> bool:
        """Business rule - only successful payments can be refunded"""
        return self.status == PaymentStatus.SUCCESS

    def is_successful(self) -> bool:
        """Business query method"""
        return self.status == PaymentStatus.SUCCESS

    def is_pending(self) -> bool:
        """Business query method"""
        return self.status == PaymentStatus.PENDING


@dataclass
class Refund:
    """
    Refund entity - also belongs in domain/entities
    """
    refund_id: str
    original_payment_id: str
    amount: 'Money'
    reason: str
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = None
    processed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @classmethod
    def create_for_payment(cls, payment_id: str, amount: 'Money', reason: str) -> 'Refund':
        """Factory method for creating refunds"""
        return cls(
            refund_id=str(uuid.uuid4()),
            original_payment_id=payment_id,
            amount=amount,
            reason=reason
        )

    def mark_processed(self) -> None:
        """Business method - refund completed"""
        if self.status != PaymentStatus.PENDING:
            raise ValueError("Can only process pending refunds")

        self.status = PaymentStatus.SUCCESS
        self.processed_at = datetime.now()