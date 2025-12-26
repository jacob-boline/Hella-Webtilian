# hr_payment/providers/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any
from hr_shop.models import Order


class PaymentProvider(ABC):
    @abstractmethod
    def create_checkout_session(self, order: Order) -> Dict[str, Any]:
        """
        Create or re-create a provider checkout session for an order.

        Return:
          {
            "id": "...",            # provider session id
            "status": "...",        # 'open', 'complete', etc (best effort)
            "client_secret": "...", # for embedded checkout
            "url": "...",           # if using redirect checkout
          }
        """
        raise NotImplementedError
