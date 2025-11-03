from tracemem import tracemem
from tracemem.tracemem import (
    MemLog,
    MemLogsList,
    MB,
    MEMORY,
    MEMPOINT,
    MEMPRINT,
    MEMTRACE,
    signif,
    IncorrectUseOfMEMLOGSError,
)

# Make MEMLOGS available at module level too (same singleton instance as in builtins)
MEMLOGS = __builtins__["MEMLOGS"]  # type: ignore
