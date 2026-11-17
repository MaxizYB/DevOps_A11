#include "policy.h"

/* A11 addition: accept exactly A followed by two decimal digits. */
int a11_group_is_valid(const char *group) {
    return group && group[0] == 'A'
        && group[1] >= '0' && group[1] <= '9'
        && group[2] >= '0' && group[2] <= '9'
        && group[3] == '\0';
}

int helper(void) {
    return a11_group_is_valid(A11_GROUP) ? 0 : -1;
}
