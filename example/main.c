// greeting on stdout
#include <stdio.h>
#include "greeter.h"

int main() {
    puts("Hello from main.c!");
    Greeter_greet();
    fflush(stdout);
}
