# hr_payments/providers/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any

from hr_shop.models import Order


class PaymentProvider(ABC):
    @abstractmethod
    def create_checkout_session(self, order: Order) -> Dict[str, Any]:
        """
        Prepare a payment for this order.

        Must:
          - Attach a provider-specific id to the order (e.g., Stripe session id)
          - Optionally update order.status
          - Return at least:
              {
                "id": "...",      # provider session id
                "status": "...",  # 'open', 'complete', 'succeeded', etc.
                "url": "...",     # where to send the user (can be internal)
              }
        """
        raise NotImplementedError
