from pocket import Pocket
from ..core.config import config_dict


class PocketAPI:
    def __init__(self):
        pocket_config = config_dict.get("api://getpocket.com", None)
        assert pocket_config is not None

        self.pocket = Pocket(
            consumer_key=pocket_config.get("consumer_key"),
            access_token=pocket_config.get("access_token"),
        )
        self.retrieve()

    def retrieve(self):
        self.json = self.pocket.retrieve()

    def __len__(self):
        return len(self.json["list"])

    def __getitem__(self, select):
        for i, elt in enumerate(self.json["list"].values()):
            if i == select:
                return elt

    def __iter__(self):
        yield from self.json["list"].values()

    def archive(self, id_):
        self.pocket.archive(id_).commit()
        self.retrieve()

    def delete(self, id_):
        self.pocket.delete(id_).commit()
        self.retrieve()
