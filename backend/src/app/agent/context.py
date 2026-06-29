from dataclasses import dataclass
from enum import Enum

from app.agent.errors import AgentError
from app.domain.models import Invoice, Policy, PurchaseOrder

class LookupState(str, Enum):
    NOT_STARTED = "not_started"
    FOUND = "found"
    NOT_FOUND = "not_found"
    FAILED = "failed"

@dataclass
class AgentContext:
    invoice_id: str | None = None
    invoice: Invoice | None = None
    invoice_lookup_state: LookupState = LookupState.NOT_STARTED

    purchase_order: PurchaseOrder | None = None
    po_lookup_state: LookupState = LookupState.NOT_STARTED

    policy: Policy | None = None
    policy_lookup_state: LookupState = LookupState.NOT_STARTED

    error: AgentError | None = None

    @property
    def invoice_lookup_attempted(self) -> bool:
        return self.invoice_lookup_state != LookupState.NOT_STARTED

    @property
    def po_lookup_attempted(self) -> bool:
        return self.po_lookup_state != LookupState.NOT_STARTED

    @property
    def policy_lookup_attempted(self) -> bool:
        return self.policy_lookup_state != LookupState.NOT_STARTED
