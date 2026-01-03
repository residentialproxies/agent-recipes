from __future__ import annotations

from dataclasses import dataclass

from src.data_store import AgentsSnapshot
from src.repository import AgentRepo
from src.repository.users import UserRepo


@dataclass
class AppState:
    snapshot: AgentsSnapshot
    webmanus_repo: AgentRepo | None = None
    user_repo: UserRepo | None = None
