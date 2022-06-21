from library.config import config
from . import HubServiceNotEnabled

if not config.hub.enabled:
    raise HubServiceNotEnabled()

import aiohttp
import requests
import urllib.parse
from typing import Literal, List, Union
from aiohttp import ClientResponseError
from graia.ariadne import Ariadne
from graia.ariadne.exception import AccountMuted, UnknownTarget
from graia.ariadne.message.chain import MessageChain

from library.model import HubMetadata, Module


class HubService:
    __auth__: dict = {}
    __initialized__: bool = False
    __session__: requests.session() = None
    __aio_session__: aiohttp.ClientSession = None

    def __init__(self):
        self.__session__ = requests.session()
        self.update_metadata()
        self.register_bot()
        self.authorize()
        self.__initialized__ = True

    def update_metadata(self):
        with self.__session__.get(url=config.hub.url + config.hub.meta) as resp:
            config.hub.metadata = HubMetadata(**resp.json())
            config.save()

    def register_bot(self):
        with self.__session__.post(
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
            config.save()

    def authorize(self):
        with self.__session__.post(
            url=config.hub.url + config.hub.metadata.authorize,
            data={"username": config.account, "password": config.hub.secret},
        ) as resp:
            if resp.status_code == 200:
                self.__auth__ = {
                    "Authorization": f"Bearer {resp.json()['access_token']}"
                }

    async def async_update_metadata(self):
        await self.check_session()
        async with self.__aio_session__.get(
            url=config.hub.url + config.hub.meta,
        ) as resp:
            config.hub.metadata = HubMetadata(**await resp.json())
            config.save()

    async def async_authorize(self):
        await self.check_session()
        async with self.__aio_session__.post(
            url=config.hub.url + config.hub.metadata.authorize,
            data={"username": config.account, "password": config.hub.secret},
        ) as resp:
            if resp.status == 200:
                self.__auth__ = {
                    "Authorization": f"Bearer {(await resp.json())['access_token']}"
                }

    def get_auth_header(self):
        return self.__auth__

    async def heartbeat(self):
        await self.check_session()
        async with self.__aio_session__.post(
            url=config.hub.url + config.hub.metadata.heartbeat, headers=self.__auth__
        ) as resp:
            if bots := await resp.json():
                ariadne = Ariadne.current()
                group_list = [g.id for g in await ariadne.get_group_list()]
                friend_list = [f.id for f in await ariadne.get_friendList()]
                for bot in bots:
                    if self.notify_missing(bot, group_list, friend_list):
                        await self.notified_missing(bot["id"])

    @staticmethod
    async def notify_missing(
        bot: dict, group_list: List[int], friend_list: List[int]
    ) -> bool:
        ariadne = Ariadne.current()
        dev_group = bot["devGroup"]
        owner = bot["owners"]
        target_group_list = [group for group in group_list if group in dev_group]
        target_friend_list = [friend for friend in friend_list if friend in owner]
        notified = False
        for group in target_group_list:
            try:
                await ariadne.send_group_message(
                    group, MessageChain(f"{bot['name']}#{bot['num']} ({bot['id']}) 已离线")
                )
                notified = True
            except (AccountMuted, UnknownTarget, ClientResponseError):
                continue
        for friend in target_friend_list:
            try:
                await ariadne.send_friend_message(
                    friend,
                    MessageChain(f"{bot['name']}#{bot['num']} ({bot['id']}) 已离线"),
                )
                notified = True
            except (UnknownTarget, ClientResponseError):
                continue
        return notified

    async def notified_missing(self, bot_id: int):
        await self.check_session()
        async with self.__aio_session__.post(
            url=config.hub.url
            + config.hub.metadata.notified_missing
            + f"?bot_id={bot_id}",
            headers=self.__auth__,
        ) as resp:
            await resp.json()

    async def event_report(self, event_type: Literal["online", "offline"]):
        await self.check_session()
        async with self.__aio_session__.post(
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
        await self.check_session()
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
                params.append(f"pypi={pypi}")
            params = f"?{'&'.join(params)}"
        async with self.__aio_session__.get(
            url=config.hub.url + config.hub.metadata.search_module + params,
            headers=self.__auth__,
        ) as resp:
            return [Module(**mod) for mod in (await resp.json())]

    async def download_module(self, name: str, version: str = "") -> Union[bytes, None]:
        await self.check_session()
        params = f"?name={urllib.parse.quote(name.replace('-', '_'))}" + (
            f"&version={urllib.parse.quote(version)}" if version else ""
        )
        async with self.__aio_session__.get(
            url=config.hub.url + config.hub.metadata.download_module + params,
            headers=self.__auth__,
        ) as resp:
            return await resp.read() if resp.status == 200 else None

    async def check_session(self):
        if self.__aio_session__:
            return
        self.__aio_session__ = aiohttp.ClientSession()


hs = HubService()
