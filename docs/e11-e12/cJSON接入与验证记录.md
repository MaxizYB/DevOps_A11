# 2026-11-15：cJSON 接入与 A11 验证记录

整理：A11 组长 241880439，AI 辅助。配对：B11。原始运行目录、输入与包不纳入 Git。

## 来源核验

- B11 来源仓库 laolvfan/devops，提交 7b45b9c04686f3aefe861bb1d8a17aa63c969f23。
- B11_E11-E12_交接.zip 的 SHA256：d658d63ab2f651f5368f04dcc9a6de844b407aa8513c1b8eec36be81b87e4e02。
- B11 原始 E11-B、cJSON E12 与交接清单分别核验；课程参考客户端的 87 个下载文件核验通过，但它运行在旧课程服务上，不作为新版 cJSON 跨组验收。
- cJSON 上游 base：359567fdde253f311545a6c80b0fa6fb62e8ff09；target：cf0d87a095becada87336ed786f11070e9a037b5。bundle 的 SHA256：b83f63991d7020fd900fc7f675b9f476280d5ad96140bab64b273ce4cdcdea73。
- 仅分析 cJSON_Utils.o 缺失 cJSON.h 的声明依赖；保留原始上游 Git 历史，Dockerfile 由 harness 注入运行副本。参考修复 SHA 仅为来源说明，不是补丁生成输入，也未声称 bundle 包含它。

## 适配和边界

保留 A11 编排、路径限制、版本化报告和下载白名单；迁入 B11 cJSON 专用 scan/patch/validate，并增加保守缓存复用、实际编译参数对齐、sandbox 回滚和真实头文件重建测试。修复只追加 Makefile 依赖，不修改 cJSON C 源码。详情见 ADR 0005。

同一共享服务器串行执行四组件。客户端与任务 API 之间是 HTTP；服务器内部通过函数及带 SHA256 的报告衔接，不需要人工转发 MD 或补丁。新版客户端还检查部署实现指纹、阶段 commit/config/job/trace、本轮 repair 的输入哈希及最终 accepted/no-MISSING。

## 已通过的服务器直接运行

- 云端独立目录：/root/241880439/DevOps_A11-e12-cjson-20261115。
- 源码：1e47db076dcd16fe0c6fb0cbb9892d2824724544；实现指纹 dd0d81c2e44ea829a18a7502470ce576ded6e1db7724ce7ce29e18b9e62762a8；实现相对提交无修改。
- 输出：work/cjson-integration-20261115/e12-03。
- job_id：job-2f056948f478458c88fe1ffb79db12b9。
- trace_id：trace-ea04230a312e4c8fb775e1c32ea0e452。
- configuration_id：cfg-e11e12-bc70f4e9e436d256。
- 五阶段 SUCCEEDED，清单 89 个产物；发现 cJSON_Utils.o → cJSON.h 的 MISSING，修复后 findings=[]。
- repair 消费的本轮增量报告 SHA256：be111944e291a467324148fc8ad1523af065a4a03a6b28583411d668a41426da。
- accepted=true；patch_applies、build、test、header_change、no_missing 五项均通过。
- 本次 base→target 的头文件/预处理变化使缓存保守刷新 cJSON_Utils.o，reused=[]；与同 target 全量对照一致。函数体复用由独立新增测试验证，不把本轮刷新伪写成复用。

环境可见内存仍约 3.54 GiB，低于手册 4 GiB；按组长先前确认串行运行并保留说明。未降低验证门槛。

## 失败与重试

e12-01 是 Docker Hub 元数据连接失败，原始结果/日志保留。e12-02-console.log 是数据集名称准备错误后未找到请求；随后修复名称变量覆盖问题，新增回归测试，不修改旧输入。最终另建 cjson-a11 数据集：Python 使用可达且固定摘要的镜像源，Debian 使用记录的 HTTPS 镜像源；候选原始构建/运行指令保留。

    python3 scripts/e11e12/prepare_cjson.py --bundle /root/241880439/cjson-20261115.bundle --dataset-name cjson-a11 --python-image m.daocloud.io/docker.io/library/python:3.13-slim@sha256:f82c96458eedc847b233e582eb31336f4954b39cae020b6dcf5b3ed0e5cbcd74 --debian-mirror https://mirrors.tuna.tsinghua.edu.cn
    python3 run_e11e12.py run --request data/cjson-a11-request.json --out work/cjson-integration-20261115/e12-03

已存在的不同内容输入和 work 目录拒绝覆盖，重试使用新名字。

本地最终单元测试 61 项通过（含 cJSON 适配、数据集名称/重试输入保护、交接包白名单/哈希及现有三人测试）；E2、E11/E12 契约与 git diff --check 通过。早期云端的 54 项测试与源码 1e47db0 对应；新增交接/准备测试另随最后代码版本复核，不能把次数混算。

## API、交接及交付状态

共享 API 切换与跨机器组长自验结果将在完成后追加；B11 新版独立 cJSON API 结果仍待对方实际运行回传，不能使用组长自验代替。

给 B11 的新版 ZIP 不含密码，不包含旧私密交接包；继续通过原 b11-e12 账号转发。包内有部署元数据、请求、数据清单、客户端、Dockerfile 和回执模板，并自带逐文件哈希。

操作全景和提交物归属见 联调全景与提交材料.md；B11 操作见 B11-cJSON正式联调.md。最终 E11/E12 课程包应在收到新版 B11 结果与必要个人材料、完成真实协作追溯后重新整理，当前不标成全部验收通过。

## 选题口径

组长已选择第三方 cJSON 历史缺陷复现，原因是本组没有长期维护的 C/Make 应用。这不证明符合手册“本组实际维护”这一独立要求，不冒充本组原创维护或教师批准；交付时如实记录该选题例外，不阻止技术联调准备。
