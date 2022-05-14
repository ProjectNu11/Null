class HubServiceNotEnabled(Exception):
    """HubService 未启用"""

    def __init__(self):
        super().__init__("HubService 未启用")
