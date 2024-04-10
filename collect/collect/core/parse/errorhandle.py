from typing import Union

from collect.collect.middlewares import ParseError


def raise_error(error: Union[BaseException, None], msg: str, content: list):
    if isinstance(error, ParseError):
        error: ParseError
        if not error.content:
            error.content = content
    else:
        error = ParseError(msg=msg, error=error, content=content)
    raise error
