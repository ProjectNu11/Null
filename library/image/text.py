import asyncio
import re
import string
from typing import Literal

from PIL import ImageDraw, ImageFont, Image

from .image import ImageUtil


class TextUtil:
    def __int__(self):
        raise NotImplementedError("This class is not intended to be instantiated.")

    @classmethod
    def break_fix(
        cls, text: str, width: int, font: ImageFont.FreeTypeFont, draw: ImageDraw.Draw
    ):
        """
        Cut text into multiple lines.

        :param text: Text to cut
        :param width: Width of the text
        :param font: Font of the text
        :param draw: Draw object of the text
        :return: List of lines
        """

        if not text:
            return
        lo = 0
        hi = len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            t = text[:mid]
            w, h = draw.textsize(t, font=font)
            if w <= width:
                lo = mid
            else:
                hi = mid - 1
        t = text[:lo]
        w, h = draw.textsize(t, font=font)
        yield t, w, h
        yield from cls.break_fix(text[lo:], width, font, draw)

    @classmethod
    def render_text(
        cls,
        text: str,
        color: tuple,
        font: ImageFont.FreeTypeFont,
        width: int = None,
        align: Literal["left", "center", "right"] = "left",
        accurate: bool = True,
    ):
        """
        Render text to image.

        :param text: text to render
        :param color: color of text
        :param font: font of text
        :param width: width of image
        :param align: align of text, not used if accurate is False
        :param accurate: whether to use accurate location of text,
        will have significant longer render time on large text
        :return: image
        """

        if not accurate:
            return cls.render_text_non_accurate(text, color, font, width)

        if width is None:
            _ = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
            width, height = _.textsize(text, font=font)
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            bbox = draw.textbbox((0, 0), text, font=font)
            draw.text((-bbox[0], -bbox[1]), text, font=font, fill=color)
            return image
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
        pieces = list(cls.break_fix(text, width - 2, font, draw))
        image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), "\n".join([p[0] for p in pieces]), font=font)
        height = sum(p[2] for p in pieces)
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        y = -bbox[1]
        for text, _width, _height in pieces:
            x = -bbox[0]
            if align == "left":
                x += 0
            elif align == "center":
                x += (image.size[0] - _width) // 2
            elif align == "right":
                x += image.size[0] - _width
            else:
                raise ValueError("align must be one of left, center, right")
            draw.text((x, y), text, font=font, fill=color)
            y += _height
        return image

    @classmethod
    async def async_render_text(
        cls, text: str, width: int, color: tuple, font: ImageFont.FreeTypeFont
    ):
        """
        Render text to image asynchronously.

        :param text: text to render
        :param width: width of image
        :param color: color of text
        :param font: font of text
        :return: image
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, cls.render_text, text, width, color, font
        )

    @classmethod
    def get_index_location(
        cls,
        text: str,
        index: int,
        width: int,
        font: ImageFont.FreeTypeFont,
        draw: ImageDraw.Draw,
    ):
        """
        Get location of index in text.

        :param text: text to get location
        :param index: index of text
        :param width: width of text
        :param font: font of text
        :param draw: draw object of text
        :return: location of index
        """

        text = text[:index]
        pieces = list(cls.break_fix(text, width - 2, font, draw))
        __check = list(cls.break_fix(text + "\u3000", width - 2, font, draw))
        if len(pieces) != len(__check):
            width = 0
            height = sum(p[2] for p in pieces)
        else:
            width = pieces[-1][1]
            height = sum(p[2] for p in pieces[:-1])
        return width, height

    @staticmethod
    def get_cut_str(text, cut):
        """
        自动断行，用于 Pillow 等不会自动换行的场景
        """

        punc = """，,、。.？?）》】“"‘'；;：:！!·`~%^& """
        si = 0
        i = 0
        next_str = text
        str_list = []

        while re.search(r"\n\n\n\n\n", next_str):
            next_str = re.sub(r"\n\n\n\n\n", "\n", next_str)
        for s in next_str:
            si += 1 if s in string.printable else 2
            i += 1
            if next_str == "":
                break
            elif next_str[0] == "\n":
                next_str = next_str[1:]
            elif s == "\n":
                str_list.append(next_str[: i - 1])
                next_str = next_str[i - 1 :]
                si = 0
                i = 0
                continue
            if si > cut:
                try:
                    if next_str[i] in punc:
                        i += 1
                except IndexError:
                    str_list.append(next_str)
                    return str_list
                str_list.append(next_str[:i])
                next_str = next_str[i:]
                si = 0
                i = 0
        str_list.append(next_str)
        i = 0
        non_wrap_str = []
        for p in str_list:
            if p == "":
                break
            elif p[-1] == "\n":
                p = p[:-1]
            non_wrap_str.append(p)
            i += 1
        return non_wrap_str

    @classmethod
    def render_text_non_accurate(
        cls,
        text: str,
        color: tuple,
        font: ImageFont.FreeTypeFont,
        width: int = None,
    ):
        """
        Render text to image, fast but not accurate.

        :param text: text to render
        :param color: color of text
        :param font: font of text
        :param width: width of image
        :return: image
        """

        char_size = font.getsize("\u3000")
        char_count = width // char_size[0]
        text = "\n".join(cls.get_cut_str(text, char_count))
        text_size = font.getsize_multiline(text)
        image = Image.new("RGBA", text_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text((-bbox[0], -bbox[1]), text, font=font, fill=color)
        return image

    @staticmethod
    def get_font(
        font_size: int,
        font_name: str = "sarasa-mono-sc-nerd-light.ttf",
        variant: str = None,
    ):
        """
        Get a font with the specified size, default to Sarasa Mono Nerd Light
        Proxy for ImageUtil.get_font.

        :param font_size: Size of the font
        :param font_name: Name of the font, must be in the assets/fonts folder
        :param variant: Variant of the font, must be in the assets/fonts folder
        :return: Font with the specified size
        """

        return ImageUtil.get_font(font_size, font_name, variant)
