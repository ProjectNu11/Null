from graia.ariadne.app import Ariadne
from graia.ariadne.message.commander import Commander
from graia.ariadne.message.commander.saya import CommanderBehaviour
from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya.behaviour import GraiaSchedulerBehaviour
from pydantic import BaseModel
from pydantic.networks import AnyHttpUrl

import module
from library.config import config


class SessionConfig(BaseModel):
    host: AnyHttpUrl = ""
    account: int = ""
    verify_key: str = ""


if __name__ == """__main__""":
    ariadne = Ariadne(MiraiSession(**SessionConfig(**config.dict()["essential"]).dict()))
    saya = ariadne.create(Saya)
    ariadne.create(GraiaScheduler)
    ariadne.create(Commander)
    saya.install_behaviours(
        ariadne.create(BroadcastBehaviour),
        ariadne.create(GraiaSchedulerBehaviour),
        ariadne.create(CommanderBehaviour),
    )
    with saya.module_context():
        for mod in module.__all__:
            saya.require(f"module.{mod}")
    ariadne.launch_blocking()
