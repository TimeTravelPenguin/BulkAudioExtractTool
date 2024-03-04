"""Helper methods for string manipulation."""

from collections.abc import Callable, Sequence


def pretty_join[T](
    items: Sequence[T],
    message: str,
    *,
    bullet: str = "∙ ",
    formatter: Callable[[T], str] | None = None,
    force_newline: bool = False,
) -> str:
    """Join a sequence of items into a pretty list string.

    Parameters
    ----------
    items : Sequence[T]
        A sequence of strings to join.

    message : str
        The message to prepend to the list.

    bullet : str
        The bullet to use for each item.

    formatter : Callable[[T], str], optional
        A function to format each item. If None, then no formatter will be used.

    force_newline : bool
        If True, then a newline will be forced even if there is only one item.


    Returns
    -------
    str
        The prettified list string.


    Examples
    --------
    >>> items = ["one", "two", "three", "four"]
    >>> pretty_join(items, "Test items")
    """

    def _formatter(item: T) -> str:
        return f"'{item}'"

    if formatter is None:
        formatter = _formatter

    if not force_newline and len(items) == 0:
        return f"{message}: []"
    elif not force_newline and len(items) == 1:
        return f"{message}: {formatter(items[0])}"

    newline_base = f"\n{' ' * 4}{bullet}"
    joiner = f",{newline_base}"
    formatted = joiner.join([formatter(p) for p in items])
    return f"{message}:{newline_base}{formatted}"


if __name__ == "__main__":
    items = ["one", "two", "three", "four"]
    print(pretty_join(items, "Test items"))
    print(pretty_join(["world"], "hello", formatter=lambda x: f"~{x}~"))
