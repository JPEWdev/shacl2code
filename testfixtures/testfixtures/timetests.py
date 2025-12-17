#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest
from pytest import param
from datetime import datetime, timezone, timedelta


def datetime_encode_tests():
    return pytest.mark.parametrize(
        "value,expect",
        [
            param(
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
                "2024-03-11T01:02:03Z",
                id="UTC Timezone",
            ),
            param(
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=0))),
                "2024-03-11T01:02:03Z",
                id="+0h (UTC) Timezone",
            ),
            param(
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
                "2024-03-11T01:02:03+03:00",
                id="+3h Timezone",
            ),
            param(
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
                "2024-03-11T01:02:03-03:00",
                id="-3h Timezone",
            ),
            param(
                datetime(
                    2024,
                    3,
                    11,
                    1,
                    2,
                    3,
                    tzinfo=timezone(timedelta(hours=3, minutes=21)),
                ),
                "2024-03-11T01:02:03+03:21",
                id="+3:21 Timezone",
            ),
            param(
                datetime(2024, 3, 11, 1, 2, 3, 999, tzinfo=timezone.utc),
                "2024-03-11T01:02:03Z",
                id="Microseconds Ignored",
            ),
            param(
                datetime(
                    2024,
                    3,
                    11,
                    1,
                    2,
                    3,
                    tzinfo=timezone(timedelta(hours=3, minutes=21, seconds=31)),
                ),
                "2024-03-11T01:02:03+03:21",
                id="Timezone Seconds Ignored (+03:21:31)",
            ),
            param(
                datetime(
                    2024,
                    3,
                    11,
                    1,
                    2,
                    3,
                    tzinfo=timezone(timedelta(hours=-3, minutes=-21, seconds=-31)),
                ),
                "2024-03-11T01:02:03-03:21",
                id="Timezone Seconds Ignored (-03:21:31)",
            ),
        ],
    )


def datetime_decode_tests():
    return pytest.mark.parametrize(
        "value,expect",
        [
            param(
                "2024-03-11T01:02:03",
                datetime(2024, 3, 11, 1, 2, 3).astimezone(),
                id="No timezone",
            ),
            param(
                "2024-03-11T01:02:03Z",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
                id="UTC Timezone 'Z'",
            ),
            param(
                "2024-03-11T01:02:03+00:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
                id="UTC Timezone '+00:00'",
            ),
            param(
                "2024-03-11T01:02:03+03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
                id="+03:00 Timezone",
            ),
            param(
                "2024-03-11T01:02:03-03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
                id="-03:00 Timezone",
            ),
            param(
                "2024-03-11T01:02:03+03:21",
                datetime(
                    2024,
                    3,
                    11,
                    1,
                    2,
                    3,
                    tzinfo=timezone(timedelta(hours=3, minutes=21)),
                ),
                id="+03:21 Timezone",
            ),
            param(
                "2024-03-11T01:02:03.999Z",
                None,
                id="Microseconds not allowed",
            ),
            param(
                "2024-03-11T01:02:03+03:00:01",
                None,
                id="Timezone with seconds not allowed",
            ),
        ],
    )


def datetimestamp_decode_tests():
    return pytest.mark.parametrize(
        "value,expect",
        [
            param(
                "2024-03-11T01:02:03Z",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
                id="UTC Timezone 'Z'",
            ),
            param(
                "2024-03-11T01:02:03+00:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
                id="UTC Timezone '+00:00'",
            ),
            param(
                "2024-03-11T01:02:03+03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
                id="+03:00 Timezone",
            ),
            param(
                "2024-03-11T01:02:03-03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
                id="-03:00 Timezone",
            ),
            param(
                "2024-03-11T01:02:03+03:21",
                datetime(
                    2024,
                    3,
                    11,
                    1,
                    2,
                    3,
                    tzinfo=timezone(timedelta(hours=3, minutes=21)),
                ),
                id="+03:21 Timezone",
            ),
            param(
                "2024-03-11T01:02:03",
                None,
                id="No Timezone",
            ),
            # Microseconds not allowed
            param(
                "2024-03-11T01:02:03.999Z",
                None,
                id="Microseconds not allowed",
            ),
            # Timezone with seconds not allowed
            param(
                "2024-03-11T01:02:03+03:00:01",
                None,
                id="Timezone with seconds not allowed",
            ),
        ],
    )
