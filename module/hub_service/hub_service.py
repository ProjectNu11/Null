from library.config import config, save_config
from module.hub_service import HubServiceNotEnabled

if not config.hub.enabled:
    raise HubServiceNotEnabled()

import requests
import urllib.parse
from typing import Literal, List, Union
from aiohttp import ClientResponseError
from graia.ariadne import get_running, Ariadne
from graia.ariadne.adapter import Adapter
from graia.ariadne.exception import AccountMuted, UnknownTarget
from graia.ariadne.message.chain import MessageChain

from library.model import HubMetadata, Module


class HubService:
    __auth__ = {}
    __initialized__ = False

    def __init__(self):
        with requests.Session() as session:
            with session.get(url=config.hub.url + config.hub.meta) as resp:
                config.hub.metadata = HubMetadata(**resp.json())
                save_config(config)
            with session.post(
                url=config.hub.url
                + config.hub.metadata.register_bot
                + "?secret="
                + config.hub.secret,
                json={
                    "id": config.account,
                    "name": config.name,
                    "num": config.num,
                    "devGroup": config.dev_group,
                    "owners": config.owners,
                },
            ) as resp:
                data = resp.json()
                config.num = data["num"]
                save_config(config)
            with session.post(
                url=config.hub.url + config.hub.metadata.authorize,
                data={"username": config.account, "password": config.hub.secret},
            ) as resp:
                if resp.status_code == 200:
                    self.__auth__ = {
                        "Authorization": f"Bearer {resp.json()['access_token']}"
                    }
                    self.__initialized__ = True

    @staticmethod
    async def update_metadata():
        async with get_running(Adapter).session.get(
            url=config.hub.url + config.hub.meta,
        ) as resp:
            config.hub.metadata = HubMetadata(**await resp.json())
            save_config(config)

    async def get_bearer(self):
        async with get_running(Adapter).session.post(
            url=config.hub.url + config.hub.metadata.authorize,
            data={"username": config.account, "password": config.hub.secret},
        ) as resp:
            self.__auth__ = {
                "Authorization": f"Bearer {(await resp.json())['access_token']}"
            }

    def get_auth_header(self):
        return self.__auth__

    async def heartbeat(self):
        async with get_running(Adapter).session.post(
            url=config.hub.url + config.hub.metadata.heartbeat, headers=self.__auth__
        ) as resp:
            if bots := await resp.json():
                ariadne = get_running(Ariadne)
                group_list = [g.id for g in await ariadne.getGroupList()]
                friend_list = [f.id for f in await ariadne.getFriendList()]
                for bot in bots:
                    notified = False
                    for dev_group in bot["devGroup"]:
                        if dev_group in group_list:
                            try:
                                await ariadne.sendGroupMessage(
                                    dev_group,
                                    MessageChain(
                                        f"{bot['name']}#{bot['num']} ({bot['id']}) 已离线"
                                    ),
                                )
                            except (AccountMuted, UnknownTarget, ClientResponseError):
                                continue
                            notified = True
                    for owner in bot["owners"]:
                        if owner in friend_list:
                            try:
                                await ariadne.sendFriendMessage(
                                    owner,
                                    MessageChain(
                                        f"{bot['name']}#{bot['num']} ({bot['id']}) 已离线"
                                    ),
                                )
                            except (UnknownTarget, ClientResponseError):
                                continue
                            notified = True
                    if notified:
                        await self.notified_missing(bot["id"])

    async def notified_missing(self, bot_id: int):
        async with get_running(Adapter).session.post(
            url=config.hub.url
            + config.hub.metadata.notified_missing
            + f"?bot_id={bot_id}",
            headers=self.__auth__,
        ) as resp:
            await resp.json()

    async def event_report(self, event_type: Literal["online", "offline"]):
        async with get_running(Adapter).session.post(
            url=config.hub.url
            + (
                config.hub.metadata.online_event
                if event_type == "online"
                else config.hub.metadata.offline_event
            ),
            headers=self.__auth__,
        ) as resp:
            await resp.json()

    async def search_module(
        self,
        name: str = "",
        pack: str = "",
        version: str = "",
        author: str = "",
        pypi: bool = "",
        category: Literal["utility", "entertainment", "misc"] = "",
        dependency: str = "",
    ) -> Union[None, List[Module]]:
        if not any(
            [name, pack, version, author, isinstance(pypi, bool), category, dependency]
        ):
            return
        if name == "*":
            params = "?all=True"
        else:
            params = []
            params.extend(
                f"{param_name}={urllib.parse.quote(param)}"
                for param_name, param in (
                    ("name", name),
                    ("pack", pack),
                    ("version", version),
                    ("author", author),
                    ("category", category),
                    ("dependency", dependency),
                )
                if param
            )

            if isinstance(pypi, bool):
                param.append(f"pypi={pypi}")
            params = f"?{'&'.join(params)}"
        async with get_running(Adapter).session.get(
            url=config.hub.url + config.hub.metadata.search_module + params,
            headers=self.__auth__,
        ) as resp:
            return [Module(**mod) for mod in (await resp.json())]

    async def download_module(self, name: str, version: str = "") -> Union[bytes, None]:
        params = f"?name={urllib.parse.quote(name.replace('-', '_'))}" + (
            f"&version={urllib.parse.quote(version)}" if version else ""
        )
        async with get_running(Adapter).session.get(
            url=config.hub.url + config.hub.metadata.download_module + params,
            headers=self.__auth__,
        ) as resp:
            return await resp.read() if resp.status == 200 else None


hs = HubService()
