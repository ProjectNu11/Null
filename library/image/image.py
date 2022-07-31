import asyncio
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from loguru import logger


class ImageUtil:
    def __int__(self):
        raise NotImplementedError("This class is not intended to be instantiated.")

    @staticmethod
    def paste_to_center(
        image: Image.Image, paste_image: Image.Image, x: int = None, y: int = None
    ):
        """
        Paste image to center of image

        :param image: Image object
        :param paste_image: Image object
        :param x: x position
        :param y: y position
        :return: Image object
        """

        image_width, image_height = image.size
        paste_image_width, paste_image_height = paste_image.size
        paste_image_x = x if x is not None else (image_width - paste_image_width) // 2
        paste_image_y = y if y is not None else (image_height - paste_image_height) // 2
        image.paste(paste_image, (paste_image_x, paste_image_y), mask=paste_image)
        return image

    @classmethod
    async def async_paste_to_center(
        cls, image: Image.Image, paste_image: Image.Image, x: int = None, y: int = None
    ):
        """
        Paste image to center of image

        :param image: Image object
        :param paste_image: Image object
        :param x: x position
        :param y: y position
        :return: Image object
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, cls.paste_to_center, image, paste_image, x, y
        )

    @staticmethod
    def round_corners(img: Image.Image, radius: int):
        """
        Round the corners of an image

        :param img: Image to round corners of
        :param radius: Radius of the rounded corners
        :return: Image with rounded corners
        """

        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0) + img.size, radius, fill=255)
        img.putalpha(mask)
        return img

    @classmethod
    async def async_round_corner(cls, img: Image.Image, radius: int):
        """
        Round the corners of an image asynchronously

        :param img: Image to round corners of
        :param radius: Radius of the rounded corners
        :return: Image with rounded corners
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.round_corners, img, radius)

    @staticmethod
    def crop_to_rect(img: Image.Image):
        """
        Crop an image to a rectangle

        :param img: Image to crop
        :return: Cropped image
        """

        size = min(img.size)
        img = img.crop(
            (
                (img.size[0] - size) // 2,
                (img.size[1] - size) // 2,
                (img.size[0] + size) // 2,
                (img.size[1] + size) // 2,
            )
        )
        return img

    @classmethod
    async def async_crop_to_rect(cls, img: Image.Image):
        """
        Crop an image to a rectangle asynchronously

        :param img: Image to crop
        :return: Cropped image
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.crop_to_rect, img)

    @classmethod
    def crop_to_circle(cls, img: Image.Image):
        """
        Crop an image to a circle

        :param img: Image to crop to a circle
        :return: Image cropped to a circle
        """

        size = min(img.size)
        img = cls.crop_to_rect(img)
        img = cls.round_corners(img, size // 2)
        return img

    @classmethod
    async def async_crop_to_circle(cls, img: Image.Image):
        """
        Crop an image to a circle asynchronously

        :param img: Image to crop to a circle
        :return: Image cropped to a circle
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.crop_to_circle, img)

    @classmethod
    def blur(cls, img: Image.Image, radius: int, boarder: bool = True):
        """
        Blur an image, shortcut for ImageFilter.GaussianBlur

        :param img: Image to blur
        :param radius: Radius of the blur
        :param boarder: Extend the image to include the blur
        :return: Image blurred
        """

        back = Image.new(
            "RGBA",
            (img.size[0] + radius * 4, img.size[1] + radius * 4)
            if boarder
            else img.size,
            (0, 0, 0, 0),
        )
        back.paste(img, (radius * 2, radius * 2) if boarder else (0, 0))
        img = back
        return img.filter(ImageFilter.GaussianBlur(radius=radius))

    @classmethod
    async def async_blur(cls, img: Image.Image, radius: int, boarder: bool = True):
        """
        Blur an image asynchronously, shortcut for ImageFilter.GaussianBlur

        :param img: Image to blur
        :param radius: Radius of the blur
        :param boarder: Extend the image to include the blur
        :return: Image blurred
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.blur, img, radius, boarder)

    @classmethod
    def get_shadow(cls, img: Image.Image, radius: int, opacity: int = 50):
        """
        Get a shadow of an image

        :param img: Image to get a shadow of
        :param radius: Radius of the shadow
        :param opacity: Opacity of the shadow
        :return: Image with a shadow
        """

        img = cls.blur(img, radius).getchannel("A")
        ratio = opacity / 100
        img = img.point(lambda x: int(x * ratio))
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        shadow.putalpha(img)
        return shadow

    @classmethod
    def add_blurred_shadow(cls, img: Image.Image, radius: int, opacity: int = 50):
        """
        Add a blurred shadow to an image

        :param img: Image to add a blurred shadow to
        :param radius: Radius of the blurred shadow
        :param opacity: Opacity of the blurred shadow
        :return: Image with a blurred shadow
        """

        img = cls.paste_to_center(cls.get_shadow(img, radius, opacity), img)
        return img

    @classmethod
    async def async_add_blurred_shadow(
        cls, img: Image.Image, radius: int, opacity: int = 50
    ):
        """
        Add a blurred shadow to an image asynchronously

        :param img: Image to add a blurred shadow to
        :param radius: Radius of the blurred shadow
        :param opacity: Opacity of the blurred shadow
        :return: Image with a blurred shadow
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, cls.add_blurred_shadow, img, radius, opacity
        )

    @classmethod
    def add_drop_shadow(cls, img: Image.Image, radius: int, opacity: int = 50):
        """
        Add a drop shadow to an image

        :param img: Image to add a drop shadow to
        :param radius: Radius of the drop shadow
        :param opacity: Opacity of the drop shadow
        :return: Image with a drop shadow
        """

        img = cls.paste_to_center(cls.get_shadow(img, radius, opacity), img, y=0)
        return img

    @classmethod
    async def async_add_drop_shadow(
        cls, img: Image.Image, radius: int, opacity: int = 50
    ):
        """
        Add a drop shadow to an image asynchronously

        :param img: Image to add a drop shadow to
        :param radius: Radius of the drop shadow
        :param opacity: Opacity of the drop shadow
        :return: Image with a drop shadow
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, cls.add_drop_shadow, img, radius, opacity
        )

    @classmethod
    def draw_rectangle(
        cls,
        img: Image.Image,
        x: int,
        y: int,
        end_x: int,
        end_y: int,
        color: tuple,
        round_radius: int = 0,
        shadow: bool = False,
    ):
        """
        Draw a rectangle on an image

        :param img: Image to draw a rectangle on
        :param x: X coordinate of the rectangle
        :param y: Y coordinate of the rectangle
        :param end_x: X coordinate of the rectangle's end
        :param end_y: Y coordinate of the rectangle's end
        :param color: Color of the rectangle
        :param round_radius: Radius of the rounded corners
        :param shadow: Draw a shadow under the rectangle
        :return: Image with a rectangle
        """

        width = end_x - x
        height = end_y - y
        rectangle = Image.new("RGBA", (width, height), (*color, 0))
        if round_radius > 0:
            rectangle = cls.round_corners(rectangle, round_radius)
        if shadow:
            rectangle = cls.add_blurred_shadow(rectangle, 10)
        rectangle = rectangle.resize((width, height))
        img.paste(rectangle, (x, y), mask=rectangle)
        return img

    @classmethod
    async def async_draw_rectangle(
        cls,
        img: Image.Image,
        x: int,
        y: int,
        end_x: int,
        end_y: int,
        color: tuple,
        round_radius: int = 0,
        shadow: bool = False,
    ):
        """
        Draw a rectangle on an image asynchronously

        :param img: Image to draw a rectangle on
        :param x: X coordinate of the rectangle
        :param y: Y coordinate of the rectangle
        :param end_x: X coordinate of the rectangle's end
        :param end_y: Y coordinate of the rectangle's end
        :param color: Color of the rectangle
        :param round_radius: Radius of the rounded corners
        :param shadow: Draw a shadow under the rectangle
        :return: Image with a rectangle
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            cls.draw_rectangle,
            img,
            x,
            y,
            end_x,
            end_y,
            color,
            round_radius,
            shadow,
        )

    @staticmethod
    def get_font(
        font_size: int,
        font_name: str = "sarasa-mono-sc-nerd-light.ttf",
        variant: str = None,
    ):
        """
        Get a font with the specified size, default to Sarasa Mono Nerd Light

        :param font_size: Size of the font
        :param font_name: Name of the font, must be in the assets/fonts folder
        :param variant: Variant of the font, must be in the assets/fonts folder
        :return: Font with the specified size
        """

        font = ImageFont.truetype(
            str(Path(Path(__file__).parent.parent, "assets", "fonts", font_name)),
            font_size,
        )

        if not variant:
            return font

        try:
            font.set_variation_by_name(variant)
        except OSError:
            logger.error(f"Font {font_name} is not a variation font.")
        finally:
            return font

    @staticmethod
    def draw_line(
        img: Image.Image,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: tuple,
        width: int = 1,
    ):
        """
        Draw a line on an image

        :param img: Image to draw a line on
        :param x1: X coordinate of the line's start
        :param y1: Y coordinate of the line's start
        :param x2: X coordinate of the line's end
        :param y2: Y coordinate of the line's end
        :param color: Color of the line
        :param width: Width of the line
        :return: Image with a line
        """

        draw = ImageDraw.Draw(img)
        draw.line((x1, y1, x2, y2), fill=color, width=width)
        return img

    @classmethod
    async def async_draw_line(
        cls,
        img: Image.Image,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: tuple,
        width: int = 1,
    ):
        """
        Draw a line on an image asynchronously

        :param img: Image to draw a line on
        :param x1: X coordinate of the line's start
        :param y1: Y coordinate of the line's start
        :param x2: X coordinate of the line's end
        :param y2: Y coordinate of the line's end
        :param color: Color of the line
        :param width: Width of the line
        :return: Image with a line
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, cls.draw_line, img, x1, y1, x2, y2, color, width
        )
