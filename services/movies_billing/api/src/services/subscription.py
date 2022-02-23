import datetime
import logging
from typing import Optional

from async_stripe import stripe
from fastapi import Depends
from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from core.config import settings
from db.session import get_db
from models.customer import Customer
from models.subscription import Status as SubscriptionStatus
from models.subscription import Subscription
from services.exceptions import AlreadyHasSubscriptions


class SubscriptionService(object):
    settings = settings

    def __init__(self, db: Session):
        self.db = db

    async def _get_stripe_customer_id(self, user_id: str) -> Optional[str]:
        user = await self.db.execute(
            select(
                Customer.stripe_customer_id,
            ).where(
                Customer.user_id == user_id,
            ),
        )
        user = user.first()
        if not user:
            return None
        return user.stripe_customer_id

    async def _create_customer(self, user_id: str):
        customer = await stripe.Customer.create(
            description="customer",
        )
        await self.db.execute(
            insert(
                Customer
            ).values(
                user_id=user_id,
                stripe_customer_id=customer.id
            ),
        )
        return customer.id

    async def _is_subscription_exists(self, user_id):
        user = await self.db.execute(
            select(
                Subscription.id,
            ).outerjoin(
                Customer, Subscription.customer_id == Customer.id
            ).where(
                Customer.user_id == user_id,
            ),
        )
        user = user.first()
        return bool(user)

    async def prepare_setup_payment(self, user_id: str) -> str:
        if self._is_subscription_exists(user_id):
            raise AlreadyHasSubscriptions

        stripe_customer_id = await self._get_stripe_customer_id(user_id)

        if not stripe_customer_id:
            logging.info(f'customer {user_id} not exists. Create in stripe')
            stripe_customer_id = await self._create_customer(user_id)
            logging.info(f'customer {stripe_customer_id} created in stripe')

        logging.info(f'create session for user {stripe_customer_id}')
        session = await stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='setup',
            customer=stripe_customer_id,
            # todo move to config
            success_url='http://localhost:8000/v1/subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:8000/v1/subscription/cancel',
        )

        print(session.url)
        return session.url

    async def create_subscription(self, session_id: str, tariff_id: int):
        session = await stripe.checkout.Session.retrieve(session_id, expand=['customer'])
        stripe_customer_id = session.customer.id

        customer = await self.db.execute(
            select(
                Customer.id
            ).where(
                Customer.stripe_customer_id == stripe_customer_id
            ).limit(1))
        customer = customer.first()

        await self.db.execute(
            insert(
                Subscription
            ).values(
                customer_id=customer.id,
                status=SubscriptionStatus.NEW,
                tariff_id=tariff_id,
                date_begin=datetime.datetime.now(),
                date_end=datetime.datetime.now(),
            ),
        )


def get_subscription_service(db: Session = Depends(get_db)):
    return SubscriptionService(db)
