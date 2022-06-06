from graia.ariadne.app import Ariadne
from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya.behaviour import GraiaSchedulerBehaviour
from loguru import logger

import module
from library.config import config
from library.util.dependency import install_dependency

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
            if not mod.loaded:
                continue
            try:
                saya.require(mod.pack)
            except ModuleNotFoundError:
                install_dependency(mod)
                try:
                    saya.require(mod.pack)
                except Exception as e:
                    logger.error(e)
            except Exception as e:
                logger.error(e)
    ariadne.launch_blocking()
