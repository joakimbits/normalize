// greeting on stdout
#include <stdio.h>
#include "Greeter.h"

int main() {
    puts("Hello from main.c!");
    Greeter greeter;
    greeter.greet();
    fflush(stdout);
}