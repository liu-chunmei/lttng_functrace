gcc -c -std=c99 -fpic -I. functrace.c 
g++ -c -std=c++0x -fpic -I. EventTrace.cc
g++ -shared -Wl,--no-as-needed -o eventtrace.so -llttng-ust functrace.o EventTrace.o
g++ -c -std=c++0x -I. main.cc
sudo cp eventtrace.so /usr/lib/libeventtrace.so
gcc -o app main.o -leventtrace -llttng-ust
#LD_PRELOAD=libeventtrace.so ./app
