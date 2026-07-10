# coding: utf-8
# Author: João S. O. Bueno
# License: LGPL v 3.0
import bisect
from collections.abc import MutableSequence
from functools import reduce
import sys
import warnings

from .defaultlist import DefaultList




def chunk_sequence(sequence, size):
    sequence = iter(sequence)
    while True:
        chunk = []
        try:
            for i in range(size):
                chunk.append(next(sequence))
        except StopIteration:
            break
        yield chunk
    if chunk:
        yield chunk




class _Page:
    __slots__ = ("start", "end", "data")


def _empty_page():
    p = _Page()
    p.start = p.end = 0
    p.data = []
    return p


class SequencePagedList(MutableSequence):
    """
    Sequence designed for high-performance inserting/deleting of elements in the middle.

    Python's list and other stdlib sequence types store a contiguous sequence of objects,
    so there is no easy sequence that allows arbitrary insertion or erasing of items
    in the middle of the body without a huge performance cost, as any insertion or
    deletion implies copying over all the remaining elements of the sequence to another
    position.

    SequencePagedList amortizes that by holding several "pages" with sequence parts, so that each
    insertion only affects one page at a time.

    """

    # Change this to True on an instance if slices should be SequencePagedList —
    # otherwise they will be plain (un-paged) sequences.

    slice_to_paged = False

    _lock_pagesize = False

    def __new__(cls, *args, **kw):
        warnings.warn(
            "SequencePagedList implementation currently has unfixed bugs. "
            "Its use in production is not recommended."
        )
        return super().__new__(cls)

    def __init__(self, sequence=None, pagesize=1000, page_class=list):
        self._reset(pagesize, page_class)
        self._fill(sequence)

    def _reset(self, pagesize, page_class):
        self.pagesize = pagesize
        self.page_class = page_class
        # DefaultList is used because when computing slices that extend to
        # self.END the page number will be one more than the actual existing pages.
        # (and len(self.pages) is super-useful to keep track of the actual number of
        # pages)
        self.pages = DefaultList(default_factory=_empty_page, append_on_extra=True)
        self._dirt_log = []

    @classmethod
    def _from_pages(cls, pages, pagesize, page_class):
        self = cls.__new__(cls)
        self._reset(pagesize, page_class)
        for i, page in enumerate(pages):
            self._append_page(page)
            if len(page) != pagesize:
                self._dirt_log.append([i, len(page) - pagesize])
        return self

    @property
    def pagesize(self):
        return self._pagesize

    @pagesize.setter
    def pagesize(self, value):
        if not self._lock_pagesize:
            self._pagesize = value
            self._lock_pagesize = True
            return
        raise RuntimeError("Pagesize for {} can't be changed after instantiation".format(self.__class__.__name__))

    def _fill(self, sequence):
        if not hasattr(sequence, "__len__"):
            for chunk in chunk_sequence(sequence, self.pagesize):
                self._append_page(self.page_class(chunk))
            return
        for page_start in range(0, len(sequence), self.pagesize):
            self._append_page(self.page_class(sequence[page_start: page_start + self.pagesize]))

    def _append_page(self, chunk):
        page = _Page()
        # page.start = len(self.pages) * self.pagesize
        page.data = chunk
        self.pages.append(page)

    def _adjust_dirt(self, page_number, amount, absolute=False):
        dirt_record = bisect.bisect_left(self._dirt_log, [page_number, -sys.maxsize])
        if (len(self._dirt_log) <= dirt_record or not self._dirt_log[dirt_record][0] == page_number):
            if amount:
                bisect.insort(self._dirt_log, [page_number, amount])
            return
        else:
            if not absolute:
                self._dirt_log[dirt_record][1] += amount
            else:
                self._dirt_log[dirt_record][1] = amount
            if self._dirt_log[dirt_record][1] == 0:
                del self._dirt_log[dirt_record]

    def _reset_dirt(self, page_number = None):
        if page_number is not None:
            amount = len(self.pages[page_number].data) - self.pagesize
            self._adjust_dirt(page_number, amount, absolute=True)
            return
        self._dirt_log = []
        for i, page in enumerate(self.pages):
            amount = len(page.data) - self.pagesize
            if amount:
                self._dirt_log.append([i, amount])


    def _local_offset(self, page_number):
        dirt_record = bisect.bisect_left(self._dirt_log, [page_number, -sys.maxsize])
        if len(self._dirt_log) <= dirt_record or not self._dirt_log[dirt_record][0] == page_number:
            return 0
        return self._dirt_log[dirt_record][1]

    def _get_indices(self, index):
        page_number= index // self.pagesize
        if not self._dirt_log:
            return page_number,  index % self.pagesize

        while True:
            # TODO: optimize this by enabling relative offset seeks:
            page_offset = self._get_offset_for_page(page_number)

            element_index = (index - page_offset) - (page_number * self.pagesize)
            if 0 <= element_index < self.pagesize + self._local_offset(page_number):
                break
            if element_index < 0:
                page_number -= 1
                if page_number < 0:
                    raise IndexError
            else:
                page_number += 1
        return page_number, element_index

    def _get_offset_for_page(self, page_number):
        offset = 0
        for dirt in self._dirt_log:
            if dirt[0] >= page_number:
                break
            offset += dirt[1]
        return offset

    def _get_slice_interval(self, slice_):
        s_start, s_stop, s_step = slice_.indices(len(self))
        s_stop = s_start + (s_stop - s_start) - (s_stop - s_start) % s_step

        lower_page, start_index = self._get_indices(s_start)
        upper_page, end_index = self._get_indices(s_stop)
        middle_pages = list(range(lower_page + 1, upper_page))

        return lower_page, start_index, middle_pages, upper_page, end_index

    def __getitem__(self, index):
        if isinstance(index, slice):
            if index.step is not None and index.step != 1:
                result_generator = (self[i] for i in range(*index.indices(len(self))))
                return (
                    self.__class__(result_generator, pagesize=self.pagesize, page_class=self.page_class)
                        if self.slice_to_paged else
                    self.page_class(result_generator)
                )
            lower_page, start_index, middle_pages, upper_page, end_index = self._get_slice_interval(index)
            if not self.slice_to_paged:
                if lower_page < upper_page:
                    result_slice = reduce(lambda prev, next: prev + next,
                                    (self.pages[i].data for i in middle_pages),
                                    self.pages[lower_page].data[start_index:]
                    ) + self.pages[upper_page].data[:end_index]
                else:
                    result_slice = self.pages[lower_page].data[start_index: end_index]

                return result_slice if self.page_class is list else self.page_class(result_slice)
            if lower_page < upper_page:
                return (self.__class__._from_pages((
                        [self.pages[lower_page].data[start_index:]] +
                        [self.pages[i].data[:] for i in middle_pages] +
                        [self.pages[upper_page].data[:end_index] ]
                    ),
                    pagesize = self.pagesize,
                    page_class = self.page_class
                ))
            else:
                return self.__class__(
                    self.pages[lower_page].data[start_index: end_index],
                    pagesize=self.pagesize,
                    page_class=self.page_class,
                )

        if index < 0:
            index += len(self)
        page_number, page_index = self._get_indices(index)
        return self.pages[page_number].data[page_index]

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            values = value
            if not hasattr(values, "__len__"):
                values = list(values)
            if index.step is None or index.step == 1:
                lower_page, start_index, middle_pages, upper_page, end_index = self._get_slice_interval(index)
                # TODO :specialize if values is instance of SequencePagedList
                if len(values) <= self.pagesize and lower_page == upper_page:
                        self.pages[lower_page].data[start_index: end_index] = values
                        self._adjust_dirt(lower_page, len(values) - (end_index - start_index))
                        return
                    # Add the end of values to the upper page:
                else:
                    start = 0; end = len(values)
                    if end_index != 0:
                        self.pages[upper_page].data[:end_index] = values[-end_index:]
                        end -= end_index
                        if end_index > len(values):
                            self._reset_dirt(upper_page)
                    if start_index < len(self.pages[lower_page].data):
                        len_lower_page = len(self.pages[lower_page].data)
                        self.pages[lower_page].data[start_index:] = values[:len_lower_page - start_index]
                        # self._reset_dirt(lower_page) # (pagesize is unchanged)
                        start = len_lower_page - start_index

                        for page_num in middle_pages:
                            self.pages[page_num].data[:] = values[start: min(start + self.pagesize, end)]
                            self._reset_dirt(page_num)
                            start += self.pagesize
                            if start >= end:
                                break

                        if not middle_pages:
                            page_num = lower_page

                        if start >= end:
                            # values is finished and there are middle pages left
                            del self.pages[page_num + 1: middle_pages[-1] + 1]
                        else:
                            # need to insert new page(s)
                            for j, start in enumerate(range(start, end, self.pagesize), page_num + 1):
                                new_page = _Page()
                                new_page.data = self.page_class(values[start: min(start + self.pagesize, end)])
                                self.pages.insert(j, new_page)

                        self._reset_dirt()
                        return

                    # add middle pages

            else:
                # extended slice: copy items one by one.
                all_indices = range(*index.indices(len(self)))
                if len(all_indices) != len(values):
                    raise ValueError(
                        "attempt to assign sequence of size {} to extended slice of size {}".format(
                        len(value), len(all_indices))
                    )
                for i, v in zip(all_indices, values):
                    self[i] = v
                return

        if index < 0:
            index += len(self)
        page_number, page_index = self._get_indices(index)
        self.pages[page_number].data[page_index] = value

    def __delitem__(self, index):
        if isinstance(index, slice):
            if index.step is None or index.step == 1:
                lower_page, start_index, middle_pages, upper_page, end_index = self._get_slice_interval(index)
                if lower_page == upper_page:
                    self.pages[lower_page].data[start_index:end_index] = []
                    self._reset_dirt(lower_page)
                    return
                self.pages[lower_page].data[start_index:] = []
                self.pages[upper_page].data[:end_index] = []
                if middle_pages:
                    del self.pages[middle_pages[0]:middle_pages[-1] + 1]
                self._reset_dirt()
                return
            else:
                # extended slice: del items one by one.
                del_count = 0
                for single_index in range(*index.indices(len(self))):
                    del self[single_index - del_count]
                    del_count += 1

                return

        page_number, page_index = self._get_indices(index)
        del self.pages[page_number].data[page_index]
        self._adjust_dirt(page_number, -1)

    def __len__(self):
        last_page_number = len(self.pages) - 1
        return self.pagesize * last_page_number + len(self.pages[-1].data) + self._get_offset_for_page(last_page_number)

    def insert(self, index, value):
        page_number, page_index = self._get_indices(index)
        self.pages[page_number].data.insert(page_index, value)
        self._adjust_dirt(page_number, +1)


