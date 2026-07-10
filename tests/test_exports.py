"""Package surface: __all__ and main public names from implementation modules."""

import importlib
import inspect

import extralist
from extralist import (
    DefaultList,
    DoubleLinkedList,
    PagedList,
    SequencePagedList,
    SliceableSequenceMixin,
    SlicedView,
    StructSequence,
    TreePagedList,
    chunk_sequence,
)

# Prefer importlib so submodule objects are not confused with same-named exports.
defaultlist = importlib.import_module("extralist.defaultlist")
linked = importlib.import_module("extralist.linked")
sequencepagedlist = importlib.import_module("extralist.sequencepagedlist")
treepagedlist = importlib.import_module("extralist.treepagedlist")
slicedview = importlib.import_module("extralist.slicedview")
structsequence = importlib.import_module("extralist.structsequence")
sliceable_module = importlib.import_module("extralist.sliceable")
version_module = importlib.import_module("extralist.version")


# Main public classes defined in package modules and re-exported at package root.
MODULE_PUBLIC_NAMES = {
    defaultlist: ("DefaultList",),
    linked: ("DoubleLinkedList",),
    sequencepagedlist: ("SequencePagedList",),
    treepagedlist: ("TreePagedList",),
    slicedview: ("SlicedView",),
    structsequence: ("StructSequence",),
    sliceable_module: ("SliceableSequenceMixin",),
}

# Non-class callables re-exported at package root.
MODULE_PUBLIC_FUNCTIONS = {
    sequencepagedlist: ("chunk_sequence",),
}


def test_all_is_defined_and_unique():
    assert hasattr(extralist, "__all__")
    assert len(extralist.__all__) == len(set(extralist.__all__))


def test_all_names_are_importable_attributes():
    for name in extralist.__all__:
        assert hasattr(extralist, name), f"{name!r} listed in __all__ but missing on package"
        assert name in vars(extralist), f"{name!r} not present in package namespace"


def test_star_import_names_match_all():
    exported = {
        "DefaultList": DefaultList,
        "DoubleLinkedList": DoubleLinkedList,
        "SequencePagedList": SequencePagedList,
        "TreePagedList": TreePagedList,
        "PagedList": PagedList,
        "SlicedView": SlicedView,
        "StructSequence": StructSequence,
        "SliceableSequenceMixin": SliceableSequenceMixin,
        "chunk_sequence": chunk_sequence,
        "__version__": extralist.__version__,
    }
    assert set(exported) == set(extralist.__all__)
    for name, obj in exported.items():
        assert getattr(extralist, name) is obj or getattr(extralist, name) == obj


def test_pagedlist_alias_is_sequence_paged_list():
    assert PagedList is SequencePagedList
    assert extralist.PagedList is extralist.SequencePagedList


def test_version_matches_version_module():
    assert extralist.__version__ == version_module.__version__
    assert isinstance(extralist.__version__, str)
    assert "__version__" in extralist.__all__


def test_module_main_classes_are_in_all_and_reexported():
    for module, names in MODULE_PUBLIC_NAMES.items():
        for name in names:
            assert name in extralist.__all__, (
                f"{module.__name__}.{name} should be listed in extralist.__all__"
            )
            assert getattr(extralist, name) is getattr(module, name)


def test_module_public_functions_are_in_all_and_reexported():
    for module, names in MODULE_PUBLIC_FUNCTIONS.items():
        for name in names:
            assert name in extralist.__all__
            assert getattr(extralist, name) is getattr(module, name)
            assert callable(getattr(extralist, name))


def test_sliceable_decorator_not_exported_at_package_root():
    """Deferred: improve sliceable later; do not advertise the decorator at package root."""
    assert "sliceable" not in extralist.__all__
    # Without a root binding, attribute access resolves to the submodule (no name shadow).
    assert inspect.ismodule(extralist.sliceable)
    assert extralist.sliceable is sliceable_module
    assert callable(sliceable_module.sliceable)


def test_exported_types_are_classes_or_expected_callables():
    class_names = {
        "DefaultList",
        "DoubleLinkedList",
        "SequencePagedList",
        "TreePagedList",
        "PagedList",
        "SlicedView",
        "StructSequence",
        "SliceableSequenceMixin",
    }
    for name in class_names:
        assert inspect.isclass(getattr(extralist, name))
    assert callable(extralist.chunk_sequence)
