# 皮筋系统设计文档

## 一、需求摘要

1. 物体形状基本凸，皮筋无需"搭桥"
2. 物体可任意形状，皮筋绑法可任意，但皮筋平面与物体交线仍为平面曲线
3. 完全重写，无需考虑历史兼容
4. 绑爆 = 皮筋数量达标后播放爆炸动画，不需要物理建模

---

## 二、皮筋定义

```
Band = {
    plane_origin:  vec3    // 平面上一点（皮筋平面经过此点）
    plane_normal:  vec3    // 平面法向量（单位向量）
    rest_circum:   f32     // 皮筋 rest 周长 L₀
    stiffness:     f32     // 刚度系数 k ∈ [0, 1]
    influ_radius:  f32     // 影响范围 δ（沿法向的衰减半宽）
}
```

### 各字段含义

| 字段 | 物理含义 |
|------|---------|
| `plane_origin` | 皮筋在空间中的参考点，通常取截面质心的初始估计 |
| `plane_normal` | 皮筋环所在的平面方向，决定勒痕的走向 |
| `rest_circum` | 皮筋的自然周长。从超市买来就是这个长度。皮筋的趋势是让截面的当前周长回归 L₀ |
| `stiffness` | 压缩刚度。值越大，每帧修正量越大，收敛越快但可能震荡 |
| `influ_radius` | 沿法向的衰减范围。顶点距平面距离 d ≤ δ 时受影响，权重 w = smoothstep(d/δ) |

### L₀ 与旧 targetRadius 的关系（仅作参考）

对于**截面恰好是半径 R 的圆**这一退化情况：L₀ = 2πR，两者等价。
新方案不依赖这个等价关系——截面不规则时，目标半径 R 无定义，L₀ 有定义。

---

## 三、约束原理

### 3.1 核心思想

皮筋在物体上勒出一个截面。约束的目标是：**让截面的周长从当前值 P_current 收缩到皮筋的 rest 周长 L₀**。

### 3.2 收缩方向：指向截面质心

凸物体的截面质心一定在截面内部。将每个受影响顶点沿"该顶点投影点 → 截面质心"方向推进，是均匀缩小截面周长的最自然方式。

### 3.3 单根皮筋每迭代的约束步骤

```
输入: 顶点集 {P_i}, 皮筋 Band = {O, N, L₀, k, δ}

Step A — 筛选受影响顶点:
    for each 顶点 P_i:
        d_i = abs(dot(P_i - O, N))        // 顶点到皮筋平面的距离
        if d_i > δ: skip                  // 超出影响范围
        w_i = smoothstep(d_i, δ)          // 权重: 1(在平面上) → 0(在边缘)
        将 (P_i, d_i, w_i) 加入集合

Step B — 投影到皮筋平面:
    for each 受影响顶点:
        proj_i = P_i - dot(P_i - O, N) * N   // 投影点
        (d_i, w_i 沿用 Step A 的结果)

Step C — 计算加权截面质心:
    sum_w = Σ w_i
    G = Σ (w_i * proj_i) / sum_w          // 加权质心（2D 或 3D，因为投影点共面）

Step D — 计算当前有效周长（精确三角面-平面交线）:
    对所有三角面，求与皮筋平面的交线段
    收集交点 → 去重 → 按绕 G 的极角排序 → 闭合多边形
    P_current = Σ |p_j - p_{j+1}|   // 欧式距离累加

    注意：Step D 的数据源是三角面-平面精确交线，而 Step E 的位移施加
    仍使用 Step A-B 的加权投影顶点。周长计算和位移施加解耦——
    精确交线保证周长准确（无锯齿、无自交、不依赖顶点密度），
    加权顶点带保证位移平滑（权重从平面中心到边缘渐变，无硬切痕）。

Step E — 施加修正:
    if P_current > L₀:
        s = L₀ / P_current                 // 缩放因子，≤ 1
        for each 受影响顶点:
            dir_i = normalize(G - proj_i)  // 在平面内指向质心
            push_i = w_i * k * (proj_i - G) * (1 - s)  // 向质心方向的位移量
            P_i_new = P_i + push_i         // 注意：push_i 是 3D 向量，自动沿平面方向
                                           // （因为 G 和 proj_i 都在平面上）
    else:
        不做修正（皮筋松弛，可以"滑落"，当前不做处理）
```

### 3.4 关键性质

- **任意法向**：所有计算在皮筋自身平面内进行，不依赖世界坐标轴
- **向后兼容水平皮筋**：N=(0,1,0) 时自然退化为旧行为
- **质心自动偏移**：截面不对称时，质心自动偏向截面"肉多"的一侧
- **周长与位移解耦**：精确交线算周长（干净准确），加权投影顶点施加位移（平滑过渡）
- **d_i 和 w_i 的计算**：距离度量用 3D 点到平面的距离，不受截面形状影响

---

## 四、GPU 实现策略

### 4.1 为什么需要两 pass

Step D（周长排序+累加）需要全局信息（所有受影响顶点的相对角度），无法在单个 per-vertex dispatch 中完成。

方案：**角度分桶近似**，用固定数目的角桶（如 64 个）来近似多边形周长。

### 4.2 Pass 1 — 投影归桶

```
工作组分派: 每个 band 一个工作组，组内 256 线程
(如果 band 数 > 工作组数，按 band 索引分派)

组内共享内存:
    sG[2]     = vec2 质心累加器 (x, y)           // 平面局部 2D
    sW        = f32  权重累加器
    sR[N_BIN] = f32  每个角桶的半径累加器        // N_BIN = 64
    sW_bin[N_BIN] = f32 每个角桶的权重累加器

算法:
    初始化共享内存为 0
    屏障

    for vi = lid; vi < total_vertices; vi += 256:
        d = abs(dot(pos[vi] - O, N))
        if d >= δ: continue
        w = smoothstep(d / δ)
        proj = pos[vi] - d_sign * N    // 投影到平面
        // 构建局部 2D 坐标系在平面上
        // 累加权质心
        sG += w * proj_2d; sW += w

        屏障

        // 归约质心 (只有 lid=0 做)
        if lid == 0: G = sG / sW

        屏障

        // 第二次遍历（或同一轮继续）: 归桶
        for vi = lid; vi < total_vertices; vi += 256:
            (同上筛选)
            proj_rel = proj_2d - G
            angle = atan2(proj_rel.y, proj_rel.x)  // [-π, π]
            bin = floor((angle + π) / (2π) * N_BIN)
            r = length(proj_rel)
            sR[bin] += w * r; sW_bin[bin] += w

    屏障
    写回: band_output[band_idx].bins[0..63] = sR / sW_bin
           band_output[band_idx].centroid = G
           band_output[band_idx].total_weight = sW
```

### 4.3 Pass 2 — 算周长 + 施加修正

```
工作组分派: 每个 band 一个工作组，组内 64 线程（每线程一个桶）

输入: 桶半径 r[0..63], 质心 G

组内:
    每个线程负责一个桶，固定角位置 θ_bin = 2π * bin / N_BIN
    桶代表点: p_bin = G + r[bin] * (cos θ_bin, sin θ_bin)

    // 累加周长
    local_sum = |p_bin - p_{bin-1}|    // 相邻桶代表点的距离
    归约 → P_current

    if lid == 0:
        if P_current > L₀:
            s_factor = L₀ / P_current
        else:
            s_factor = 1.0  (不修正)

    屏障

    // 写回缩放因子到 band_params
    band_params[band_idx].scale_factor = s_factor

// 然后第三个 per-vertex pass 施加修正:
    对每个顶点:
        对每个 band:
            (同 Step A 筛选)
            dir = normalize(G_band - proj_2d)
            修正量 = w * k * r * (1 - s_factor) * dir
            pos += 修正量
```

### 4.4 精确周长（与 CPU 参考一致）

$P \approx 2\pi \cdot \bar{r}$ 近似对椭圆截面误差 < 5%，但对不规则截面
（凹陷、扁平、月牙形等）误差可达数倍，不可接受。

GPU 实现应使用与 3.3 节 Step D 相同的精确三角面-平面交线算法。
交线计算是 per-triangle 的、完全并行的，天然适合 GPU：

```
Pass 0 (per-triangle intersection):
    对每个三角面，计算与皮筋平面的交线段
    输出交点坐标到 append buffer

Pass 1 (per-band reduction):
    对收集的交点，按极角排序（共享内存双调排序）
    归约周长 P_current
    计算质心 G（加权，同 3.3 节 Step C）
    写回: G, s = L₀ / P_current

Pass 2 (per-vertex apply):
    同 3.3 节 Step E，使用加权投影顶点施加位移
```

---

## 五、Per-Vertex Delta（替代 1D Delta Field）

### 5.1 问题

旧的 1D delta field `delta[Y] → scale` 假设变形只依赖 Y 坐标（轴对称）。倾斜皮筋导致非轴对称变形，1D 表无法表达。

### 5.2 方案

PBD 后，每个代理顶点存一个 `r_ratio = current_radial_dist / rest_radial_dist`。高模顶点通过查最近代理顶点来获取缩放因子。

### 5.3 具体步骤

```
Step 1 — PBD 完成后 (代理网格):
    重算每个代理顶点的 r_ratio:
    
    // 注意：这里的"径向距离"是相对于皮筋截面的质心，
    // 不是相对于 Y 轴。
    // 但如果每次迭代都重新算质心，成本很高。
    // 折中：对于代理顶点，直接用局部邻居来估计"期望半径"。
    //
    // 更简单的方案：用 rest 位置和当前位置直接算变形幅度。
    // ratio_i = |cur_i - rest_i| / 某种归一化
    
    实际方案：
        对每个代理顶点 i：
            rest_i = rest 位置
            cur_i  = PBD 后的位置
            // 取 rest 位置的表面法向（预计算存储）
            n_rest = rest_normal[i]
            // 沿法向的位移量
            d_cur  = dot(cur_i - rest_i, n_rest)
            // ratio 用于后续高模缩放：> 1 表示向外膨胀，< 1 表示向内收缩
            ratio_i = clamp(1.0 + d_cur / max(|rest_i|, 0.001), 0.1, 3.0)

Step 2 — 高模顶点查 ratio:
    预计算: 对每个高模顶点，找最近代理顶点索引 (CPU 端，加载时做)

    GPU:
        for each 高模顶点 v:
            nearest_proxy = nearest_proxy_idx[v]
            ratio = ratio_buf[nearest_proxy]
            // 沿 rest 法向缩放（通用，不依赖坐标轴）
            n_rest = rest_normal_hr[v]
            new_pos = rest_pos_hr + (ratio - 1.0) * |rest_pos_hr| * n_rest
```

### 5.4 通用性

上述方案使用 rest 表面法向定义位移方向，不依赖任何世界坐标轴，
适用于任意形状的物体（旋转体、非旋转体、凹的、凸的）。

---

## 六、PBD 整体流程

```
每帧:
    if bands.length == 0:
        如果 needsRestore: 走恢复流程
        否则: 空闲

    if bands.length > 0 && !pbdConverged:
        将 rest 位置写入 pos（起始状态）
        重复 PBD_ITER 次:
            ┌──────────────────────┐
            │ Shape Pass           │  ← 不变
            │ 每顶点: cur +=       │
            │   (rest - cur) * k_s │
            └──────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │ Band Pass 1          │  ← 新
            │ per-band reduction:  │
            │   投影 → 质心 → 平均r│
            │   算 s = L₀ / P_est  │
            └──────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │ Band Pass 2          │  ← 新
            │ per-vertex apply:    │
            │   对每 band:         │
            │     推顶点向截面质心  │
            └──────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │ Volume Pass          │
            │ 梯度方向均匀壳厚位移  │
            │ dr = k·ΔV / SurfaceArea│
            └──────────┬───────────┘
                       ▼
            (最后一次迭代:)
            ┌──────────────────────┐
            │ Build Per-Vertex     │  ← 新
            │ Delta:               │
            │   ratio = r_cur /    │
            │           r_rest     │
            └──────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │ Apply Delta + Norm   │
            │ 高模 = rest × ratio  │
            │ 重算法线             │
            └──────────────────────┘
```

---

## 七、数据结构汇总

### 7.1 GPU Buffer

| Buffer | 大小 | 说明 |
|--------|------|------|
| `posA/posB` | proxy_vc × 4 × 4 B | 代理顶点位置 vec4 (双缓冲) |
| `restB` | proxy_vc × 4 × 4 B | 代理顶点 rest 位置 |
| `idxB` | proxy_tc × 3 × 4 B | 代理三角形索引 |
| `bandParamsB` | MAX_BANDS × 7 × 4 B | 每 band: O(3) + N(3) + L₀(1), 共 7 float |
| `bandStateB` | MAX_BANDS × 3 × 4 B | 每 band 运行时: G(2) + s(1) |
| `ratioB` | proxy_vc × 4 B | 每代理顶点 r_ratio |
| `nearestProxyB` | hr_vc × 4 B | 高模→代理最近邻索引 |
| `volB` | proxy_tc × 4 B | 体积累加 |
| `volTotalB` | 1 × 4 B | 总体积 |
| `deltaBuf` | (废弃，改用 ratioB) | - |
| `highResRestB` | hr_vc × 4 × 4 B | 高模 rest 位置 |
| `highResOutB` | hr_vc × 4 × 4 B | 高模输出位置 |

### 7.2 JS 端

```javascript
const bands = [];  // 每项:
// {
//   planeOrigin: [x, y, z],
//   planeNormal: [nx, ny, nz],   // 已归一化
//   restCircum:  float,           // 皮筋自然周长
//   stiffness:   float,
//   influRadius: float,
// }

const MAX_BANDS = 256;
```

### 7.3 WGSL Struct

```wgsl
struct BandParam {
    ox: f32, oy: f32, oz: f32,   // plane_origin
    nx: f32, ny: f32, nz: f32,   // plane_normal
    rest_circum: f32,             // L₀
    // padding to vec4 alignment
}

struct BandState {
    gx: f32, gy: f32,            // 截面质心 2D
    scale: f32,                   // 缩放因子 s = L₀ / P_current
}
```

---

## 八、可视化环渲染

每根皮筋渲染为两条折线环：
- **实际环**（红色实线）：三角面-平面精确交线多边形，反映当前变形后的截面轮廓
- **目标环**（绿色虚线）：实际交线多边形向 centroid 缩放至 L₀，显示皮筋的目标形状

折线由 `getExactCrossSectionPolyline` 输出的点集直接构建 `THREE.LineLoop`，
无需 torus 或实例化。256 个环 × 每环 ~200 顶点 ≈ 50K 线段 — 开销极低。

---

## 九、交互设计（放置皮筋）

### 9.1 点击放置

```
用户点击屏幕
  → 射线 cast 到物体
  → 求交点 P_hit
  → 皮筋平面经过 P_hit
  → 皮筋法向 = 用户当前视角相关（或表面法向，两步走）
```

### 9.2 两步放置（推荐）

```
Step 1: 点击确定皮筋中心点
  → 出现预览环（默认水平朝向）

Step 2: 拖拽调整倾斜
  → 预览环跟随鼠标旋转
  → 释放确定
```

或更简单：

```
点击 → 皮筋法向 = 该点的表面法向（皮筋"贴"在表面上）
      → 平面经过该点
      → 这是最直观的物理语义：皮筋垂直于表面绑
```

### 9.3 默认参数

```javascript
const DEFAULT_BAND = {
    restCircum:    2.5,      // 周长 ≈ 半径 0.4 的圆，适合菠萝
    stiffness:     0.5,
    influRadius:   0.6,
};

function addBand(origin, normal) {
    bands.push({
        planeOrigin:   [...origin],
        planeNormal:   [...normal],
        restCircum:    DEFAULT_BAND.restCircum,
        stiffness:     DEFAULT_BAND.stiffness,
        influRadius:   DEFAULT_BAND.influRadius,
    });
}

function removeBand() {
    bands.pop();
}
```

---

## 十、不变模块

以下模块**不需要修改**：

| 模块 | 原因 |
|------|------|
| `shapeCS` | per-vertex 弹簧，与皮筋方向无关 |
| `volAccCS` + `volReduceCS` + `volApCS` | 梯度方向均匀壳厚位移，对任意形状适用 |
| `normCS` + `normUnpackCS` + `posUnpackCS` | 通用法线重算和 unpack |
| 高模 Three.js 渲染管线 | 只管显示，不参与 PBD |
| 代理线框渲染 | 只管显示代理位置 |
| 模型加载 (`loadModel`, `loadModels`) | 加载逻辑不变 |
| 体积读取 (`staging.mapAsync`) | 体积监控不变 |

---

## 十一、实现顺序

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| 1 | 改 Band 数据结构（JS + WGSL） | P0 |
| 2 | 写 Band Pass 1（归约质心 + 平均 r + 缩放因子） | P0 |
| 3 | 写 Band Pass 2（per-vertex 施加修正） | P0 |
| 4 | 集成到 PBD 循环，验证水平皮筋与旧行为一致 | P0 |
| 5 | 改交互（支持法向量输入） | P1 |
| 6 | 测试倾斜皮筋 | P1 |
| 7 | Per-vertex delta（替代 1D delta field） | P1 |
| 8 | 环渲染支持旋转 | P2 |
| 9 | 移除旧 1D delta 相关代码 | P2 |

---

## 十二、与旧代码的 diff 概要

### 删除
- `bands[].centerY`, `bands[].targetRadius` (改为 `planeOrigin`, `planeNormal`, `restCircum`)
- `bandCS`（旧的半径约束着色器）
- `buildDeltaCS`（旧的 1D delta field 构建）
- `applyDeltaCS`（旧的 1D delta field 应用）
- `bandRadCS`（旧的水平环半径扫描）
- `DELTA_BUCKETS` 及相关 buffer

### 新增
- `bandReduceCS`：归约质心 + 平均半径 + 缩放因子
- `bandApplyCS`：per-vertex 施加修正
- `buildRatioCS`：per-vertex delta ratio 构建
- `applyRatioCS`：高模应用 ratio（替代 applyDeltaCS）
- `BandParam` / `BandState` WGSL struct
- `nearestProxyIdx` 预计算（CPU 端，加载时）

### 修改
- `bands[]` JS 数据结构
- `writeBandInstances` → 适配新的环渲染
- PBD 循环 dispatch 顺序
- 交互回调（支持法向量）
- Slider 绑定（`targetRadius` → `restCircum`）
