from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import httpx
from pydantic import BaseModel, Field, HttpUrl, field_validator

from ..core.config import config_dict


class RaindropTag(BaseModel):
    """Model representing a tag in a Raindrop item."""

    _id: str
    name: str


class RaindropCollection(BaseModel):
    """Model representing a collection that a Raindrop item belongs to."""

    _id: int
    name: Optional[str] = None
    color: Optional[str] = None
    ref: Optional[str] = Field(None, alias="$ref")
    id: Optional[int] = Field(None, alias="$id")
    oid: Optional[int] = None


class RaindropItem(BaseModel):
    """Model representing a Raindrop bookmark item."""

    id_: int = Field(alias="_id")
    title: str
    excerpt: Optional[str] = None
    note: Optional[str] = None
    link: HttpUrl
    created: datetime
    lastUpdate: datetime
    tags: List[str] = Field(default_factory=list)
    cover: Optional[HttpUrl] = None
    collection: RaindropCollection
    type: Literal["link", "article", "image", "video", "document"]
    user: Dict[str, Any]  # Simplified; contains user information
    important: bool = False
    media: List[Dict] = Field(default_factory=list)
    broken: bool = False
    creatorRef: Optional[Dict] = None

    @field_validator("cover", mode="before", json_schema_input_type=str)
    @classmethod
    def cover_validate(cls, value: str) -> Optional[str]:
        if value == "":
            return None
        return value


class RaindropAPI:
    """API client for interacting with Raindrop.io.

    Go to https://app.raindrop.io/settings/integrations
    Create a new application and copy the test token

    """

    def __init__(self):
        raindrop_config = config_dict.get("raindrop.io", None)
        assert raindrop_config is not None, (
            "Raindrop.io configuration not found."
        )

        self.token = raindrop_config.get("token")
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.token}"}
        )
        self.async_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.token}"}
        )

    async def get_collections_async(self) -> List[Dict[str, Any]]:
        response = await self.async_client.get(
            "https://api.raindrop.io/rest/v1/collections"
        )
        response.raise_for_status()
        return response.json()["items"]

    async def get_user_async(self) -> Dict[str, Any]:
        response = await self.async_client.get(
            "https://api.raindrop.io/rest/v1/user"
        )
        response.raise_for_status()
        return response.json()

    async def get_tags_async(self) -> List[RaindropTag]:
        response = await self.async_client.get(
            "https://api.raindrop.io/rest/v1/tags/"
        )
        response.raise_for_status()
        return [RaindropTag(**tag) for tag in response.json()["items"]]

    async def get_items_page_async(self, page: int = 0) -> List[RaindropItem]:
        response = await self.async_client.get(
            f"https://api.raindrop.io/rest/v1/raindrops/0?page={page}"
        )
        response.raise_for_status()
        return [RaindropItem(**item) for item in response.json()["items"]]

    async def get_items_async(
        self, page: int = 0, cumul: None | list[RaindropItem] = None
    ) -> List[RaindropItem]:
        response = await self.async_client.get(
            f"https://api.raindrop.io/rest/v1/raindrops/0?page={page}"
        )
        response.raise_for_status()
        json = response.json()
        if cumul is None:
            cumul = []
        cumul.extend([RaindropItem(**item) for item in json["items"]])
        if len(cumul) == json["count"]:
            return cumul
        return await self.get_items_async(page=page + 1, cumul=cumul)

    def get_collections(self) -> List[Dict[str, Any]]:
        response = self.client.get(
            "https://api.raindrop.io/rest/v1/collections"
        )
        response.raise_for_status()
        return response.json()["items"]

    def get_user(self) -> Dict[str, Any]:
        response = self.client.get("https://api.raindrop.io/rest/v1/user")
        response.raise_for_status()
        return response.json()

    def get_tags(self) -> List[RaindropTag]:
        response = self.client.get("https://api.raindrop.io/rest/v1/tags/")
        response.raise_for_status()
        return [RaindropTag(**tag) for tag in response.json()["items"]]

    def get_items_page(self, page: int = 0) -> List[RaindropItem]:
        response = self.client.get(
            f"https://api.raindrop.io/rest/v1/raindrops/0?page={page}"
        )
        response.raise_for_status()
        return [RaindropItem(**item) for item in response.json()["items"]]
