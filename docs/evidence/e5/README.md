# E5 A 轨道：BuildChecker 原始复现

E5 只解释一次真实构建，不把 E4 冒烟结果当作依赖检测结论。实验必须在本组 Linux ECS 的独立克隆中运行；完整原始输出留在被忽略的 `work/<run>/`，提交报告只引用实际路径、提交 SHA 和退出码。

## 命令

```sh
python3 scripts/lab_cloud.py doctor --out work/doctor-<student-id>
python3 scripts/lab_cloud.py build --out work/build-<student-id>
python3 scripts/lab_cloud.py e5 --out work/e5-<student-id>
```

`e5` 在服务镜像内复制 `fixtures/md-rd/`，先执行 `make clean`，再以 `strace -ff -s 4096 -e trace=%file,%process` 跟踪 `make -p app`，最后运行 `./app`。`work/e5-<student-id>/evidence/` 至少保留：

- `trace/t.*`：每个进程的系统调用记录；
- `make-db.txt`：GNU Make 声明数据库；
- `build-stderr.log`、`program-output.txt`；
- 输入副本、`command.json`、退出码和容器 ID。

## 人工解释

当前样例的 `Makefile` 声明为 `main.o: main.c unused.h`，而编译 `main.c` 的子进程实际成功读取 `config.h`。应根据本次真实 trace 的 PID、父子进程关系和行号记录：

```text
实际依赖(main.o) - 声明依赖(main.o) = MD: config.h
声明依赖(main.o) - 实际依赖(main.o) = RD: unused.h
```

仅统计项目目录内成功的文件打开；系统头文件、临时文件和失败打开不构成这里的依赖结论。课程实验使用 `strace` 代替论文原型的 `ptrace`，使用已知最小样例代替论文开源项目集合，差异必须写入实验报告。

## 验收

`program-output.txt` 应为 `1`，`make-db.txt` 应出现 `main.o: main.c unused.h`，trace 应出现成功打开 `config.h` 的记录。E5 交付还需要所用代码来源、命令、工具版本、退出码和证据相对路径。
