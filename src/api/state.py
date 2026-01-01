from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.data_store import AgentsSnapshot
from src.repository import AgentRepo


@dataclass
class AppState:
    snapshot: AgentsSnapshot
    webmanus_repo: Optional[AgentRepo] = None

