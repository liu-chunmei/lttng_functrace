#include "EventTrace.h"

void func3()
{
  FUNCTRACE();
}
void func2()
{
  FUNCTRACE();
  func3();
}

void func1()
{
  FUNCTRACE();
  func2();
}


int main()
{
  FUNCTRACE(); 
  func1();
  return 0;
}
