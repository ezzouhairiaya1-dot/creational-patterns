# Creational pattern refactors

The diagrams below define the class relationships before the implementation in [`patterns.py`](patterns.py).

## Payment factory

```mermaid
classDiagram
    class PaymentProcessor {
        <<abstract>>
        +validate(details: dict) bool
        +process(amount: float, details: dict) dict
    }
    class CreditCardProcessor
    class BankTransferProcessor
    class PayPalProcessor
    class PaymentFactory {
        -processors: dict
        +get_processor(payment_type: str) PaymentProcessor
    }
    PaymentProcessor <|-- CreditCardProcessor
    PaymentProcessor <|-- BankTransferProcessor
    PaymentProcessor <|-- PayPalProcessor
    PaymentFactory ..> PaymentProcessor : creates
```

The dictionary-backed `PaymentFactory` is the registry-style factory requested in the exercise. In GoF terminology, it is closer to a Simple Factory than the subclass-overridden Factory Method pattern.

## Employee builder

```mermaid
classDiagram
    class Employee {
        +first_name: str
        +last_name: str
        +email: str
        +department: str
        +position: str
        +salary: float
        +start_date: str | None
        +manager_id: int | None
        +phone: str | None
        +address: str | None
        +emergency_contact: str | None
        +has_parking: bool
        +has_laptop: bool
        +has_vpn_access: bool
        +has_admin_rights: bool
        +office_location: str | None
        +contract_type: str
    }
    class EmployeeBuilder {
        +with_name(first_name, last_name) EmployeeBuilder
        +with_email(email) EmployeeBuilder
        +with_job(department, position, salary) EmployeeBuilder
        +with_equipment(laptop, parking) EmployeeBuilder
        +with_access(vpn, admin) EmployeeBuilder
        +build() Employee
    }
    class DeveloperBuilder
    EmployeeBuilder ..> Employee : builds
    DeveloperBuilder --|> EmployeeBuilder : presets
```

## Configuration singleton

```mermaid
classDiagram
    class ConfigManager {
        -_instance: ConfigManager
        -_config: dict
        +get_instance(config_path) ConfigManager
        +get(key: str, default) Any
        +set(key: str, value: Any) None
    }
    ConfigManager --> ConfigManager : returns shared instance
```

## Usage

```python
from design_patterns.patterns import (
    ConfigManager,
    DeveloperBuilder,
    EmployeeBuilder,
    PaymentFactory,
)

processor = PaymentFactory().get_processor("credit_card")
payment = processor.process(
    100.0,
    {"card_number": "1234567890123456", "cvv": "123"},
)

employee = (
    EmployeeBuilder()
    .with_name("John", "Doe")
    .with_email("john.doe@company.com")
    .with_job("Engineering", "Senior Developer", 75000)
    .with_equipment(laptop=True, parking=False)
    .with_access(vpn=True, admin=True)
    .build()
)
developer = DeveloperBuilder("John", "Doe", "john.doe@company.com").build()

config = ConfigManager.get_instance("config.json")
db_host = config.get("database.host")
```

`ConfigManager` loads the file on its first construction. Later calls return the same object, so updates made with `set` (or through a mutable value returned by `get`) are visible to every caller in the process. The first config path used for the singleton is the one that remains active.
