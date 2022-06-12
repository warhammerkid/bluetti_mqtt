from dataclasses import dataclass


@dataclass(frozen=True)
class BluettiDevice:
    address: str
    type: str
    sn: str
