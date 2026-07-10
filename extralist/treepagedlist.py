# coding: utf-8
# Author: João S. O. Bueno
# License: LGPL v 3.0

from collections.abc import MutableSequence

import typing as t

class _EmptyNode:
    left = right = None
    def __len__(self):
        return 0
    @property
    def value(self):
        return []

class _Node:
    def __init__(self, value: MutableSequence, start=0, parent=None):
        self.value = value
        self.parent = parent
        self.dirty = False
        self.start = start
        self.stop = self.start + len(value)

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value: t.Self):
        self.dirty = True
        self._left = value
        self.start = len(value)


    def __getitem__(self, index: slice):
        start, stop, step = index.indicices(len(self))
        return self.data[index]

    def __setitem__(self, index, value):
        self.data[index] = value

    def __delitem__(self, index):
        del self.data[index]

    def insert(self, index, value):
        self.data.insert(index, value)

    def __len__(self):
        return len(self.data)



class _Tree:
    def __init__(self, pagesize):
        self.pagesize = pagesize

    @property
    def start(self):
        return len(self.left)

    @property
    def end(self):
        return self.start + len(self.value)


    def __getitem__(self, index: slice):
        start, stop, step = index.indicices(len(self))
        return self.data[index]

    def __setitem__(self, index, value):
        self.data[index] = value

    def __delitem__(self, index):
        del self.data[index]

    def insert(self, index, value):
        self.data.insert(index, value)

    def __len__(self):
        return len(self.data)



class TreePagedList(MutableSequence):
    pagesize = 1000

    def __init__(self, initial=(), /, pagesize: t.Optional[int] = None):
        if pagesize is not None:
            self.pagesize = pagesize
        self.data = list(initial)

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, value):
        self.data[index] = value

    def __delitem__(self, index):
        del self.data[index]

    def insert(self, index, value):
        self.data.insert(index, value)

    def __len__(self):
        return len(self.data)
