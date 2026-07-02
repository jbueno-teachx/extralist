from __future__ import annotations

import builtins
from collections.abc import Iterator, MutableSequence
from typing import TypeVar, overload

_T = TypeVar("_T")

# slice_ may be a slice, a (start, stop, step) triple, or None (full sequence).
# Use builtins.slice in annotations: the instance attribute is also named "slice".
_SliceSpec = builtins.slice | tuple[int | None, int | None, int | None] | None


class SlicedView(MutableSequence[_T]):
    """A View on a sequence.
    Allows one to have sub-lists of a list without duplicating the underlying data.

    Reading a slice from an object of this class will produce a new view
    on the original data. (But passing a SlicedView as data to it,
    will wrap that view in an extra layer)


    """

    data: MutableSequence[_T]
    slice: builtins.slice

    def __init__(self, data: MutableSequence[_T], slice_: _SliceSpec = None) -> None:
        self.data = data
        if isinstance(slice_, builtins.slice):
            start = slice_.start
            stop = slice_.stop
            step = slice_.step
        else:
            start, stop, step = slice_ if slice_ is not None else (0, len(data), 1)
        if start is None:
            start = 0
        if stop is None:
            stop = len(data)
        if step is None:
            step = 1

        self.slice = builtins.slice(start, stop, step)

    def _real_index(self, index: int) -> int:
        real_index = self.slice.start + index * self.slice.step
        if real_index > len(self.data):
            raise IndexError("Index out of range.")
        return real_index

    @overload
    def __getitem__(self, index: int) -> _T: ...

    @overload
    def __getitem__(self, index: builtins.slice) -> SlicedView[_T]: ...

    def __getitem__(self, index: int | builtins.slice) -> _T | SlicedView[_T]:
        if isinstance(index, builtins.slice):
            return self.__class__(
                self.data,
                builtins.slice(
                    self.slice.start + index.start,
                    min(self.slice.start + (index.start or 0), self.slice.stop),
                    self.slice.step * (index.step or 1),
                ),
            )
        if index < 0:
            raise NotImplementedError("Can't use negative indexes on a SlicedView")
        return self.data[self._real_index(index)]

    def __setitem__(self, index: int | builtins.slice, value: _T) -> None:
        if isinstance(index, builtins.slice):
            raise NotImplementedError("Can't assign to slice on SlicedView")
        if index < 0:
            raise NotImplementedError("Can't use negative indexes on a SlicedView")
        self.data[self._real_index(index)] = value

    def __delitem__(self, index: int | builtins.slice) -> None:
        if isinstance(index, builtins.slice):
            self.data.__delitem__(
                builtins.slice(
                    self.slice.start + (index.start or 0),
                    min(
                        self.slice.stop,
                        self.slice.start
                        + (
                            index.stop
                            if index.stop is not None
                            else (self.slice.start + len(self)) // self.slice.step
                        ),
                    ),
                    self.slice.step * (index.step or 1),
                )
            )

        else:
            del self.data[self._real_index(index)]
            self.slice = builtins.slice(
                self.slice.start, self.slice.stop - self.slice.step, self.slice.step
            )

    def __len__(self) -> int:
        if len(self.data) < self.slice.start:
            return 0
        return (min(self.slice.stop, len(self.data)) - self.slice.start) // self.slice.step

    def __iter__(self) -> Iterator[_T]:
        # Iterate the logical view length so a short underlying sequence cannot
        # raise during iteration (len() already clamps to the data).
        for i in range(len(self)):
            yield self.data[self._real_index(i)]

    def insert(self, position: int, value: _T) -> None:
        if not (0 <= position <= len(self)):
            raise IndexError(
                "Can't insert new item at position '{}' in slice".format(position)
            )
        self.data.insert(self._real_index(position), value)
        self.slice = builtins.slice(
            self.slice.start, self.slice.stop + self.slice.step, self.slice.step
        )
