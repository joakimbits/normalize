// C interface for greeter.cpp
#include <cstdlib>

#include "greeter.h"
#include "greeter.hpp"

#ifndef __MMSEMBEDDED_CPP_
#define __MMSEMBEDDED_CPP_
#include <stdlib.h>
void* operator new(size_t size) { return malloc(size); }
void operator delete(void* ptr) { free(ptr); }
#endif

#ifdef __cplusplus
    extern "C" {
#endif

void Greeter_greet() {
    Greeter *greeter = new Greeter();
    greeter->greet();
    delete greeter;
}

#ifdef __cplusplus
}
#endif