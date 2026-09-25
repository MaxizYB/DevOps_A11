#include <stdio.h>

#include "config.h"

#ifndef MODE
#define MODE 0
#endif

int main(void) {
    printf("%d\n", CONFIG_VALUE + MODE);
    return 0;
}
