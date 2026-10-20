CC = gcc
CFLAGS = -Wall -Wextra

all: distance

distance: distance.o
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f distance distance.o