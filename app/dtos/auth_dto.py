from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LoginRequestDto:
    username: str
    password: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoginRequestDto":
        username = data.get("Username") or data.get("username")
        password = data.get("Password") or data.get("password")
        if not username or not password:
            raise ValueError("Username e Password são obrigatórios.")
        return cls(username=username, password=password)


@dataclass(frozen=True)
class TokenResponseDto:
    access_token: str

    def to_dict(self) -> Dict[str, str]:
        return {"access_token": self.access_token}
