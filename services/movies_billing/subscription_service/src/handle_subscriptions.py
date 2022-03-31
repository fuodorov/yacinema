import time

from core.config import settings
from services.subscriptions import SubscriptionService


def handle_subscriptions():
    subscription_service = SubscriptionService()

    while True:
        subscription_service.process()
        time.sleep(settings.poll_timeout)


if __name__ == '__main__':
    handle_subscriptions()
