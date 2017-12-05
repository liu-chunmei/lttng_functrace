#ifndef _EventTrace_h_
#define _EventTrace_h_
#include <string>
#include <stdlib.h>
#include <ostream>

#define FUNCTRACE() EventTrace _t1(__FILE__, __func__, __LINE__)


class EventTrace {
private:
  std::string file;
  std::string func;
  int line;

public:

  EventTrace(const char *_file, const char *_func, int line);
  ~EventTrace();
};
#endif
