#ifndef _eTrace_h_
#define _eTrace_h_
#include <string.h>

void f_enter(const char *file, const char *func, int line);
void f_exit(const char *file, const char *func);

#endif
