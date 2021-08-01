from pathlib import Path
from typing import Dict

import requests


class Download:

    login_url: str
    credentials: Dict[str, str]

    def __init__(self) -> None:
        self.connected = False
        self.latest_issue = None
        self.session: requests.Session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) "
                    "Gecko/20100101 Firefox/72.0"
                )
            }
        )

    def login_dict(self) -> Dict[str, str]:
        return {}

    def login(self) -> None:
        c = self.session.post(self.login_url, data=self.login_dict())
        c.raise_for_status()
        self.connected = True

    def latest_issue_url(self) -> str:
        raise NotImplementedError()

    def file_name(self, c) -> str:
        if not self.connected:
            self.login()
        url = self.latest_issue_url()
        return Path(url).name

    def get_latest_issue(self):
        if self.latest_issue is not None:
            return self.latest_issue
        if not self.connected:
            self.login()
        url = self.latest_issue_url()
        c = self.session.get(url)
        return c

    def save_latest_issue(self):
        c = self.get_latest_issue()
        full_path = Path(".") / self.file_name(c)
        full_path.write_bytes(c.content)
        print(f"File written: {full_path}")

    def get_content(self, url):
        return
