from abc import ABC
from typing import Optional


class BaseApi(ABC):
    base_url: Optional[str] = None

    method: str = "GET"


class GETBaseApi(BaseApi):
    method = "GET"

    def get_complete_url(self, **kwargs) -> str:
        raise NotImplementedError


class POSTBaseApi(BaseApi):
    method = "POST"

    def get_body(self, **kwargs) -> str:
        raise NotImplementedError
