# C2 Compile Command Change

C2 的源码保持 C1 不变，只把 `CFLAGS` 从 `-O0` 改为：

```make
CFLAGS = -O0 -DMODE=7
```

预期行为：

- 从 C1 产物直接进入 C2 后运行普通增量构建，`main.o` 不会因为命令变化自动重编译，`app.exe` 仍输出 `12`。
- `mingw32-make -n -B main.o` 可观察到强制重建命令变为 `gcc -O0 -DMODE=7 -c main.c -o main.o`。
- clean build 后运行 `app.exe` 输出 `19`。
- `feature.h` 仍未写入 `main.o` 的声明依赖，MD Oracle 保持存在。
