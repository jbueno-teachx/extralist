"""Tests for paged list implementations.

Behaviour is checked against the same operations on a plain ``list``
(oracle) wherever the public sequence contract applies.

Common contract tests are parametrized over ``SequencePagedList`` and
(when enabled) ``TreePagedList``. Implementation-specific tests target
``SequencePagedList`` only.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable, MutableSequence, Sequence

import pytest

from extralist import SequencePagedList, TreePagedList

# Classes under test for the shared list-oracle suite.
# TreePagedList is stubbed; keep its parametrization commented until implemented.
PAGED_LIST_CLASSES = [
    SequencePagedList,
    # TreePagedList,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_paged(
    cls: type,
    sequence: Iterable | None = (),
    pagesize: int | None = None,
):
    """Build a paged-list instance, silencing intentional production warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        if sequence is None:
            return cls()
        if pagesize is None:
            return cls(sequence)
        return cls(sequence, pagesize=pagesize)


def pair(
    cls: type,
    data: Iterable,
    pagesize: int | None = 10,
) -> tuple[MutableSequence, list]:
    """Return (paged(data), list(data)) for oracle comparisons.

    Default *pagesize* is 10 so multi-chunk behaviour is exercised; pass
    ``pagesize=None`` to use the class constructor default.
    """
    control = list(data)
    return make_paged(cls, control, pagesize), control


def assert_oracle(paged: Sequence, control: list) -> None:
    assert list(paged) == control
    assert len(paged) == len(control)


def page_data_len(paged: SequencePagedList) -> int:
    """Sum of element counts stored in SequencePagedList pages."""
    return sum(len(paged.pages[i].data) for i in range(len(paged.pages)))


# ---------------------------------------------------------------------------
# Construction / empty  (shared)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_empty_constructor(paged_cls):
    """Paged list() with no args should behave like list()."""
    x = make_paged(paged_cls, None)
    assert_oracle(x, [])


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_empty_sequence_constructor(paged_cls):
    x = make_paged(paged_cls, [])
    assert_oracle(x, [])


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_construct_from_range_and_iterator(paged_cls):
    x = make_paged(paged_cls, range(25), pagesize=10)
    assert_oracle(x, list(range(25)))

    y = make_paged(paged_cls, iter(range(25)), pagesize=10)
    assert_oracle(y, list(range(25)))


# ---------------------------------------------------------------------------
# Single-index access / mutation (shared oracle)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_single_item_access(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    assert x[0] == c[0] == 0
    assert x[99] == c[99] == 99
    assert x[35] == c[35] == 35
    with pytest.raises(IndexError):
        _ = x[100]
    with pytest.raises(IndexError):
        _ = c[100]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_negative_index_access_and_assign(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    assert x[-5] == c[-5] == 95
    x[-1] = 1000
    c[-1] = 1000
    assert_oracle(x, c)
    assert x[99] == 1000


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_single_item_deletion(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    del x[35]
    del c[35]
    assert_oracle(x, c)
    assert x[35] == 36
    assert x[49] == 50
    with pytest.raises(IndexError):
        _ = x[99]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_single_item_insertion_fresh_list(paged_cls):
    """Insert on a fresh list — list semantics."""
    x, c = pair(paged_cls, range(100), 10)
    x.insert(48, "bla")
    c.insert(48, "bla")
    assert_oracle(x, c)
    assert x[48] == "bla"
    assert x[49] == 48
    assert x[50] == 49

    x.insert(48, "ble")
    c.insert(48, "ble")
    assert_oracle(x, c)
    assert x[48] == "ble"
    assert x[49] == "bla"
    assert x[50] == 48


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_single_item_insertion_after_delete_matches_list(paged_cls):
    """Delete then insert (former continuous doctest narrative)."""
    x, c = pair(paged_cls, range(100), 10)
    del x[35]
    del c[35]
    x.insert(48, "bla")
    c.insert(48, "bla")
    assert_oracle(x, c)
    assert x[48] == "bla"
    assert x[49] == 49
    assert x[50] == 50

    x.insert(48, "ble")
    c.insert(48, "ble")
    assert_oracle(x, c)
    assert x[50] == 49


# ---------------------------------------------------------------------------
# Slice get / del / set (shared oracle)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_slicing_with_negative_indices(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    assert x[-5] == c[-5]
    assert list(x[-5:]) == c[-5:]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_slicing_with_step(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    assert list(x[0:15:4]) == c[0:15:4]
    assert list(x[::-1]) == c[::-1]
    assert list(x[10:2:-1]) == c[10:2:-1]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_tail_deletions_match_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    del x[98]
    del c[98]
    assert list(x[-5:]) == c[-5:]
    del x[88]
    del c[88]
    assert list(x[-15:]) == c[-15:]
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_intra_page_slice_assignment_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    x[12:15] = range(9)
    c[12:15] = range(9)
    assert_oracle(x, c)
    assert list(x[:30]) == c[:30]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_intra_page_slice_assignment_default_pagesize_matches_list(paged_cls):
    """Default pagesize path (constructor default, not forced to 10)."""
    x, c = pair(paged_cls, range(100), pagesize=None)
    x[12:15] = range(9)
    c[12:15] = range(9)
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_expanding_slice_assignment_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    x[5:12] = range(200, 220)
    c[5:12] = range(200, 220)
    assert_oracle(x, c)
    assert list(x[:35]) == c[:35]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_chained_expanding_slice_assignments_match_list(paged_cls):
    """Grow once then again — fragile multi-chunk path."""
    x, c = pair(paged_cls, range(100), 10)
    x[12:15] = range(9)
    c[12:15] = range(9)
    assert_oracle(x, c)

    x[5:12] = range(200, 220)
    c[5:12] = range(200, 220)
    assert_oracle(x, c)
    assert list(x[:35]) == c[:35]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_del_multi_page_slice_matches_list(paged_cls):
    x, c = pair(paged_cls, range(30), 5)
    del x[3:17]
    del c[3:17]
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_set_multi_page_slice_matches_list(paged_cls):
    x, c = pair(paged_cls, range(30), 5)
    replacement = list(range(100, 110))
    x[3:12] = replacement
    c[3:12] = replacement
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_slice_grow_mid_list_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    x[5:15] = range(30)
    c[5:15] = range(30)
    assert_oracle(x, c)
    assert list(x[:42]) == c[:42]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_slice_grow_and_replace_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    x[5:35] = range(100, 160)
    c[5:35] = range(100, 160)
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_slice_shrink_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    x[5:85] = range(100, 110)
    c[5:85] = range(100, 110)
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_clear_via_slice_assign_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    x[:] = []
    c[:] = []
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_clear_via_del_slice_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    del x[:]
    del c[:]
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_extended_slice_assign_matches_list(paged_cls):
    x, c = pair(paged_cls, range(20), 5)
    values = [10, 11, 12, 13, 14]
    x[0:10:2] = values
    c[0:10:2] = values
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_extended_slice_assign_full_span_matches_list(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    values = list(range(20))
    x[0:100:5] = values
    c[0:100:5] = values
    assert_oracle(x, c)
    assert list(x[0:100:5]) == values


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_extended_slice_assign_wrong_size_raises(paged_cls):
    x = make_paged(paged_cls, range(20), 5)
    with pytest.raises(ValueError):
        x[0:10:2] = [1]


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_extended_slice_delete_matches_list(paged_cls):
    x, c = pair(paged_cls, range(20), 5)
    del x[0:10:2]
    del c[0:10:2]
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_extended_slice_delete_with_step_matches_list(paged_cls):
    x, c = pair(paged_cls, range(30), 7)
    del x[1:25:3]
    del c[1:25:3]
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_assign_slice_past_end_matches_list(paged_cls):
    x, c = pair(paged_cls, range(10), 3)
    x[8:20] = range(5)
    c[8:20] = range(5)
    assert_oracle(x, c)


# ---------------------------------------------------------------------------
# Chained mutate-after-clear (shared)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_chained_mutate_after_clear_via_slice_assign(paged_cls):
    x, c = pair(paged_cls, range(100), 10)
    x[:] = []
    c[:] = []
    assert_oracle(x, c)

    x[5:15] = range(30)
    c[5:15] = range(30)
    assert_oracle(x, c)

    x[5:35] = range(100, 160)
    c[5:35] = range(100, 160)
    assert_oracle(x, c)

    x[5:85] = range(100, 110)
    c[5:85] = range(100, 110)
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_chained_mutate_after_clear_via_del(paged_cls):
    x, c = pair(paged_cls, range(50), 10)
    del x[:]
    del c[:]
    assert_oracle(x, c)

    x.extend(range(10))
    c.extend(range(10))
    assert_oracle(x, c)

    x[2:5] = range(20, 30)
    c[2:5] = range(20, 30)
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_chained_delete_insert_slice_assign(paged_cls):
    x, c = pair(paged_cls, range(40), 5)
    del x[10:25]
    del c[10:25]
    assert_oracle(x, c)

    x.insert(5, "mid")
    c.insert(5, "mid")
    assert_oracle(x, c)

    x[3:8] = list(range(100, 115))
    c[3:8] = list(range(100, 115))
    assert_oracle(x, c)


# ---------------------------------------------------------------------------
# pop / append / extend / reverse (shared MutableSequence)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_pop_last_matches_list(paged_cls):
    x, c = pair(paged_cls, range(20), 5)
    assert x.pop() == c.pop()
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_pop_index_matches_list(paged_cls):
    x, c = pair(paged_cls, range(20), 5)
    assert x.pop(0) == c.pop(0)
    assert x.pop(7) == c.pop(7)
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_pop_empty_raises(paged_cls):
    x = make_paged(paged_cls, [])
    with pytest.raises(IndexError):
        x.pop()


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_append_and_extend_match_list(paged_cls):
    x, c = pair(paged_cls, range(10), 4)
    x.append(99)
    c.append(99)
    x.extend([1, 2, 3])
    c.extend([1, 2, 3])
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_reverse_matches_list(paged_cls):
    x, c = pair(paged_cls, range(20), 5)
    x.reverse()
    c.reverse()
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_remove_and_clear_match_list(paged_cls):
    x, c = pair(paged_cls, [1, 2, 3, 2, 4], 2)
    x.remove(2)
    c.remove(2)
    assert_oracle(x, c)
    x.clear()
    c.clear()
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_pagesize_one_matches_list(paged_cls):
    x, c = pair(paged_cls, range(15), 1)
    x.insert(7, "x")
    c.insert(7, "x")
    del x[3]
    del c[3]
    x[2:5] = [9, 8, 7, 6]
    c[2:5] = [9, 8, 7, 6]
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_boundary_insert_and_delete_match_list(paged_cls):
    """Ops exactly on chunk boundaries (multiples of pagesize)."""
    x, c = pair(paged_cls, range(30), 5)
    x.insert(10, "a")
    c.insert(10, "a")
    x.insert(5, "b")
    c.insert(5, "b")
    del x[15]
    del c[15]
    del x[0]
    del c[0]
    assert_oracle(x, c)


@pytest.mark.parametrize("paged_cls", PAGED_LIST_CLASSES)
def test_contains_index_count_match_list(paged_cls):
    x, c = pair(paged_cls, [1, 2, 2, 3, 2], 2)
    assert (2 in x) == (2 in c)
    assert x.index(3) == c.index(3)
    assert x.count(2) == c.count(2)


# ---------------------------------------------------------------------------
# SequencePagedList-only (internals / API extras)
# ---------------------------------------------------------------------------


def test_construct_emits_unfixed_bugs_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        SequencePagedList(range(3), 2)
    assert any("unfixed bugs" in str(w.message) for w in caught)


def test_default_pagesize():
    x = make_paged(SequencePagedList, range(100))
    assert x.pagesize == 1000
    assert_oracle(x, list(range(100)))


def test_pagesize_locked_after_init():
    x = make_paged(SequencePagedList, range(10), 5)
    with pytest.raises(RuntimeError, match="Pagesize"):
        x.pagesize = 3


def test_slice_access_returns_list_by_default():
    x, c = pair(SequencePagedList, range(100), 10)
    y = x[25:35]
    assert list(y) == c[25:35]
    assert y.__class__ is list
    y2 = x[0:15:4]
    assert list(y2) == c[0:15:4]


def test_slice_to_paged_false_returns_list():
    x = make_paged(SequencePagedList, range(100), 10)
    x.slice_to_paged = False
    y = x[25:35]
    assert list(y) == list(range(25, 35))
    assert y.__class__ is list


def test_slice_to_paged_same_page_returns_sequence_paged_list():
    x = make_paged(SequencePagedList, range(20), 10)
    x.slice_to_paged = True
    y = x[2:5]
    assert type(y) is SequencePagedList
    assert list(y) == [2, 3, 4]


def test_slice_to_paged_true_independent_copy_on_delete():
    x = make_paged(SequencePagedList, range(100), 10)
    x.slice_to_paged = True
    y = x[25:35]
    assert type(y) is SequencePagedList
    assert y.pagesize == 10
    del y[5]
    assert list(y) == [25, 26, 27, 28, 29, 31, 32, 33, 34]
    assert y[5] == 31
    assert y[4] == 29
    assert x[30] == 30
    assert list(x[25:35]) == list(range(25, 35))


def test_slice_to_paged_multi_page_insert_does_not_mutate_parent():
    x = make_paged(SequencePagedList, range(100), 10)
    x.slice_to_paged = True
    y = x[0:31]
    assert type(y) is SequencePagedList
    y.insert(15, "bla")
    assert y[15] == "bla"
    assert x[15] == 15
    assert list(x[:31]) == list(range(31))


def test_slice_to_paged_true_stepped_and_negative_slices():
    x = make_paged(SequencePagedList, range(100), 10)
    x.slice_to_paged = True
    y = x[0:15:4]
    assert list(y) == [0, 4, 8, 12]
    assert list(x[-5:]) == [95, 96, 97, 98, 99]


def test_page_data_sum_matches_len_after_simple_ops():
    x = make_paged(SequencePagedList, range(100), 10)
    assert page_data_len(x) == len(x)

    x.insert(50, "z")
    assert page_data_len(x) == len(x)

    del x[10:40]
    assert page_data_len(x) == len(x)


def test_clear_page_bookkeeping_shape():
    """Document SequencePagedList clear-via-assign page structure."""
    x = make_paged(SequencePagedList, range(100), 10)
    x[:] = []
    assert len(x) == 0
    assert len(x.pages) >= 1
    assert len(x.pages[0].data) == 0
