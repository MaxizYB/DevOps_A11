app: main.o
	$(CC) main.o -o app

main.o: main.c unused.h
	$(CC) -c main.c -o main.o

.PHONY: clean
clean:
	rm -f app main.o
