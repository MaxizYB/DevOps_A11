CC = gcc
CFLAGS = -O0 -DMODE=7
TARGET := app.exe
OBJECTS := main.o
RM ?= rm -f

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^

main.o: main.c config.h
	$(CC) $(CFLAGS) -c main.c -o main.o

clean:
	-$(RM) $(TARGET) $(OBJECTS)

.PHONY: all clean
