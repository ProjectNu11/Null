"""
Hub Service
中心服务
"""
import json
from datetime import datetime

from graia.ariadne import get_running, Ariadne
from graia.ariadne.adapter import Adapter
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.mirai import (BotOnlineEvent,
                                       BotOfflineEventForce,
                                       BotOfflineEventDropped,
                                       BotOfflineEventActive)
from graia.ariadne.message.chain import MessageChain
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema

from library.config import config, HubMetadata, save_config

saya = Saya.current()
channel = Channel.current()

channel.name("HubService")
channel.author("nullqwertyuiop")
channel.description("中心服务")

auth = {}


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def hub_service_authorize():
    config.hub.metadata = await get_metadata(3)
    token = await get_token(3)
    auth.update({"Authorization": f"Bearer {token}"})
    save_config(config)


async def get_metadata(retry_time: int):
    async with get_running(Adapter).session.get(
            url=config.hub.url + config.hub.meta
    ) as resp:
        if retry_time <= 0:
            resp.raise_for_status()
        if resp.status == 200:
            return HubMetadata(**await resp.json())
        else:
            return await get_metadata(retry_time - 1)


async def get_token(retry_time: int):
    async with get_running(Adapter).session.post(
            url=config.hub.url + config.hub.metadata.authorize,
            data={"username": config.essential.account,
                  "password": config.hub.secret}
    ) as resp:
        if retry_time <= 0:
            resp.raise_for_status()
        if resp.status == 200:
            data = await resp.json()
        elif resp.status == 404:
            if await register_bot():
                data = await get_token(retry_time - 1)
            else:
                resp.raise_for_status()
        else:
            data = await get_token(retry_time - 1)
        return data["access_token"]


async def register_bot():
    async with get_running(Adapter).session.post(
            url=(config.hub.url
                 + config.hub.metadata.register_bot
                 + "?secret=" + config.hub.secret),
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {"id": config.essential.account,
                 "name": config.essential.name,
                 "num": config.essential.num,
                 "maintainer": [],
                 "devGroup": config.essential.dev_group,
                 "owners": config.essential.owners}
            )) as resp:
        return True if resp.status == 200 else False


async def get_announcement():
    async with get_running(Adapter).session.get(
            url=(config.hub.url + config.hub.metadata.announcement),
            headers=auth
    ) as resp:
        data = await resp.json()
        data["time"] = datetime.fromisoformat(data["time"])
        return data


async def heartbeat():
    async with get_running(Adapter).session.post(
            url=(config.hub.url + config.hub.metadata.heartbeat),
            headers=auth
    ) as resp:
        if bots := await resp.json():
            ariadne = get_running(Ariadne)
            groups = await ariadne.getGroupList()
            friends = await ariadne.getFriendList()
            for bot in bots:
                if dev_groups := list(filter(
                        lambda group:
                        group.id in bot['devGroup'],
                        groups
                )):
                    await ariadne.sendGroupMessage(
                        dev_groups[0],
                        MessageChain(f"Bot {bot['name']}#{bot['num']} 已离线！")
                    )
                    await get_running(Adapter).session.post(
                        url=(config.hub.url
                             + config.hub.metadata.notified_missing
                             + "?bot_id="
                             + str(bot['id'])),
                        headers=auth
                    )
                    continue
                if owners := list(filter(
                        lambda friend:
                        friend.id in bot['owners'],
                        friends
                )):
                    await ariadne.sendFriendMessage(
                        owners[0],
                        MessageChain(f"{bot['name']}#{bot['num']} ({bot['id']}) 已离线！")
                    )
                    await get_running(Adapter).session.post(
                        url=(config.hub.url
                             + config.hub.metadata.notified_missing
                             + "?bot_id="
                             + str(bot['id'])),
                        headers=auth
                    )
                    continue


@channel.use(SchedulerSchema(timer=timers.every_minute()))
async def hub_service_heartbeat_report():
    if auth:
        await heartbeat()


@channel.use(ListenerSchema(listening_events=[BotOnlineEvent]))
async def hub_service_online_report():
    if auth:
        await get_running(Adapter).session.post(
            url=config.hub.url + config.hub.metadata.online_event,
            headers=auth
        )


@channel.use(ListenerSchema(listening_events=[BotOfflineEventForce, BotOfflineEventDropped, BotOfflineEventActive]))
async def hub_service_offline_report():
    if auth:
        await get_running(Adapter).session.post(
            url=config.hub.url + config.hub.metadata.offline_event,
            headers=auth
        )
