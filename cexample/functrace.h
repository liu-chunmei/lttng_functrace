#undef TRACEPOINT_PROVIDER
#define TRACEPOINT_PROVIDER functrace

#undef TRACEPOINT_INCLUDE
#define TRACEPOINT_INCLUDE "./functrace.h"

#if !defined(_FuncTrace_h) || defined(TRACEPOINT_HEADER_MULTI_READ)
#define _FuncTrace_h_
#include <lttng/tracepoint.h>
TRACEPOINT_EVENT(functrace, func_enter,
    TP_ARGS(
        const char*, file,
        const char*, func,
        uint32_t, line),
    TP_FIELDS(
        ctf_string(file, file)
        ctf_string(func, func)
        ctf_integer(uint32_t, line, line)
    )
)

TRACEPOINT_EVENT(functrace, func_exit,
    TP_ARGS(
        const char*, file,
        const char*, func),
    TP_FIELDS(
        ctf_string(file, file)
        ctf_string(func, func)
    )
)



#endif

#include <lttng/tracepoint-event.h>

