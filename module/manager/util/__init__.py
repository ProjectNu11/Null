try:
    from module.hub_service.exception import HubServiceNotEnabled
    from module.hub_service import hs
except HubServiceNotEnabled:
    hs = None
