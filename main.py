from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config as ariadne_config,
)
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya.behaviour import GraiaSchedulerBehaviour

from library.context import scheduler
from library.config import config

ariadne = Ariadne(
    connection=ariadne_config(
        config.account,
        config.verify_key,
        HttpClientConfig(host=config.host),
        WebsocketClientConfig(host=config.host),
    )
)
saya = ariadne.create(Saya)
scheduler.set(ariadne.create(GraiaScheduler))
saya.install_behaviours(
    ariadne.create(BroadcastBehaviour),
    ariadne.create(GraiaSchedulerBehaviour),
)

if __name__ == """__main__""":
    from module import modules

    modules.require_modules(saya, log_exception=False)
    ariadne.launch_blocking()
