from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class RawCustomerRecord:
    customer_name: Optional[str] = None
    email: Optional[str] = None
    tax_year: Optional[str] = None
    income: Optional[str] = None
    withholding: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class ValidatedCustomerRecord:
    customer_name: str
    email: str
    tax_year: int
    income: Decimal
    withholding: Decimal
    source_file: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.income, Decimal):
            self.income = Decimal(str(self.income))
        if not isinstance(self.withholding, Decimal):
            self.withholding = Decimal(str(self.withholding))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_name": self.customer_name,
            "email": self.email,
            "tax_year": self.tax_year,
            "income": self.income,
            "withholding": self.withholding,
            "source_file": self.source_file,
        }


@dataclass
class ValidationError:
    field: Optional[str]
    message: str
    source_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "source_file": self.source_file,
        }


@dataclass
class ValidationReport:
    valid_records: List[ValidatedCustomerRecord] = field(default_factory=list)
    errors: List[ValidationError] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid_record_count": len(self.valid_records),
            "error_count": len(self.errors),
            "valid_records": [r.to_dict() for r in self.valid_records],
            "errors": [e.to_dict() for e in self.errors],
        }
