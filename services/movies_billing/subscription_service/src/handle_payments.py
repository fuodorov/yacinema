import time

from core.config import settings
from services.payment import PaymentService
from services.payment_processor.stripe_processor import PaymentProcessorStripe


def handle_payments():
    stripe_processor = PaymentProcessorStripe(settings.stripe_settings.stripe_secret_key)
    payment_service = PaymentService(stripe_processor)

    while True:
        payment_service.process()
        time.sleep(settings.poll_timeout)


if __name__ == '__main__':
    handle_payments()
