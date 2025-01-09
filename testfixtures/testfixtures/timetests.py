#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timezone, timedelta
from .utils import parametrize


def datetime_encode_tests():
    return parametrize(
        "value,expect",
        [
            (
                "UTC Timezone",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
                "2024-03-11T01:02:03Z",
            ),
            (
                "+0h (UTC) Timezone",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=0))),
                "2024-03-11T01:02:03Z",
            ),
            (
                "+3h Timezone",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
                "2024-03-11T01:02:03+03:00",
            ),
            (
                "-3h Timezone",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
                "2024-03-11T01:02:03-03:00",
            ),
            (
                "+3:21 Timezone",
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
            ),
            (
                "Microseconds Ignored",
                datetime(2024, 3, 11, 1, 2, 3, 999, tzinfo=timezone.utc),
                "2024-03-11T01:02:03Z",
            ),
            (
                "Timezone Seconds Ignored (+03:21:31)",
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
            ),
            (
                "Timezone Seconds Ignored (-03:21:31)",
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
            ),
        ],
    )


def datetime_decode_tests():
    return parametrize(
        "value,expect",
        [
            (
                "No timezone",
                "2024-03-11T01:02:03",
                datetime(2024, 3, 11, 1, 2, 3).astimezone(),
            ),
            (
                "UTC Timezone 'Z'",
                "2024-03-11T01:02:03Z",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
            ),
            (
                "UTC Timezone '+00:00'",
                "2024-03-11T01:02:03+00:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
            ),
            (
                "+03:00 Timezone",
                "2024-03-11T01:02:03+03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
            ),
            (
                "-03:00 Timezone",
                "2024-03-11T01:02:03-03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
            ),
            (
                "+03:21 Timezone",
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
            ),
            (
                "Microseconds not allowed",
                "2024-03-11T01:02:03.999Z",
                None,
            ),
            (
                "Timezone with seconds not allowed",
                "2024-03-11T01:02:03+03:00:01",
                None,
            ),
        ],
    )


def datetimestamp_decode_tests():
    return parametrize(
        "value,expect",
        [
            (
                "UTC Timezone 'Z'",
                "2024-03-11T01:02:03Z",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
            ),
            (
                "UTC Timezone '+00:00'",
                "2024-03-11T01:02:03+00:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
            ),
            (
                "+03:00 Timezone",
                "2024-03-11T01:02:03+03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
            ),
            (
                "-03:00 Timezone",
                "2024-03-11T01:02:03-03:00",
                datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
            ),
            (
                "+03:21 Timezone",
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
            ),
            (
                "No Timezone",
                "2024-03-11T01:02:03",
                None,
            ),
            # Microseconds not allowed
            (
                "Microseconds not allowed",
                "2024-03-11T01:02:03.999Z",
                None,
            ),
            # Timezone with seconds not allowed
            (
                "Timezone with seconds not allowed",
                "2024-03-11T01:02:03+03:00:01",
                None,
            ),
        ],
    )
