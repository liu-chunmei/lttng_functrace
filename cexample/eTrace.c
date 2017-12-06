#include "functrace.h"

void f_enter(const char *file, const char *func, int line)
{
  tracepoint(functrace, func_enter, file, func, line);
}


void f_exit(const char *file, const char *func, int line)
{
  tracepoint(functrace, func_exit, file, func);
}

