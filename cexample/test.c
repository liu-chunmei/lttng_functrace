#include "eTrace.h"
#include <string.h>
#include <stdio.h>

void func3(void)
{
  f_enter(__FILE__, __func__, __LINE__); 
  f_exit(__FILE__, __func__); 
}
void func2(void)
{
  f_enter(__FILE__, __func__, __LINE__); 
  func3();
  f_exit(__FILE__, __func__); 
}

void func1(void)
{
  f_enter(__FILE__, __func__, __LINE__); 
  func2();
  f_exit(__FILE__, __func__); 
}


int main()
{
  f_enter(__FILE__, __func__, __LINE__); 
  func1();
  f_exit(__FILE__, __func__); 
  return 0;
}
