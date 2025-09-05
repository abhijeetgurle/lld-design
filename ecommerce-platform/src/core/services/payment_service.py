from core.entities.payment import Payment, Refund
from core.value_objects.money import Money


class PaymentService:
    def process_payment(self, payment: Payment) -> Payment:
        """
        In interview: "This would integrate with Stripe, Razorpay, etc.
        Handle multiple gateways, retries, and failure scenarios"
        """
        pass

    def process_refund(self, payment_id: str, amount: Money) -> Refund:
        """Key for order cancellation workflows"""
        pass