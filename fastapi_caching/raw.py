from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

__all__ = ("RawCacheObject",)


@dataclass
class RawCacheObject:
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    meta: Dict[str, Any] = field(default_factory=dict)  # For future usage
