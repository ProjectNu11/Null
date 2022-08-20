from library.model import NConfig

config: NConfig = NConfig()
config.save()


from library.config.group_config import GroupConfig

group_config = GroupConfig()
