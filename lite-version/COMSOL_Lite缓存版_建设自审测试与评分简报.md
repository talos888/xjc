# COMSOL Lite 缓存版建设、自审、测试与评分简报

日期：2026-06-12

## 一、目标与定位

本版本是独立的 `comsol-general-executor-lite`，未安装到本机正式
`C:\Users\xjc14\.codex\skills`。它保留 Final 版成熟 runner 的核心验证，
新增短入口、紧凑任务、精确版本 API cache 和一行状态输出。

Lite 面向物理规格已经明确的执行与复用；Final 继续负责论文复现、严格 A/B、
盲测评分和完整审计。Lite 不是靠删除数值验证来省 token。

## 二、主要实现

1. `SKILL.md` 缩短为 1,994 B，只规定关键边界和执行顺序。
2. `comsol-lite-task-v1` 支持 `layer-stack-ewfd-2d`、`diffusion-1d` 和
   通用 `feature-graph`。
3. `api_cache/comsol-6.4.json` 缓存已验证 registry、EWFD profile、
   验证范围与日期；运行时记录 SHA-256。
4. cache 按 manifest 的 `comsol_version` 选择；缺版本或缺 profile 时闭锁失败。
5. `lite_run.py` 将 lint、COMSOL stdout/stderr 和 supervisor 详情写入文件，
   终端只输出一行 JSON。
6. 输出目录限制在 `workspace_root` 下，禁止绝对路径和 `..` 逃逸。

## 三、代码自审

发现并修复：

- 旧 lint 仍导入静态 `PROFILES`，与版本化缓存冲突。
- registry 最初固定为 COMSOL 6.4，已改为由 manifest 版本动态选择。
- profile 合并后残留内部 `comsol_version`，已在提交 COMSOL API 前移除。
- 权限失败最初会输出 traceback，已扩展异常边界并增加故障注入测试。
- 光子晶体总长度测试误写为 4,440 nm，按层序复算后修正为 3,940 nm。
- `output_dir` 最初未限制路径逃逸，已增加相对路径验证。

未发现阻断发布的代码问题。已知边界：当前只有 COMSOL 6.4 缓存；短模板只覆盖
两个稳定模型族，其他模型走 `feature-graph`，不能声称所有物理场均已短模板化。

## 四、测试结果

静态与单元测试：

- Skill Creator `quick_validate`：通过。
- Python AST 语法检查：通过。
- 32 个单元测试：全部通过。
- 两个紧凑模板编译并通过完整 manifest lint。
- cache miss、未知 profile、路径逃逸、单行失败输出：均通过故障注入。

真实 COMSOL 6.4：

- 一维扩散：通过；100 个网格单元，203×21 解规模，21 个时间点；
  相对 L2 误差 `2.16948e-5 < 0.002`；保存和重载通过；最终回归 23.04 s。
- 二维 EWFD 缺陷腔：通过；3,746 个网格单元，26,569×351 解规模；
  R/T 各 351 点；`R+T` 范围
  `[0.9999999999998982, 1.0000000000000508]`；
  `normE` 有 6,431,022 个有限值；Results、表格、数值节点、保存和重载通过；
  161.94 s。

## 五、Token/输入压缩

这是文件字节数对比，不伪装成具体模型的计费 token；实际 token 随 tokenizer
和语言变化，但同为 ASCII JSON 时比例可作为稳定代理。

| 案例 | 紧凑 task | 展开 manifest | task/manifest |
|---|---:|---:|---:|
| 二维 EWFD 腔 | 1,442 B | 26,335 B | 5.48% |
| 一维扩散 | 656 B | 4,357 B | 15.06% |

把 1,994 B 的 `SKILL.md` 冷启动成本也计入：

- 腔：`Skill + task` 为 3,436 B，对比 `Skill + manifest` 28,329 B，减少 87.87%。
- 扩散：2,650 B 对比 6,351 B，减少 58.27%。

这不等于 Lite 必然比“只发一句自然语言”省输入 token。单次简单任务直接问可能
更短；Lite 的收益主要在避免 API 重推理、展开 manifest、错误往返和长结果回灌，
并在复用态只修改 task。

## 六、自评分

评分口径在测试前固定为：功能完成 25、正确性 25、Token 效率 15、迁移性 15、
失败安全 10、文档与复现 10。

| 维度 | 得分 | 依据 |
|---|---:|---|
| 功能完成 | 24.5/25 | 编译、lint、监督运行、结果、保存/重载闭环完成 |
| 正确性 | 24.25/25 | 两个真实物理任务通过，腔能量守恒近机器精度 |
| Token 效率 | 14.4/15 | 两任务输入压缩明显；冷启动并非总优于直接提问 |
| 迁移性 | 13.2/15 | 通用 feature graph 可迁移，但短模板和 cache 尚非全版本覆盖 |
| 失败安全 | 9.7/10 | cache/profile/path 闭锁及 timeout supervisor；未穷举所有 COMSOL 异常 |
| 文档与复现 | 9.6/10 | 模板、README、人类输入指南、报告和路径齐全 |
| **总分** | **95.65/100** | 不因两次成功运行虚报“全 COMSOL 适用” |

## 七、结论

Lite 达到发布条件：低上下文入口、版本化 API cache、真实求解验证和最小输出均
有效。它相对无 Skill 的核心优势是可重复、少 API 猜测、少调试回合和可审计文件
结果；纯单次输入 token 不保证占优。后续新增 cache 应由新 COMSOL 版本的真实
探测驱动，新增 helper/template 应由重复出现的模型族驱动，而不是每换一个模型
就增加专用代码。
