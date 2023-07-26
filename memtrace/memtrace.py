"""memtrace: Trace and measure the memory a Python session takes."""
import builtins
import inspect
import gc
import warnings

from pympler.asizeof import asizeof


from collections import namedtuple
from functools import wraps


MemLog = namedtuple("MemLog", "ID memory")


class IncorrectUseOfMEMLOGSError(Exception):
    """MEMLOGS was used incorrectly."""


class MemLogsList:
    """A container for keeping memory logs.

    It's designed as a singleton class in a way that only a MEMPOINT()
    function can change it.
    
    >>> MEMLOGS[0].ID
    'memtrace import'
    >>> MEMLOGS[0] = "Wrong!"
    Traceback (most recent call last):
        ...
    IncorrectUseOfMEMLOGSError: MEMLOGS does not accept item assignment
    >>> MEMLOGS[0]
    MemLog(ID='memtrace import', memory=...)
    >>> MEMLOGS[20:25]
    []
    >>> MEMLOGS.append("Wrong!")
    Traceback (most recent call last):
        ...
    IncorrectUseOfMEMLOGSError: MEMLOGS can be updated only using the MEMPOINT() function
    
    >>> current_len = len(MEMLOGS)
    >>> for _ in range(10): MEMPOINT()
    >>> len(MEMLOGS) - current_len
    10
    >>> del MEMLOGS
    Traceback (most recent call last):
        ...
    NameError: name 'MEMLOGS' is not defined
    """

    _instance = None

    def __new__(cls, data, *args, **kwargs):
        """Singleton class."""
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, data):
        self.data = data
        self.provided_IDs = []

    @property
    def IDs(self):
        return [ID for ID, _ in self.data]

    @property
    def memories(self):
        return [memory for _, memory in self.data]

    def filter(self, predicate):
        """Get a list of MemLog elements satisfying the condition from predicate."""
        return [memlog for memlog in self.data if predicate(memlog)]

    def map(self, func):
        return [func(memlog) for memlog in self.data]

    def append(self, memlog):
        if inspect.stack()[1][3] == "MEMPOINT":
            if memlog.ID in self.provided_IDs:
                ID_new = (
                    f"{memlog.ID}-{self.provided_IDs.count(memlog.ID) + 1}"
                )
            else:
                ID_new = memlog.ID
            self.provided_IDs.append(memlog.ID)
            self.data.append(MemLog(ID_new, memlog.memory))
        else:
            raise IncorrectUseOfMEMLOGSError(
                "MEMLOGS can be updated only using the MEMPOINT() function"
            )

    def __setitem__(self, *args, **kwargs):
        raise IncorrectUseOfMEMLOGSError(
            "MEMLOGS does not accept item assignment"
        )

    def __repr__(self):
        return repr(self.data)

    def __getitem__(self, i):
        """Get item(s) of MEMLOGS.add()

        Warning: When i is a slice, a list is returned, not an instance of
        MemLogsList.
        """
        if isinstance(i, slice):
            return [MemLog(*it) for it in self.data[i]]
        else:
            return MemLog(*self.data[i])

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for ID, memory in self.data:
            yield MemLog(ID, memory)


builtins.__dict__["MEMLOGS"] = MemLogsList([])


def MEMPOINT(ID=None):
    """Global function to measure full memory and log it into MEMLOGS.

    The function is available from any module of a session. It logs into
    MEMLOGS, also available from any module.

    Memory is collected using pympler.asizeof.asizeof(), and reported in
    bytes. So, the function measures the size of all current gc objects,
    including module, global and stack frame objects, minus the size
    of `MEMLOGS`.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        MEMLOGS.append(  # type: ignore
            MemLog(
                str(ID), (asizeof(all=True)) # type: ignore
            )
        )


def MEMORY():
    """Global function to measure full memory.

    The function is available from any module of a session. It returns
    the memory in bytes, calculated using pympler.asizeof.asizeof(). So,
    the function measures the size of all current gc objects, including
    module, global and stack frame objects, minus the size of `MEMLOGS`.
    
    >>> len(MEMLOGS)
    1
    >>> mem = MEMORY()
    >>> type(mem)
    <class 'int'>
    >>> len(MEMLOGS)
    1
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return asizeof(all=True) # type: ignore


def MEMTRACE(func, ID_before=None, ID_after=None):
    """Decorator to log memory before and after running a function."""

    @wraps(func)
    def inner(*args, **kwargs):
        before = ID_before if ID_before else f"Before {func.__name__}()"
        MEMPOINT(before)
        f = func(*args, **kwargs)
        after = ID_after if ID_after else f"After {func.__name__}()"
        MEMPOINT(after)
        return f

    return inner


def MEMPRINT():
    """Pretty-print MEMLOGS in MB.
    
    >>> MEMPOINT()
    >>> MEMPOINT("Testing point")
    >>> MEMPOINT()
    >>> MEMPOINT("Testing point")
    >>> MEMPRINT()
    0   ... MB     → memtrace import
    1   ... MB      → None
    2   ... MB      → Testing point
    3   ... MB      → None-2
    4   ... MB      → Testing point-2
    """
    for i, memlog in enumerate(MEMLOGS):  # type: ignore
        ID = memlog.ID if memlog.ID else ""
        print(
            f"{i: < 4} "
            f"{str(round(memlog.memory / 1024/1024, 2)) + ' MB': <11} → "
            f"{ID}"
        )


builtins.__dict__["MEMPOINT"] = MEMPOINT
builtins.__dict__["MEMORY"] = MEMORY
builtins.__dict__["MEMPRINT"] = MEMPRINT
builtins.__dict__["MEMTRACE"] = MEMTRACE


gc.collect()
MEMPOINT("memtrace import")


if __name__ == "__main__":
    import doctest

    flags = flags = (
        doctest.ELLIPSIS
        | doctest.NORMALIZE_WHITESPACE
        | doctest.IGNORE_EXCEPTION_DETAIL
    )
    doctest.testmod(optionflags=flags)
