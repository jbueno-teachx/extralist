Extra Sequence Types and Helpers
================================

## Testing

Requires Python 3.10+ (CPython 3.10–3.15, plus PyPy 3.10/3.11). Test orchestration
is configured with [tox](https://tox.wiki/) 4 in `pyproject.toml` (`[tool.tox]`).

```bash
pip install -e ".[dev]"          # includes tox; or: pip install "tox>=4.30"
tox                              # every env in env_list whose interpreter exists
tox run -e py314                 # one environment
tox run -e pypy311               # PyPy
tox run -e py315t                # free-threaded CPython 3.15, if installed
tox run -e lint                  # ruff (extra env, not in default env_list)
tox run -- tests/test_defaultlist.py -q   # pass args through to pytest
```

Install missing interpreters with your usual toolchain (`uv python install 3.12`,
`pyenv install`, distro packages, etc.) and ensure they are on `PATH` as
`python3.XY` / `pypy3.XY`. Missing interpreters are skipped locally
(`skip_missing_interpreters = true`).

CI runs the same tox envs on GitHub Actions (`.github/workflows/tests.yml`): one
job per interpreter via `actions/setup-python` (`allow-prereleases: true` for
3.15) and `tox run -e <env>`. An optional `[tool.tox.gh.python]` mapping is
included for [tox-gh](https://github.com/tox-dev/tox-gh) if you prefer plain
`tox run` without `-e` on Actions.


## Recipes

Runnable examples live under the top-level `recipes/` directory. They are not
installed as part of the package; run them from a checkout after installing
extralist (for example `pip install -e .`).

### Parallel workers with `chunk_sequence`

`chunk_sequence(sequence, size)` yields successive list chunks of up to `size`
items. That is a convenient way to batch a large sequence before handing work
to [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html)
pools—one future per chunk instead of one future per element.

Example script: [`recipes/parallel_chunk_workers.py`](recipes/parallel_chunk_workers.py)

```bash
pip install -e .
python recipes/parallel_chunk_workers.py
python recipes/parallel_chunk_workers.py --executor thread --size 500000 --chunk-size 25000
```

By default the recipe builds `range(1_000_000)`, splits it into chunks of
50_000 with `chunk_sequence`, and submits each chunk to a
`ProcessPoolExecutor` worker that computes per-chunk stats (count, min, max,
sum of squares). Pass `--executor thread` to use `ThreadPoolExecutor` instead;
`--max-workers`, `--size`, and `--chunk-size` control pool size and partitioning.


## PagedList

A paged mutable sequence designed
not to suffer heavy performance hits when elements must be deleted
or inserted inside a large sequence.

From an initializer sequence, the data is split into pages, each with
the given `pagesize`. By default the data type of pages is a Python list.
From then on, all insertion or deletion happens on the individual pages
and PagedList keeps track of page size changes so that it can always
retrieve the correct values for the contained sequence.

Important: "pagesize" is not an absolute page size — it is rather an
indication of desired page size. Insertions and deletions can change
individual pages to be larger or smaller than this amount.
Insertions made through slicing (`x[5:15] = range(100)`) will
respect maximum page size if the slice crosses a page boundary —
but not otherwise.

[WIP] At this point of the implementation, for a 10_000_000 sized sequence, using page_size = 10000
there is a 250-fold __gain__ (25000%) in deleting consecutive elements one by one, and a 40-fold
(36700%) performance __loss__ in random-access reading of elements on the same sequence afterwards.

[WIP] getitem slice and negative index handling implemented


## DefaultList
    A defaultdict-analogue class

## LinkedList
    Linked list implementation of a mutable sequence

## SlicedView
    Returns slices of a larger sequence as an in-place window onto the
    main sequence, instead of copies.
    (If you need that before it is done here, check the ListView implementation
     at https://github.com/lhc/lhcpython/blob/master/tree.py for now)

## Future
Planned helpers/sequence types to be featured here:



### SliceableMutableSequence
    Like collections.abc.MutableSequence but automatically handles
    slices for your `__getitem__`, `__setitem__`, `__delitem__` methods
    if they support integer indexes. (The stdlib's version requires one to
    support both integer indexes and slices for these methods). It should also
    handle negative indexes properly.

### SomeTreeishSequence
    Some tree-based sequence :-)


