from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LoginRequestDto:
    username: str
    password: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoginRequestDto":
        if not isinstance(data, dict):
            raise ValueError("Informe Username e Password em um objeto JSON.")
        username = data.get("Username") or data.get("username")
        password = data.get("Password") or data.get("password")
        if not username or not password:
            raise ValueError("Username e Password são obrigatórios.")
        return cls(username=username, password=password)


@dataclass(frozen=True)
class TokenResponseDto:
    access_token: str
    usuario: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"access_token": self.access_token, "usuario": self.usuario}
