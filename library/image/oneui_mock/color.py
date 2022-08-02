class Color:
    TEXT_COLOR_LIGHT = (0, 0, 0)
    TEXT_COLOR_DARK = (255, 255, 255)

    DESCRIPTION_COLOR_LIGHT = (139, 139, 139)
    DESCRIPTION_COLOR_DARK = (221, 221, 221)

    FOREGROUND_COLOR_LIGHT = (252, 252, 252)
    FOREGROUND_COLOR_DARK = (38, 38, 38)

    BACKGROUND_COLOR_LIGHT = (246, 246, 246)
    BACKGROUND_COLOR_DARK = (2, 2, 2)

    LINE_COLOR_LIGHT = (231, 231, 231)
    LINE_COLOR_DARK = (90, 90, 90)

    HINT_COLOR_LIGHT = (232, 237, 243)
    HINT_COLOR_DARK = (24, 38, 64)

    HIGHLIGHT_COLOR_LIGHT = (72, 112, 206)
    HIGHLIGHT_COLOR_DARK = (103, 143, 242)

    SWITCH_ENABLE_COLOR = (58, 129, 255)
    SWITCH_DISABLE_COLOR = (220, 220, 220)
    SWITCH_DISABLE_COLOR_DARK = (147, 149, 140)

    def __setattr__(self, *_):
        raise AttributeError("Looks like you are trying to set a color value.")


PALETTE = [
    "#D32F2F",
    "#C62828",
    "#B71C1C",
    "#D50000",
    "#D81B60",
    "#C2185B",
    "#AD1457",
    "#880E4F",
    "#C51162",
    "#AB47BC",
    "#9C27B0",
    "#8E24AA",
    "#7B1FA2",
    "#6A1B9A",
    "#4A148C",
    "#AA00FF",
    "#7E57C2",
    "#673AB7",
    "#5E35B1",
    "#512DA8",
    "#4527A0",
    "#311B92",
    "#7C4DFF",
    "#651FFF",
    "#6200EA",
    "#5C6BC0",
    "#3F51B5",
    "#3949AB",
    "#303F9F",
    "#283593",
    "#1A237E",
    "#3D5AFE",
    "#304FFE",
    "#1976D2",
    "#1565C0",
    "#0D47A1",
    "#2962FF",
    "#0277BD",
    "#01579B",
    "#006064",
    "#00796B",
    "#00695C",
    "#004D40",
    "#2E7D32",
    "#1B5E20",
    "#33691E",
    "#BF360C",
    "#DD2C00",
    "#8D6E63",
    "#795548",
    "#6D4C41",
    "#5D4037",
    "#4E342E",
    "#3E2723",
    "#546E7A",
    "#455A64",
    "#37474F",
    "#263238",
]
