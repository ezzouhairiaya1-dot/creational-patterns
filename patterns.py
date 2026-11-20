"""Examples of a payment factory, fluent employee builder, and config singleton."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any


# ---------------------------------------------------------------------------
# Factory: payment processors
# ---------------------------------------------------------------------------


class PaymentProcessor(ABC):
    """Common contract for supported payment methods."""

    method: str

    @abstractmethod
    def validate(self, details: dict) -> bool:
        """Return whether the supplied payment details are valid."""

    @abstractmethod
    def process(self, amount: float, details: dict) -> dict:
        """Validate and process the payment, returning a result dictionary."""

    @staticmethod
    def _failure(method: str, error: str) -> dict:
        return {"success": False, "method": method, "error": error}

    @staticmethod
    def _success(method: str, amount: float, fee: float) -> dict:
        return {"success": True, "method": method, "amount": amount + fee, "fee": fee}


class CreditCardProcessor(PaymentProcessor):
    method = "credit_card"

    def validate(self, details: dict) -> bool:
        card_number = details.get("card_number")
        cvv = details.get("cvv")
        return (
            isinstance(card_number, str)
            and len(card_number) == 16
            and isinstance(cvv, str)
            and len(cvv) == 3
        )

    def process(self, amount: float, details: dict) -> dict:
        card_number = details.get("card_number")
        cvv = details.get("cvv")
        if not isinstance(card_number, str) or len(card_number) != 16:
            return self._failure(self.method, "Invalid card number")
        if not isinstance(cvv, str) or len(cvv) != 3:
            return self._failure(self.method, "Invalid CVV")
        fee = amount * 0.029
        return self._success(self.method, amount, fee)


class BankTransferProcessor(PaymentProcessor):
    method = "bank_transfer"

    def validate(self, details: dict) -> bool:
        iban = details.get("iban")
        return isinstance(iban, str) and len(iban) >= 15

    def process(self, amount: float, details: dict) -> dict:
        if not self.validate(details):
            return self._failure(self.method, "Invalid IBAN")
        fee = 1.50
        return self._success(self.method, amount, fee)


class PayPalProcessor(PaymentProcessor):
    method = "paypal"

    def validate(self, details: dict) -> bool:
        email = details.get("email")
        return isinstance(email, str) and "@" in email

    def process(self, amount: float, details: dict) -> dict:
        if not self.validate(details):
            return self._failure(self.method, "Invalid PayPal email")
        fee = amount * 0.034 + 0.30
        return self._success(self.method, amount, fee)


class PaymentFactory:
    """Create the processor registered for a payment type."""

    _processors: dict[str, type[PaymentProcessor]] = {
        "credit_card": CreditCardProcessor,
        "bank_transfer": BankTransferProcessor,
        "paypal": PayPalProcessor,
    }

    def get_processor(self, payment_type: str) -> PaymentProcessor:
        try:
            processor_class = self._processors[payment_type]
        except KeyError:
            raise ValueError(f"Unknown payment type: {payment_type}") from None
        return processor_class()


# ---------------------------------------------------------------------------
# Builder: employee records
# ---------------------------------------------------------------------------


@dataclass
class Employee:
    """Final employee record produced by EmployeeBuilder."""

    first_name: str
    last_name: str
    email: str
    department: str
    position: str
    salary: float
    start_date: str | None = None
    manager_id: int | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    has_parking: bool = False
    has_laptop: bool = False
    has_vpn_access: bool = False
    has_admin_rights: bool = False
    office_location: str | None = None
    contract_type: str = "permanent"


class EmployeeBuilder:
    """Fluent builder that validates required employee data at build time."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {
            "first_name": None,
            "last_name": None,
            "email": None,
            "department": None,
            "position": None,
            "salary": None,
        }

    def with_name(self, first_name: str, last_name: str) -> EmployeeBuilder:
        self._values.update(first_name=first_name, last_name=last_name)
        return self

    def with_email(self, email: str) -> EmployeeBuilder:
        self._values["email"] = email
        return self

    def with_job(self, department: str, position: str, salary: float) -> EmployeeBuilder:
        self._values.update(department=department, position=position, salary=salary)
        return self

    def with_start_date(self, start_date: str) -> EmployeeBuilder:
        self._values["start_date"] = start_date
        return self

    def with_manager(self, manager_id: int | None) -> EmployeeBuilder:
        self._values["manager_id"] = manager_id
        return self

    def with_contact(
        self,
        phone: str | None = None,
        address: str | None = None,
        emergency_contact: str | None = None,
    ) -> EmployeeBuilder:
        self._values.update(
            phone=phone,
            address=address,
            emergency_contact=emergency_contact,
        )
        return self

    def with_equipment(self, laptop: bool = False, parking: bool = False) -> EmployeeBuilder:
        self._values.update(has_laptop=laptop, has_parking=parking)
        return self

    def with_access(self, vpn: bool = False, admin: bool = False) -> EmployeeBuilder:
        self._values.update(has_vpn_access=vpn, has_admin_rights=admin)
        return self

    def with_office(self, office_location: str | None) -> EmployeeBuilder:
        self._values["office_location"] = office_location
        return self

    def with_contract_type(self, contract_type: str) -> EmployeeBuilder:
        self._values["contract_type"] = contract_type
        return self

    def build(self) -> Employee:
        required = ("first_name", "last_name", "email", "department", "position", "salary")
        missing = [field for field in required if self._values.get(field) is None]
        if missing:
            raise ValueError(f"Missing required employee fields: {', '.join(missing)}")

        first_name = self._values["first_name"]
        last_name = self._values["last_name"]
        email = self._values["email"]
        salary = self._values["salary"]
        if not first_name or not last_name:
            raise ValueError("Name is required")
        if not email or "@" not in email:
            raise ValueError("Valid email is required")
        if salary < 0:
            raise ValueError("Salary cannot be negative")

        return Employee(**self._values)


class DeveloperBuilder(EmployeeBuilder):
    """Preset for a senior engineering developer with standard equipment/access."""

    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        salary: float = 75000.0,
    ) -> None:
        super().__init__()
        self.with_name(first_name, last_name)
        self.with_email(email)
        self.with_job("Engineering", "Senior Developer", salary)
        self.with_equipment(laptop=True)
        self.with_access(vpn=True, admin=True)


# ---------------------------------------------------------------------------
# Singleton: shared configuration
# ---------------------------------------------------------------------------


class ConfigManager:
    """Load JSON configuration once and share it across the process."""

    _instance: ConfigManager | None = None
    _lock = RLock()

    def __new__(cls, config_path: str | Path = "config.json") -> ConfigManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str | Path = "config.json") -> None:
        with type(self)._lock:
            if getattr(self, "_initialized", False):
                return
            self._config_path = Path(config_path)
            with self._config_path.open("r", encoding="utf-8") as config_file:
                config = json.load(config_file)
            if not isinstance(config, dict):
                raise ValueError("The configuration file must contain a JSON object")
            self._config: dict[str, Any] = config
            self._initialized = True

    @classmethod
    def get_instance(cls, config_path: str | Path = "config.json") -> ConfigManager:
        """Return the singleton, loading the given path only on first access."""
        return cls(config_path)

    def get(self, key: str, default: Any = None) -> Any:
        """Read a dotted path such as ``database.host`` from the shared config."""
        if key == "":
            return self._config
        value: Any = self._config
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def set(self, key: str, value: Any) -> None:
        """Update a dotted path in memory so all callers see the new value."""
        parts = key.split(".")
        if not key or any(not part for part in parts):
            raise ValueError("Configuration key must be a non-empty dotted path")
        target = self._config
        for part in parts[:-1]:
            current = target.get(part)
            if current is None:
                current = {}
                target[part] = current
            if not isinstance(current, dict):
                raise ValueError(f"Cannot set nested key below non-object value: {part}")
            target = current
        target[parts[-1]] = value
