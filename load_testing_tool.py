#!/bin/python3
import argparse
import time
from collections import defaultdict
from typing import Sequence, List

import aiohttp
import asyncio
import datetime as dt


def filter_old_time(lst: Sequence[int], retention: dt.timedelta):
    retention_ns = retention.total_seconds() * 10**9
    return [e for e in lst if e > time.monotonic_ns() - retention_ns]


async def fetch(session: aiohttp.ClientSession, url: str, last_requests_timing: List[int]):
    request_start_ns = time.monotonic_ns()
    async with session.get(url) as response:
        request_time_ns = time.monotonic_ns() - request_start_ns
        last_requests_timing.append(time.monotonic_ns())
        last_requests_timing = filter_old_time(last_requests_timing, dt.timedelta(minutes=1))
        print(f'[{url}] status code: {response.status} '
              f'| response time, ms: {request_time_ns / 10 ** 6} '
              f'| requests/m: {len(last_requests_timing)}')


async def main(n: int, period: dt.timedelta, endpoints: Sequence[str]):
    interval_ns = round(period.total_seconds() / n * 10**9)

    async with aiohttp.ClientSession() as session:
        cycle_n = time.monotonic_ns() // interval_ns
        last_requests_timings = defaultdict(list)

        while True:
            if cycle_n != (current_cycle_n := time.monotonic_ns() // interval_ns):
                cycle_n = current_cycle_n
                for e in endpoints:
                    asyncio.create_task(fetch(session, e, last_requests_timings[e]))
            else:
                await asyncio.sleep(0.001)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Requests Benchmark',
        description='Sends n requests per t minutes on each endpoint',
        epilog='Text at the bottom of help')
    parser.add_argument('-r', '--requests', type=int, required=True, help='requests per minute')
    parser.add_argument('-e', '--endpoints', type=str, nargs='+', required=True, help='list of endpoints')
    parser.add_argument('-p', '--period', type=int, help='period in seconds', default=60)
    args = parser.parse_args()
    asyncio.run(main(args.requests, dt.timedelta(seconds=args.period), args.endpoints))
