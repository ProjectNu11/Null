from enum import Enum


class UserPerm(Enum):
    MEMBER = "MEMBER"
    ADMINISTRATOR = "ADMINISTRATOR"
    OWNER = "OWNER"
    BOT_OWNER = "BOT_OWNER"

    def __lt__(self, other: "UserPerm"):
        lv_map = {
            UserPerm.MEMBER: 1,
            UserPerm.ADMINISTRATOR: 2,
            UserPerm.OWNER: 3,
            UserPerm.BOT_OWNER: 4,
        }
        return lv_map[self] < lv_map[other]
