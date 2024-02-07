#include <stdio.h>
#include <ctype.h>
#include <string.h>

int rovarsprak(void)
{
    const char consontants[] = "bcdfghjklmnpqrstvwxz";
    char c;

    while ((c = tolower(getchar()))) {
        switch (c) {
            case EOF:
            case '!':
                return 0;
        }

        for (int i = 0; i < strlen(consontants); i++)
            if (c == consontants[i])
                printf("%co", c);

        putchar(c);
    }

    return 1;
}

int main(int argc, char **argv)
{
    return rovarsprak();
}
