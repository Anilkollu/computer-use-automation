from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ArtifactStep:
    action: str
    target: dict[str, Any]
    value: Any = None


@dataclass
class CapabilityArtifact:
    schema_version: str
    capability_id: str
    capability_version: int

    inputs: dict[str, dict[str, str]]
    steps: list[dict[str, Any]]

    outputs: dict[str, dict[str, str]]

    checkpoint: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)