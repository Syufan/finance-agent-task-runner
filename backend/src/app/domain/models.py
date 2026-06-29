from dataclasses import dataclass


@dataclass
class Invoice:
    invoiceId: str
    vendor: str
    amount: int
    currency: str
    status: str
    poId: str | None
    blockReason: str | None


@dataclass
class PurchaseOrder:
    poId: str
    amount: int
    currency: str
    owner: str
    status: str


@dataclass
class Policy:
    blockReason: str
    policy: str
    recommendedAction: str