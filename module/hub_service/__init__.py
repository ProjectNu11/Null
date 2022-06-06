from library.config import config
from .exception import HubServiceNotEnabled

if not config.hub.enabled:
    raise HubServiceNotEnabled

from graia.ariadne.event.mirai import (
    BotOnlineEvent,
    BotOfflineEventActive,
    BotOfflineEventForce,
    BotOfflineEventDropped,
    BotReloginEvent,
)
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from .hub_service import hs

saya = Saya.current()
channel = Channel.current()

channel.name("ModuleManager")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(SchedulerSchema(timer=timers.every_minute()))
async def hub_service_heartbeat_report():
    if hs.get_auth_header():
        await hs.heartbeat()


@channel.use(ListenerSchema(listening_events=[BotOnlineEvent, BotReloginEvent]))
async def hub_service_bot_online_event():
    if hs.get_auth_header():
        await hs.event_report("online")


@channel.use(
    ListenerSchema(
        listening_events=[
            BotOfflineEventActive,
            BotOfflineEventForce,
            BotOfflineEventDropped,
        ]
    )
)
async def hub_service_bot_offline_event():
    if hs.get_auth_header():
        await hs.event_report("offline")
