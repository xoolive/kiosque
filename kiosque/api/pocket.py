from typing import Iterator, Literal, TypedDict

import httpx

from ..core.config import config_dict


class UnknownJSON(TypedDict): ...


class PocketRetrieveEntry(TypedDict):
    item_id: str
    resolved_id: str  # useful for duplicates
    given_url: str
    resolved_url: str
    given_title: str
    resolved_title: str
    favorite: Literal[0, 1]
    status: Literal[0, 1, 2]
    excerpt: str  # articles only
    is_article: Literal[0, 1]
    has_image: Literal[0, 1, 2]
    has_video: Literal[0, 1, 2]
    word_count: str
    tags: UnknownJSON
    authors: UnknownJSON
    images: UnknownJSON
    videos: UnknownJSON
    time_added: str


class PocketRetrieveResponse(TypedDict):
    maxActions: int
    status: Literal[0, 1]
    list: dict[str, PocketRetrieveEntry]


class PocketAPI:
    json: PocketRetrieveResponse

    def __init__(self):
        pocket_config = config_dict.get("getpocket.com", None)
        assert pocket_config is not None

        self.consumer_key = pocket_config.get("consumer_key")
        self.access_token = pocket_config.get("access_token")
        self.client = httpx.Client()
        self.async_client = httpx.AsyncClient()

    def __len__(self):
        return len(self.json["list"])

    def __getitem__(self, select):
        for i, elt in enumerate(self.json["list"].values()):
            if i == select:
                return elt

    def __iter__(self) -> Iterator[PocketRetrieveEntry]:
        yield from self.json["list"].values()

    def retrieve(self, offset=30) -> PocketRetrieveResponse:
        # https://getpocket.com/developer/docs/v3/retrieve
        r = self.client.post(
            "https://getpocket.com/v3/get",
            json={
                "consumer_key": self.consumer_key,
                "access_token": self.access_token,
                "count": 30,
                "offset": offset,
                "total": 1,
                "sort": "newest",
            },
            headers={
                "Content-Type": "application/json",
                "X-Accept": "application/json",
            },
        )
        r.raise_for_status()
        self.json = r.json()
        return self.json

    async def async_retrieve(self, offset=0) -> PocketRetrieveResponse:
        r = await self.async_client.post(
            "https://getpocket.com/v3/get",
            json={
                "consumer_key": self.consumer_key,
                "access_token": self.access_token,
                "count": 30,
                "offset": offset,
                "total": 1,
                "sort": "newest",
                "state": "unread",
            },
            headers={
                "Content-Type": "application/json",
                "X-Accept": "application/json",
            },
        )
        r.raise_for_status()
        self.json = r.json()
        return self.json

    def action(self, action: str, item_id: str):
        r = self.client.post(
            "https://getpocket.com/v3/send",
            json={
                "consumer_key": self.consumer_key,
                "access_token": self.access_token,
                "actions": [{"action": action, "item_id": item_id}],
            },
            headers={
                "Content-Type": "application/json",
                "X-Accept": "application/json",
            },
        )
        r.raise_for_status()
        return r.json()

    async def async_action(self, action: str, item_id: str):
        r = await self.async_client.post(
            "https://getpocket.com/v3/send",
            json={
                "consumer_key": self.consumer_key,
                "access_token": self.access_token,
                "actions": [{"action": action, "item_id": item_id}],
            },
            headers={
                "Content-Type": "application/json",
                "X-Accept": "application/json",
            },
        )
        r.raise_for_status()
        return r.json()
