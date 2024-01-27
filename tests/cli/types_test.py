from itertools import groupby
from logging import getLogger
from string import ascii_uppercase

import faker
import pytest
from faker import Faker

from BAET.cli.types import Merger

fake: Faker = faker.Faker()

logger = getLogger("testing")


@pytest.fixture()
def letter_int_dict() -> dict[str, int]:
    return {k: int(fake.numerify("##")) for k in ascii_uppercase}


class TestMerge:
    @pytest.mark.repeat(100)
    def test_merge_dictionaries(self, letter_int_dict: dict[str, int]) -> None:
        def selector(p: tuple[str, int]) -> str:
            return p[0]

        def composer(p: tuple[str, int], q: tuple[str, int]) -> tuple[str, int]:
            return (p[0], p[1] + q[1])

        others: list[tuple[str, int]] = sorted(
            zip(
                fake.random_choices(ascii_uppercase, length=26),
                [int(fake.numerify("##")) for _ in range(26)],
                strict=True,
            ),
            key=lambda tup: tup[0],
        )

        logger.info("letter_int_dict: %r", letter_int_dict)
        logger.info("Others: %r", list(others))

        combined = others
        combined.extend(letter_int_dict.items())
        sorted_combined = sorted(combined, key=lambda x: x[0])
        grouped = groupby(sorted_combined, key=lambda x: x[0])
        grouped_reduced = [(k, [t[1] for t in tup]) for k, tup in grouped]
        expected = {k: sum(tup) for k, tup in grouped_reduced}

        m = Merger(selector=selector, composer=composer)
        actual = dict(m(combined))

        logger.info("Combined: %r", combined)
        logger.info("Expected: %r", expected)
        logger.info("Actual: %r", actual)

        assert expected == actual
