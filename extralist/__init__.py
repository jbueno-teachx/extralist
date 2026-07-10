# coding: utf-8
from .defaultlist import DefaultList
from .linked import DoubleLinkedList
from .sequencepagedlist import SequencePagedList, chunk_sequence
from .treepagedlist import TreePagedList
from .sliceable import SliceableSequenceMixin
from .slicedview import SlicedView
from .structsequence import StructSequence
from .version import __version__

# Backward-compatible alias for the sequence-backed paged list.
PagedList = SequencePagedList

__author__ = "João S. O. Bueno"
__license__ = "LGPL v3.0+"

__all__ = [
    "DefaultList",
    "DoubleLinkedList",
    "SequencePagedList",
    "TreePagedList",
    "PagedList",
    "SlicedView",
    "StructSequence",
    "SliceableSequenceMixin",
    "chunk_sequence",
    "__version__",
]
