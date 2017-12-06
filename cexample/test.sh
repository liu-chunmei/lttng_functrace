gcc -c -std=c99 -fpic -I. functrace.c
gcc -c -std=c99 -fpic -I. eTrace.c
gcc -shared -Wl,--no-as-needed -o etrace.so -llttng-ust functrace.o eTrace.o
gcc -c -std=c99 -I. test.c
sudo cp etrace.so /usr/lib/libetrace.so
gcc -o test test.o -letrace -llttng-ust

