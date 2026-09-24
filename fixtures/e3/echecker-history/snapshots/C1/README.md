# C1 Missing Dependency

C1 新增 `feature.h` 并让 `main.c` 使用它，但 `Makefile` 仍只声明：

```make
main.o: main.c config.h
```

因此人工 Oracle 标记：

```text
main.o -> feature.h: MISSING
```

clean build 后运行 `app.exe` 输出：`12`。
