# COMSOL Lite 人类使用与输入指南

## 1. 什么时候用

适合：

- 物理模型已经基本明确，希望少来回问答地执行。
- 重复扫参、改层厚、改材料或复用同一类模型。
- 需要 `.mph`、Results、CSV 和运行报告，而不是把大量结果贴到聊天框。

不适合：

- 论文严格复现、盲测评分、正式审计：用 `final-version`。
- 物理边界、材料模型或目标量尚未确定：先澄清物理问题。
- COMSOL 版本没有对应的已验证 API cache：先做一次性能力探测。

## 2. 人类直接怎么说

不要求人类手写 JSON。推荐按下面顺序写一段短说明：

```text
COMSOL版本：
空间维度与物理场：
几何和层序：
材料参数及单位：
激励/初始条件：
边界条件：
研究类型和扫描范围：
网格要求（没有可写“自动并做收敛检查”）：
需要的结果：
保存目录和是否允许覆盖：
允许的假设：
```

关键原则：输入物理事实，不输入 COMSOL Java API 名称。缺失项如果会改变
物理意义，执行者应提问；只影响实现细节的内容可由 skill 选择保守默认值并记录。

## 3. 分层波动光学示例

```text
COMSOL 6.4，二维 EWFD。x 方向层序为空气 800 nm、
4 对 SiO2 170 nm/TiO2 60 nm、NbOCl2 500 nm、
4 对 TiO2 60 nm/SiO2 170 nm、空气 800 nm；y 宽 893 nm。
n_air=1，n_SiO2=1.46，n_TiO2=2.34，
NbOCl2 的 n=[2.5,2.15,2.15]。xmin 正入射，E=[0,1,0] V/m，
xmax 输出，上下 Floquet 周期相移为 0。波长 750:1:1100 nm。
输出 normE、R、T、R+T，保存模型、Results 和 CSV，允许覆盖测试目录。
```

对应机器输入参考：
`comsol-general-executor-lite/assets/templates/lite-layer-stack-ewfd.json`。

## 4. 一维扩散示例

```text
COMSOL 6.4，一维区间 0 到 1 m，扩散系数 1e-4 m^2/s。
初值 sin(pi*x/L)，两端 Dirichlet 为 0，时间 0:50:1000 s。
与解析解 sin(pi*x/L)*exp(-D*(pi/L)^2*t) 比较，
相对 L2 误差阈值 0.002，保存模型、曲线、CSV 和报告。
```

对应机器输入参考：
`comsol-general-executor-lite/assets/templates/lite-diffusion-1d.json`。

## 5. 命令行使用

系统需要能运行带有 `mph`、`numpy` 和 `PyYAML` 的 Python。

```powershell
python scripts/compact_task.py --task task.json --output model_manifest.json
python scripts/lite_run.py --task task.json --config runner_config.json --timeout-seconds 1800
```

运行器只在终端返回一行状态 JSON。详细 stdout/stderr、manifest、报告、
CSV 和 `.mph` 都写入 `output_dir`。

## 6. 紧凑任务的三种模板

- `layer-stack-ewfd-2d`：二维分层 EWFD、两端口、上下 Floquet 周期。
- `diffusion-1d`：一维瞬态扩散，可带解析解阈值。
- `feature-graph`：其他物理场使用通用 manifest，仍复用缓存、lint、求解和验证。

`feature-graph` 是通用后备，不代表所有物理场都已拥有短模板。新增模型通常先用
通用 manifest；只有反复出现、结构稳定的模型族才值得新增紧凑模板。

## 7. API cache 规则

缓存键是精确 COMSOL 版本，例如 `api_cache/comsol-6.4.json`，包含：

- 官方名称到 Java `api_type` 的 registry。
- 已验证的 feature/property profile。
- 验证日期、范围和文件 SHA-256。

如果版本或 profile 不存在，必须失败停止，不能猜。更新缓存前应在一次性模型中
探测 API，并用最小真实求解验证网格、DOF、结果节点、保存和重载。

## 8. Token 该怎么理解

Lite 的主要节省来自：

- 不把展开 manifest 放进对话。
- 不反复推理已经缓存的 API 属性。
- 只返回状态和路径，不回灌长日志与数组。
- 重复任务只修改紧凑 task。

单次、非常清楚、非常简单的任务，直接自然语言提问的输入 token 可能更少，因为
冷启动读取 Skill 有固定成本。Lite 的优势是总流程 token、稳定性和可复用性，
不是保证每一句用户输入都比无 Skill 更短。
