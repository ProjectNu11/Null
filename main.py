from graia.ariadne.app import Ariadne

from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya.behaviour import GraiaSchedulerBehaviour

import module
from library.config import config

if __name__ == """__main__""":
    ariadne = Ariadne(
        MiraiSession(**config.dict(include={"host", "account", "verify_key"}))
    )
    saya = ariadne.create(Saya)
    ariadne.create(GraiaScheduler)
    saya.install_behaviours(
        ariadne.create(BroadcastBehaviour),
        ariadne.create(GraiaSchedulerBehaviour),
    )
    with saya.module_context():
        for mod in module.__all__:
            saya.require(mod.pack)
    ariadne.launch_blocking()
