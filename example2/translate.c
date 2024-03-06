#include <stdio.h>
#include <ctype.h>
#include <string.h>

// Rövarspråket - a simple spoken langugage obfuscator https://en.wikipedia.org/wiki/R%C3%B6varspr%C3%A5ket
// Everything up to a first exclamation mark (!) gets translated into Rövarspråket
int rovarsprak(void)
{
    for (char c; (c = getchar());) {
        switch (c)
            case EOF:
            case '!':
                return 0;

        char lowercase_c = tolower(c);
        for (const char *consontant = "bcdfghjklmnpqrstvwxz"; *consontant; consontant++)
            if (lowercase_c == *consontant)
                printf("%co", c);

        putchar(c);
    }

    return 1;
}

int main(int argc, char **argv)
{
    return rovarsprak();
}
