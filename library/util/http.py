import html


def html_escape(text: str) -> str:
    """
    Escape text to be used in HTML.

    :param text: The text to escape.
    :return: The escaped text.
    """

    string = html.escape(text)
    string = string.replace("\n", "<br />")
    return string
