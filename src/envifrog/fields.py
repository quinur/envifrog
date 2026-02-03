from dataclasses import dataclass
from typing import Any, Optional, Callable, List


@dataclass
class Var:
    """
    Configuration for a specific environment variable field.

    Attributes:
        default: The default value if the environment variable is missing.
                 Use Ellipsis (...) to mark it as required.
        secret: If True, the value will be masked in string representations.
        min_val: Minimum allowed value (for numbers).
        max_val: Maximum allowed value (for numbers).
    """
    default: Any = ...
    secret: bool = False
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    prefix: Optional[str] = None
    validator: Optional[Any] = None  # Callable[[Any], bool]
    choices: Optional[list[Any]] = None
