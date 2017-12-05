
#include "EventTrace.h"

#include "functrace.h"

EventTrace::EventTrace(const char *_file, const char *_func, int _line) :
  file(_file),
  func(_func),
  line(_line)
{
  tracepoint(functrace, func_enter, file.c_str(), func.c_str(), line);
}

EventTrace::~EventTrace()
{
  tracepoint(functrace, func_exit, file.c_str(), func.c_str());
}

