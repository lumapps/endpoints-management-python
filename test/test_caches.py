# Copyright 2016, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import

import collections
import datetime
import unittest2

from expects import be, be_a, be_none, equal, expect, raise_error

from google.scc import (caches, CheckAggregationOptions,
                        ReportAggregationOptions)


_TEST_NUM_ENTRIES = 3  # arbitrary


class TestDequeOutLRUCache(unittest2.TestCase):

    def test_constructor_should_set_up_a_default_deque(self):
        c = caches.DequeOutLRUCache(_TEST_NUM_ENTRIES)
        expect(c.out_deque).to(be_a(collections.deque))

    def test_constructor_should_fail_on_bad_deques(self):
        testf = lambda: caches.DequeOutLRUCache(_TEST_NUM_ENTRIES,
                                                out_deque=object())
        expect(testf).to(raise_error(ValueError))

    def test_constructor_should_accept_deques(self):
        a_deque = collections.deque()
        c = caches.DequeOutLRUCache(_TEST_NUM_ENTRIES, out_deque=a_deque)
        expect(c.out_deque).to(be(a_deque))

    def test_lru(self):
        lru_limit = 2
        cache = caches.DequeOutLRUCache(lru_limit)
        cache[1] = 1
        cache[2] = 2
        cache[3] = 3
        expect(len(cache)).to(equal(2))
        expect(cache[2]).to(equal(2))
        expect(cache[3]).to(equal(3))
        expect(cache.get(1)).to(be_none)
        expect(len(cache.out_deque)).to(be(1))
        cache[4] = 4
        expect(cache.get(2)).to(be_none)
        expect(len(cache.out_deque)).to(be(2))


class _Timer(object):
    def __init__(self, auto=False):
        self.auto = auto
        self.time = 0

    def __call__(self):
        if self.auto:
            self.tick()
        return self.time

    def tick(self):
        self.time += 1


_TEST_TTL = 3  # arbitrary


class TestDequeOutTTLCache(unittest2.TestCase):
    # pylint: disable=fixme
    #
    # TODO: add a ttl test based on the one in cachetools testsuite

    def test_constructor_should_set_up_a_default_deque(self):
        c = caches.DequeOutTTLCache(_TEST_NUM_ENTRIES, _TEST_TTL)
        expect(c.out_deque).to(be_a(collections.deque))

    def test_constructor_should_fail_on_bad_deques(self):
        testf = lambda: caches.DequeOutTTLCache(_TEST_NUM_ENTRIES, _TEST_TTL,
                                                out_deque=object())
        expect(testf).to(raise_error(ValueError))

    def test_constructor_should_accept_deques(self):
        a_deque = collections.deque()
        c = caches.DequeOutTTLCache(3, 3, out_deque=a_deque)
        expect(c.out_deque).to(be(a_deque))

    def test_lru(self):
        lru_limit = 2
        expiry = 100
        cache = caches.DequeOutTTLCache(lru_limit, expiry)
        cache[1] = 1
        cache[2] = 2
        cache[3] = 3
        expect(len(cache)).to(equal(2))
        expect(cache[2]).to(equal(2))
        expect(cache[3]).to(equal(3))
        expect(cache.get(1)).to(be_none)
        expect(len(cache.out_deque)).to(be(1))
        cache[4] = 4
        expect(cache.get(2)).to(be_none)
        expect(len(cache.out_deque)).to(be(2))

    def test_ttl(self):
        cache = caches.DequeOutTTLCache(2, ttl=1, timer=_Timer())
        expect(cache.timer()).to(equal(0))
        expect(cache.ttl).to(equal(1))

        cache[1] = 1
        expect(set(cache)).to(equal({1}))
        expect(len(cache)).to(equal(1))
        expect(cache[1]).to(equal(1))

        cache.timer.tick()
        expect(set(cache)).to(equal({1}))
        expect(len(cache)).to(equal(1))
        expect(cache[1]).to(equal(1))

        cache[2] = 2
        expect(set(cache)).to(equal({1, 2}))
        expect(len(cache)).to(equal(2))
        expect(cache[1]).to(equal(1))
        expect(cache[2]).to(equal(2))

        cache.timer.tick()
        expect(set(cache)).to(equal({2}))
        expect(len(cache)).to(equal(1))
        expect(cache[2]).to(equal(2))
        expect(cache.get(1)).to(be_none)


class _DateTimeTimer(object):
    def __init__(self, auto=False):
        self.auto = auto
        self.time = datetime.datetime(1970, 1, 1)

    def __call__(self):
        if self.auto:
            self.tick()
        return self.time

    def tick(self):
        self.time += datetime.timedelta(seconds=1)


class TestCreate(unittest2.TestCase):

    def test_should_fail_if_bad_options_are_used(self):
        should_fail = [
            lambda: caches.create(object()),
            lambda: caches.create(None)
        ]
        for testf in should_fail:
            expect(testf).to(raise_error(ValueError))

    def test_should_return_num_if_cache_size_not_positive(self):
        should_be_none = [
            lambda: caches.create(CheckAggregationOptions(num_entries=0)),
            lambda: caches.create(CheckAggregationOptions(num_entries=-1)),
            lambda: caches.create(ReportAggregationOptions(num_entries=0)),
            lambda: caches.create(ReportAggregationOptions(num_entries=-1)),
        ]
        for testf in should_be_none:
            expect(testf()).to(be_none)

    def test_should_return_ttl_cache_if_flush_interval_is_positive(self):
        delta = datetime.timedelta(seconds=1)
        should_be_ttl = [
            lambda timer: caches.create(
                CheckAggregationOptions(num_entries=1, flush_interval=delta),
                timer=timer
            ),
            lambda timer: caches.create(
                ReportAggregationOptions(num_entries=1, flush_interval=delta),
                timer=timer
            ),
        ]
        for testf in should_be_ttl:
            timer = _DateTimeTimer()
            sync_cache = testf(timer)
            expect(sync_cache).to(be_a(caches.LockedObject))
            with sync_cache as cache:
                expect(cache).to(be_a(caches.DequeOutTTLCache))
                expect(cache.timer()).to(equal(0))
                cache[1] = 1
                expect(set(cache)).to(equal({1}))
                expect(cache.get(1)).to(equal(1))
                timer.tick()
                expect(cache.get(1)).to(equal(1))
                timer.tick()
                expect(cache.get(1)).to(be_none)

            # Is still TTL without the custom timer
            sync_cache = testf(None)
            expect(sync_cache).to(be_a(caches.LockedObject))
            with sync_cache as cache:
                expect(cache).to(be_a(caches.DequeOutTTLCache))

    def test_should_return_a_lru_cache_if_flush_interval_is_negative(self):
        delta = datetime.timedelta(seconds=-1)
        should_be_ttl = [
            lambda: caches.create(
                CheckAggregationOptions(num_entries=1, flush_interval=delta),
            ),
            lambda: caches.create(
                ReportAggregationOptions(num_entries=1, flush_interval=delta)),
        ]
        for testf in should_be_ttl:
            sync_cache = testf()
            expect(sync_cache).to(be_a(caches.LockedObject))
            with sync_cache as cache:
                expect(cache).to(be_a(caches.DequeOutLRUCache))