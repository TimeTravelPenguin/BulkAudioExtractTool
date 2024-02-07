"""Custom type to parse cli args with click."""

import re
from collections import OrderedDict
from collections.abc import Callable, Iterable
from re import Pattern
from typing import Any, Protocol, override, runtime_checkable

import rich_click as click
from rich.repr import Result


class RegexPatternParamType(click.ParamType):
    """Regex Pattern type for parsing with click."""

    name = "RegexPattern"

    @override
    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> Pattern[str]:
        if isinstance(value, Pattern):
            return value

        try:
            return re.compile(value)
        except ValueError:
            self.fail(f"'{value!r}' is an invalid pattern...", param, ctx)


RegexPattern = RegexPatternParamType()


@runtime_checkable
class Equatable(Protocol):
    """A protocol asserting that an object has an implementation of `__eq__`."""

    def __eq__(self, __value: object) -> bool:  # noqa: D105
        ...


class Merger[T: Equatable, K: Equatable]:
    """A class to merge elements of a list, compared via a comparer and composed via a composer function.

    This class is effectively an aggregator or folder.
    """

    def __init__(self, selector: Callable[[T], K], composer: Callable[[T, T], T]) -> None:
        self._selector = selector
        self._composer = composer

    def __call__(self, it: Iterable[T]) -> list[T]:
        """Merge the elements of the given iterable.

        Elements are compared using the provided selector.
        Elements that are found to be equal are merged using the provided composer.

        Parameters
        ----------
        it : Iterable[T] The iterable of elements to merge.


        Returns
        -------
        list[T] A list of merged elements.
        """
        merged: OrderedDict[K, T] = OrderedDict()
        for item in it:
            key = self._selector(item)
            if key not in merged:
                merged[key] = item
                continue

            merged[key] = self._composer(merged[key], item)

        return list(merged.values())


class FFmpegArgsRepr:
    """A class to represent FFmpeg arguments for rich pretty-printy."""

    def __init__(self, args: list[str]) -> None:
        self.args = args

    def __rich_repr__(self) -> Result:
        """Rich representation of the object."""
        yield self.args


FFmpegArgsRepr.__name__ = "FFmpeg"
