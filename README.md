# e `tracemem`: Memory tracker for Python sessions

`tracemem` enables you to check the full memory used by a Python session. It also offers simple tools to keep the memory used by the session in subsequent moments, which is why we can say `tracemem` lets you track full memory used by a Python session.

`tracemem` is a very lightweight package for profiling memory use. It's a very simple wrapper around `pympler.asizeof.asizeof()`. `tracemem`'s only purpose is to measure memory usage by a Python session, so you cannot, for instance, measure a memory used by a particular function or object. For this, you can use other tools, such as

* [`pympler`](https://pypi.org/project/Pympler/)
* [`memory_profiler`](https://pypi.org/project/memory-profiler/)
* [`perftester`](https://pypi.org/project/perftester/)

and others.

## Usage

Since this is a profiling tool, `tracemem` code is typically *not* used by applications; instead, it's added only for profiling purposes. Hence, to make using the tool easier, it's objects are available as `builtins` global variables, that is, as variables obtained from any module used in the session. Hence, you do not have to import them in every module in which you're using the tools. So, to use this functionality, it's enough to import `tracemem `in any of the modules of your application; after this import, all `tracemem` functions and objects are available inside the Python session, hence, in any module of your application.

Here's a list of all `tracemem` functions:

* `MEMPOINT()`, which creates a memory point in your session (see below)
* `MEMORY()`, which prints the memory usage, without creating a memory point
* `MEMPRINT()`, which prints `MEMLOGS` (see below)
* `tracemem()`, a decorator function that creates a memory point before and after calling the decorated method

In addition, `tracemem` offers one more object:

* `MEMLOGS`, an object of a  `MemLogsList` class, a list-like container that keeps all memory points created during a session

To use `tracemem`, you only need to import it:

```python-repl
>>> import tracemem

```

### `MEMPOINT()`: Creating memory points

The main function is `MEMPOINT()`, which creates a memory point — a measurement point of the memory used by a Python session — and adds it to `MEMLOGS`, a list-like container of memory points.

> **A memory point**: A measurement point of the memory used by a Python session.

The first memory point is when `tracemem` is imported. We can see this by checking the `MEMLOGS` object, which can be accessed from the `builtins` global space:

```python-repl
>>> MEMLOGS
[MemLog(ID='tracemem import', memory=...)]
>>> MEMPOINT()
>>> len(MEMLOGS)
2
>>> MEMPOINT("The second MEMPOINT")
>>> len(MEMLOGS)
3
>>> MEMLOGS
[MemLog(ID='tracemem import', memory=...),
 MemLog(ID='None', memory=...),
 MemLog(ID='The second MEMPOINT', memory=...)]

```

(The measured memory usage is not included in the doctests, as they would fail.)

A memory point creates a point with an ID, which by default is `None`; `MEMPOINT()` adds such a memory point `MEMLOGS`. When you create two points with the same ID, say "my id", the second time it will be replaced with "my id-2", and so on. Note that while you can use any object as an ID, its string representation will be used instead:

```python-repl
>>> MEMPOINT()
>>> MEMLOGS[-1].ID
'None-2'

```

In addition to IDs, memory points contain their essence: the memory used by the current session, in bytes. Let's see what happens when we add a big list to the scope and then remove it:

```python-repl
>>> li = [i for i in range(10_000_000)]
>>> MEMPOINT("After adding a list with 10 mln elements")
>>> del li
>>> MEMPOINT("After removing this list")
>>> MEMLOGS[-2].memory / MEMLOGS[-1].memory > 100
True

```

This basically means that adding so big a list to the scope makes the session use over a hundred times more memory.

### `MEMLOGS`: A container of memory points

`MEMLOGS` is actually not a list but an object of a `tracemem.MemLogsList` class:

```python-repl
>>> type(MEMLOGS).__name__
'MemLogsList'

```

This class inherits from `collections.UserList`, but it works in quite a different way than a regular list. First of all, it's a singleton class, so `MEMLOGS` is its only instance. The only method to update it is to use the `MEMPOINT()` function. You cannot append anything to it, and item assignment does not work for it, either; neither do multiplication and adding.

Note that `MEMLOGS` elements are instances of a `MemLog` named tuple (`collections.namedtuple`, to be precise). So, you can access its two items as if it were a regular tuple, or using the names of its two attributes, `ID` and `memory`:

```python-repl
>>> MEMPOINT("Just checking")
>>> m = MEMLOGS[-1]
>>> type(m).__name__
'MemLog'
>>> m.ID
'Just checking'
>>> m[0]
'Just checking'
>>> type(m.memory).__name__
'int'
>>> type(m[1]).__name__
'int'

```

You can use several additional methods and properties of the `MEMLOGS` object:

* `.memories`, a property that returns all the memories reported until the moment
* `IDs`, like above but for IDs
* `.filter()`, a method for filtering `MEMLOGS`
* `.map()`, a method for applying a function to all elements of `MEMLOGS`

Let's see how this works:

```python-repl
>>> type(MEMLOGS.memories), len(MEMLOGS.memories)
(<class 'list'>, 7)
>>> MEMLOGS.IDs
['tracemem import',
 'None',
 'The second MEMPOINT',
 'None-2',
 'After adding a list with 10 mln elements',
 'After removing this list',
 'Just checking']

```

The `.filter()` methods accepts one argument, that is, a predicate to be used for filtering, just like you'd use with the built-in `filter()` function. For the `.filter()` method, however, you need to create a predicate working with `MemLog` elements. Unlike the built-in `filter()` function, it does not create a generator but a list. This is because `MEMLOGS` is not expected to be a large object.

```python-repl
>>> def memory_over(memlog: tracemem.MemLog) -> bool:
...     return memlog.memory > 3_750_000
>>> MEMLOGS.filter(memory_over)
[MemLog(ID='After adding a list with 10 mln elements', memory=...)]

```

We can of course use a `lambda` function instead:

```python-repl
>>> MEMLOGS.filter(lambda m: m.memory > 3_750_000)
[MemLog(ID='After adding a list with 10 mln elements', memory=...)]
>>> MEMLOGS.filter(lambda m: m.memory < 1_000_000)
[]
>>> MEMLOGS.filter(lambda m: "after" in m.ID.lower() or "before" in m.ID.lower())
[MemLog(ID='After adding a list with 10 mln elements', memory=...),
 MemLog(ID='After removing this list', memory=...)]

```

And here's the `.map()` method in action. Like the `.filter()` method, it returns a list:

```python-repl
>>> as_MB = MEMLOGS.map(lambda m: m.memory / 1024 / 1024)
>>> all(m < 500 for m in as_MB)
True
>>> MEMLOGS.map(lambda m: m.ID.lower())
['tracemem import',
 'none',
 'the second mempoint',
 'none-2',
 'after adding a list with 10 mln elements',
 'after removing this list',
 'just checking']
>>> memlogs = MEMLOGS.map(lambda m: (m.ID.lower(), round(m.memory / 1024 / 1024)))
>>> memlogs[:2]
[('tracemem import', ...), ('none', ...)]

```

## `MEMPRINT()`: Printing `MEMLOGS`

To print `MEMLOGS`, you can use a dedicated function `MEMPRINT()`, which converts memories to MB and pretty-prints the memory points collected in `MEMLOGS`:

```python-repl
>>> MEMPRINT()
 0   ...    → tracemem import
 1   ...    → None
 2   ...    → The second MEMPOINT
 3   ...    → None-2
 4   ...    → After adding a list with 10 mln elements
 5   ...    → After removing this list
 6   ...    → Just checking

```

## `@MEMTRACE`: Creating memory points by decorating a function

If you want to log the full-memory usage of a particular function, you can use the `@MEMTRACE` decorator. It creates two memory points: right before and right after calling the function. Just like the other `tracemem` tools, you do not need to import the decorator:

```python-repl
>>> @MEMTRACE
... def create_huge_list(n):
...     return [i for i in range(n)]
>>> li = create_huge_list(10_000_000)
>>> del li
>>> MEMPOINT()
>>> MEMLOGS[-3:]
[MemLog(ID='Before create_huge_list()', memory=...),
 MemLog(ID='After create_huge_list()', memory=...),
 MemLog(ID='None-3', memory=...)]
>>> MEMLOGS[-2].memory > 100 * MEMLOGS[-1].memory
True

```

## `MEMORY()`: Printing current memory usage without creating a memory point

Above, we've seen the most common use of `tracemem`'s full-memory tracer. There's one additional function, `MEMORY()`, which returns the current full memory of the session:

```python-repl
>>> mem = MEMORY()
>>> type(mem)
<class 'int'>

```

The function does not create a memory point, so it does not log the memory usage to `MEMLOGS`:

```python-repl
>>> len(MEMLOGS)
10
>>> _ = MEMORY()
>>> len(MEMLOGS)
10
>>> MEMPOINT("Just once more")
>>> len(MEMLOGS)
11
>>> _ = MEMORY()
>>> len(MEMLOGS)
11

```

## Why the `builtins` global scope?

Since this feature of `tracemem` is to be used to debug memory use from various modules, it'd be inconvinient to import the required objects in all these modules. That's why the required objects are kept in the global scope — but this can change in future versions.

## Unit testing

The package is covered with documentation tests and unit tests, located in this README and in the main module, [tracemem.py](tracemem.py). To run them, you need to use three `doctest` flags: `doctest.ELLIPSIS`, `doctest.NORMALIZE_WHITESPACE` and `doctest.IGNORE_EXCEPTION_DETAIL`. To run the tests under Linux, it's enough to use the `run_tests.sh` shell script, which contains only two commands:

```bash
(venv-tracemem) $ python -m doctest README.md -o ELLIPSIS -o NORMALIZE_WHITESPACE -o IGNORE_EXCEPTION_DETAIL
(venv-tracemem) $ python tracemem/tracemem.py

```

Remember to run the script or these two commands in the virtual environment, here called `venv-tracemem`. In Windows, the commands would be exactly the same, so you can simply copy theme and paste into your shell.

For the moment, `doctest` is the only testing framework used in `tracemem`, but if it occurrs to be insufficient, `pytest`would be implemented.

## Operating systems

The package is developed in Linux (actually, under WSL) and checked in Windows 10, so it works in both these environments.

## Contribution

Any contribution will be welcome. You can submit an issue in the [repository](https://github.com/nyggus/perftester). You can also create your own pull requests.
