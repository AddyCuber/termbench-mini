#include <math.h>
#include <stdio.h>

int main(void) {
    volatile double horizontal = 9.0;
    volatile double vertical = 16.0;
    printf("%.1f\n", sqrt(horizontal + vertical));
    return 0;
}