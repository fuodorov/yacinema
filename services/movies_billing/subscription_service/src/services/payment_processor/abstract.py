from abc import ABC


class PaymentProcessorAbstract(ABC):
    def make_payment(self, customer_id: str, amount: int):
        pass
