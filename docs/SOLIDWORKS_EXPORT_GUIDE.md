# SolidWorks 叉车模型导出指南

## 📋 STEP 文件分析结果

**文件**: `Forklift.STEP`
- **Schema**: STEP AP214 (SolidWorks 2015)
- **总实体**: 418,994 个
- **装配关系**: 2 个 ✅ (包含层级结构！)
- **实体部件**: 156 个 BREP (有多个独立部件)
- **产品定义**: 3 个

**关键发现**: STEP 文件包含完整的装配结构，可以保留部件层级！

---

## 🎯 导出目标

### 保留的部件层级 (建议结构)
```
Forklift_Assembly (根装配)
├── Body_Chassis (车身底盘)
├── Mast_Outer (外门架)
├── Mast_Inner (内门架)
├── Carriage (货叉架)
├── Fork_Left (左货叉)
├── Fork_Right (右货叉)
├── Counterweight (配重)
├── Cabin_Operator (操作室)
├── Wheels_Front (前轮组)
├── Wheels_Rear (后轮组)
├── Hydraulics (液压系统)
└── Engine_Compartment (发动机舱)
```

---

## 📝 SolidWorks 导出步骤

### Step 1: 打开 STEP 文件

1. **启动 SolidWorks 2015+**
2. **File → Open** → 选择 `Forklift.STEP`
3. **导入选项设置**:
   ```
   ✅ Import as assembly
   ✅ Import multiple bodies as parts
   ❌ Do not heal faces (保留原始几何)
   ❌ Do not knit surfaces
   ```

### Step 2: 检查装配结构

1. **打开 FeatureManager 设计树**
2. **检查部件层级**:
   - 展开 `Forklift Assem1` (或类似名称)
   - 确认是否看到子部件/零件
3. **如果结构混乱**:
   - 右键 → `Edit Assembly`
   - 使用 `Insert Components` 重新组织

### Step 3: 命名和组织部件

**重要**: 统一命名规范，便于 Unity 识别

| SolidWorks 名称 | Unity 用途 | 说明 |
|----------------|-----------|------|
| `Body_Chassis` | 静态基础 | 车身底盘，不移动 |
| `Mast_Outer` | 门架外层 | 固定在车身上 |
| `Mast_Inner` | 门架内层 | 可升降 |
| `Carriage_Fork` | 货叉架 | 随内门架升降 |
| `Fork_Left` | 左货叉 | 可在货叉架上移动 |
| `Fork_Right` | 右货叉 | 可在货叉架上移动 |
| `Mast_Tilt_Cylinder` | 倾斜液压缸 | 控制门架倾斜 |
| `Counterweight` | 配重 | 静态 |
| `Cabin` | 驾驶室 | 静态 |

### Step 4: 创建装配关系和约束

#### 门架升降约束
```
1. 选择 Mast_Inner → 右键 → Edit Component
2. Insert → Mate → 选择:
   - Mast_Inner 内表面 和 Mast_Outer 外表面
   - 关系类型: Width Mate (宽度配合) 或 Concentric (同心)
   - 勾选 "Lock rotation" (锁定旋转)
```

#### 门架倾斜约束
```
1. 选择 Mast_Outer → 右键 → Edit Component
2. Insert → Mate → 选择:
   - Mast_Older 底部枢轴点
   - Body_Chassis 对应枢轴点
   - 关系类型: Hinge (铰链)
   - 限制角度: -12° ~ +6° (后倾 ~ 前倾)
```

#### 货叉移动约束
```
1. 选择 Fork_Left → 右键 → Edit Component
2. Insert → Mate → 选择:
   - Fork_Left 底部和 Carriage_Fork 导轨
   - 关系类型: Slider (滑块)
   - 限制距离: 0 ~ 1200mm
```

### Step 5: 设置动画关键帧 (可选)

**方法 A: 使用 SolidWorks Motion**
1. **Tools → Add-ins → SolidWorks Motion**
2. **创建马达**:
   - 插入马达到 Mast_Inner
   - 类型: Linear Motor (线性马达)
   - 速度: 300mm/s
3. **设置运动范围**:
   - Motion Study → 设置时间轴
   - 0-5秒: 门架从 1.8m 升到 4.5m

**方法 B: 手动创建配置 (推荐)**
1. **Configuration Manager → Add Configuration**
2. **创建配置**:
   - `Mast_Low` (门架低位 1.8m)
   - `Mast_High` (门架高位 4.5m)
   - `Tilt_Backward` (后倾 -12°)
   - `Tilt_Forward` (前倾 +6°)
3. **在不同配置下拖动部件到目标位置**

### Step 6: 导出为 FBX

1. **File → Save As**
2. **文件类型**: `FBX (*.fbx)`
3. **导出选项**:
   ```
   ✅ Export as assembly
   ✅ Preserve hierarchy (保留层级)
   ✅ Export configuration: [选择所有配置]
   ✅ Include materials
   ✅ Include textures
   ⚙️ Units: Millimeters (毫米)
   ⚙️ Up Axis: Y-up
   ⚙️ Forward Axis: Z-forward
   ```
4. **高级设置**:
   ```
   ✅ Embed media (嵌入纹理)
   ✅ Binary format (二进制格式，文件更小)
   ❌ Do not export hidden components
   ⚙️ Scale factor: 0.001 (mm → m)
   ```

### Step 7: 验证导出结果

**检查清单**:
- [ ] FBX 文件大小 < 50MB
- [ ] 在 Windows 3D Viewer 中打开正常
- [ ] 层级结构保留完整
- [ ] 材质和纹理显示正确
- [ ] 如果有动画，可以播放

---

## 🔧 Blender 替代方案 (无 SolidWorks 时)

### 方案 A: 直接处理 STEP → FBX

1. **安装 Blender** (3.6+)
2. **安装 STEP 导入插件**:
   ```
   Edit → Preferences → Add-ons
   搜索 "STEP" → 启用 "Import-Export STEP format"
   ```

3. **导入 STEP**:
   ```
   File → Import → STEP
   选择 Forklift.STEP
   ```

4. **清理和优化**:
   ```
   # 查看导入的层级
   Outliner → 确认是否有子对象

   # 如果是单网格，手动分离:
   Edit Mode → 选择面 → P → Separate by Selection
   为每个部件命名 (Body_Chassis, Mast_Inner 等)
   ```

5. **设置原点**:
   ```
   选择每个部件 → Object → Set Origin → Origin to Geometry
   确保 Y 轴向上
   ```

6. **导出 FBX**:
   ```
   File → Export → FBX
   ✓ Include: Selected Objects
   ✓ Transform: Apply Transform
   ✓ Scale: 0.001 (mm → m)
   ✓ Forward: -Z Forward
   ✓ Up: Y Up
   ✓ Path Mode: Copy (复制纹理)
   ```

### 方案 B: 优化现有 GLB 并重组

如果 STEP 导出困难，可以用 Blender 优化现有 GLB:

1. **导入 GLB**:
   ```
   File → Import → glTF 2.0 (.glb/.gltf)
   选择 001.glb
   ```

2. **网格减面**:
   ```
   选中模型 → Modifiers → Add Modifier → Decimate
   Ratio: 0.05 (保留5%面数，从143万 → 7万)
   Apply
   ```

3. **手动分离部件**:
   ```
   Edit Mode → 选择车身面 → P → Separate
   重命名为 "Body_Chassis"
   重复操作分离门架、货叉等
   ```

4. **创建层级**:
   ```
   创建空对象 "Forklift_Root"
   将所有部件设为其子对象
   设置正确的父子关系
   ```

5. **导出优化后的 FBX**:
   ```
   File → Export → FBX
   同上述导出设置
   ```

---

## 📦 导出后的文件准备

### 文件结构
```
/Volumes/aigo S7 Med/ForkliftCLI/unity/Assets/StreamingAssets/models/
├── forklift_main.fbx              # 主 FBX 文件
├── forklift_main.fbm/             # 纹理文件夹 (自动生成)
│   ├── body_diffuse.png
│   ├── body_metallic.png
│   └── body_normal.png
└── metadata.json                  # 模型元数据 (手动创建)
```

### 元数据模板 (metadata.json)
```json
{
  "name": "Toyota 8FG30 叉车",
  "manufacturer": "Toyota",
  "model_year": "2020",
  "format": "fbx",
  "scale_unit": "meters",
  "source_file": "Forklift.STEP",
  "export_date": "2026-09-08",

  "parts": [
    {
      "mesh_name": "Body_Chassis",
      "part_id": 1,
      "name": "车身底盘",
      "group": "body",
      "is_interactive": false,
      "is_static": true
    },
    {
      "mesh_name": "Mast_Outer",
      "part_id": 2,
      "name": "外门架",
      "group": "mast",
      "is_interactive": false,
      "is_static": true
    },
    {
      "mesh_name": "Mast_Inner",
      "part_id": 3,
      "name": "内门架",
      "group": "mast",
      "is_interactive": true,
      "animation_type": "lift",
      "min_value": 1800,
      "max_value": 4500,
      "unit": "mm"
    },
    {
      "mesh_name": "Carriage_Fork",
      "part_id": 4,
      "name": "货叉架",
      "group": "fork",
      "is_interactive": true,
      "parent_part": 3,
      "animation_type": "lift_child"
    },
    {
      "mesh_name": "Fork_Left",
      "part_id": 5,
      "name": "左货叉",
      "group": "fork",
      "is_interactive": true,
      "parent_part": 4,
      "animation_type": "slide"
    },
    {
      "mesh_name": "Fork_Right",
      "part_id": 6,
      "name": "右货叉",
      "group": "fork",
      "is_interactive": true,
      "parent_part": 4,
      "animation_type": "slide"
    }
  ],

  "animations": [
    {
      "name": "mast_lift",
      "display_name": "门架升降",
      "type": "linear",
      "duration_ms": 3000,
      "loop": false,
      "affected_parts": [3, 4, 5, 6],
      "control_method": "slider"
    },
    {
      "name": "mast_tilt",
      "display_name": "门架倾斜",
      "type": "rotation",
      "axis": "x",
      "min_angle": -12,
      "max_angle": 6,
      "duration_ms": 2000,
      "affected_parts": [2, 3, 4, 5, 6],
      "control_method": "buttons"
    }
  ],

  "ar_config": {
    "real_length_mm": 3450,
    "real_width_mm": 1200,
    "real_height_mm": 2100,
    "real_mast_height_mm": 4500,
    "real_wheelbase_mm": 1650,
    "real_turning_radius_mm": 2500,
    "real_weight_kg": 3800,
    "real_load_capacity_kg": 3000
  },

  "physics": {
    "center_of_mass": [0, 1.0, 0],
    "mass_kg": 3800
  }
}
```

---

## ✅ 验证检查清单

### SolidWorks 导出验证
- [ ] FBX 文件可以在 Unity 中导入
- [ ] 层级结构完整显示在 Hierarchy 面板
- [ ] 所有部件都有正确的命名
- [ ] 材质和纹理正确显示
- [ ] 文件大小合理 (< 50MB)
- [ ] 三角面数在合理范围 (5-10万)

### Unity 导入验证
- [ ] 拖入 FBX 到 Unity Project 面板
- [ ] 检查 Inspector 中的 Import Settings
- [ ] Scale Factor 设置为 0.001 (mm → m)
- [ ] 勾选 "Import Materials" 和 "Import Textures"
- [ ] 点击 "Apply" 后没有错误

### 功能验证
- [ ] 可以在 Scene 视图中旋转和缩放模型
- [ ] 可以单独选中每个部件
- [ ] 部件的 Transform 坐标正确
- [ ] 如果有动画，可以在 Animation 窗口播放

---

## 🚨 常见问题

### Q: STEP 导入后所有部件合并成一个？
**A**: 检查导入选项，确保 "Import as assembly" 已勾选。如果还是有问题，尝试在 SolidWorks 中重新保存 STEP 文件时选择 "Save assembly as STEP"。

### Q: FBX 导入 Unity 后材质丢失？
**A**:
1. 确保导出时勾选 "Include materials"
2. 检查纹理文件是否在 `.fbm` 文件夹中
3. 在 Unity 中选中 FBX，Inspector → Materials → Material Creation Mode 选择 "Standard"

### Q: 模型太大/太小？
**A**: 在 Unity 的 FBX Import Settings 中调整 Scale Factor:
- 如果太大: 减小 Scale Factor (如 0.001 → 0.0001)
- 如果太小: 增大 Scale Factor (如 0.001 → 0.01)

### Q: 动画在 Unity 中无法播放？
**A**:
1. 确认 SolidWorks 导出时选择了配置
2. 在 Unity FBX Import Settings 中勾选 "Import Animations"
3. Animation Type 选择 "Generic" 或 "Humanoid"
4. 检查 Animation 窗口是否有动画片段

---

## 📞 技术支持

如遇到问题，提供以下信息:
1. SolidWorks 版本
2. 导出时的错误截图
3. FBX 文件大小
4. Unity Console 错误日志

---

**下一步**: 导出完成后，将 FBX 文件放入 Unity 项目，然后参考 `UNITY_IMPORT_GUIDE.md` 进行 Unity 中的设置。
