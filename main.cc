#include "EventTrace.h"
int main()
{
  int count = 100;
  while (count--){
    FUNCTRACE();
  }
  return 0;
}
