# Unity 叉车模型导入和设置指南

## 📋 前置条件

- ✅ Unity 2022.3.20f1 LTS 已安装
- ✅ Unity 项目已创建 (`/Volumes/aigo S7 Med/ForkliftCLI/unity/`)
- ✅ 已完成 SolidWorks 导出，获得 `forklift_main.fbx`

---

## 🎯 目标架构

### Unity 场景结构
```
ThreeDViewer.unity Scene
├── Main Camera
├── Directional Light
├── Forklift_Root (空对象，Transform = 0,0,0)
│   ├── Body_Chassis (车身底盘，静态)
│   ├── Mast_Assembly (门架总成)
│   │   ├── Mast_Outer (外门架，静态)
│   │   ├── Mast_Inner (内门架，可升降)
│   │   └── Mast_Tilt_Pivot (倾斜枢轴，可旋转)
│   ├── Fork_Assembly (货叉总成)
│   │   ├── Carriage_Fork (货叉架，随内门架升降)
│   │   ├── Fork_Left (左货叉，可滑动)
│   │   └── Fork_Right (右货叉，可滑动)
│   ├── Counterweight (配重，静态)
│   └── Cabin (驾驶室，静态)
└── EventSystem
```

---

## 📝 Step 1: 导入 FBX 模型

### 1.1 复制文件到 Unity 项目
```bash
# 复制 FBX 文件
cp "/path/to/forklift_main.fbx" \
   "/Volumes/aigo S7 Med/ForkliftCLI/unity/Assets/StreamingAssets/models/"

# 复制纹理文件夹 (如果有)
cp -r "/path/to/forklift_main.fbm" \
   "/Volumes/aigo S7 Med/ForkliftCLI/unity/Assets/StreamingAssets/models/"
```

### 1.2 Unity 中导入
1. **打开 Unity 项目**
2. **Project 面板** → 导航到 `Assets/StreamingAssets/models/`
3. **拖拽** `forklift_main.fbx` 到 Project 面板
4. **等待导入完成** (进度条消失)

---

## ⚙️ Step 2: 配置 FBX 导入设置

### 2.1 基础设置
选中 `forklift_main.fbx`，在 Inspector 中设置:

**Tab: Model**
```
Scale Factor: 0.001 (mm → m)
Convert Units: ✅
```

**Tab: Rig**
```
Animation Type: Generic
Avatar Definition: Create from this model
```

**Tab: Animation**
```
Import Animation: ✅
Bake Animation: ✅
Resample Curves: ✅
```

**Tab: Materials**
```
Material Creation Mode: Standard
Material Naming: By Base Texture Name
Material Search: Local
```

**点击 "Apply" 应用设置**

---

## 🔧 Step 3: 创建 Prefab 和场景层级

### 3.1 创建 Prefab
1. **Project 面板** → 右键 → `Create → Prefab`
2. **命名为**: `Forklift_Prefab`
3. **双击打开 Prefab** (进入 Prefab 编辑模式)

### 3.2 构建层级结构
1. **从 Project 面板拖拽** `forklift_main.fbx` 到 Hierarchy
2. **展开层级**，检查部件是否正确分离
3. **重新组织层级** (如果需要):

```csharp
// 在 Hierarchy 中创建空对象作为根节点
GameObject → Create Empty
重命名为 "Forklift_Root"
Transform Position: (0, 0, 0)

// 将所有 FBX 子对象拖拽到 Forklift_Root 下
// 按功能分组创建空对象
```

### 3.3 验证部件命名
确保关键部件名称与代码中的名称一致:

| Unity 对象名 | 对应功能 | 脚本引用 |
|-------------|----------|----------|
| `Forklift_Root` | 根节点 | 整体控制 |
| `Mast_Inner` | 内门架 | 升降动画 |
| `Mast_Outer` | 外门架 | 倾斜枢轴 |
| `Carriage_Fork` | 货叉架 | 随升降 |
| `Fork_Left` | 左货叉 | 滑动动画 |
| `Fork_Right` | 右货叉 | 滑动动画 |

---

## 🎬 Step 4: 设置机械动画

### 4.1 门架升降动画

**方法 A: 使用 Animator (推荐)**

1. **创建 Animator Controller**:
   ```
   Project 面板 → 右键 → Create → Animator Controller
   命名为 "Forklift_Animator"
   ```

2. **设置动画参数**:
   - 双击打开 Animator 窗口
   - Parameters → + → Float
   - 命名为 `MastHeight` (范围: 0-1)

3. **创建动画片段**:
   ```
   Project 面板 → 右键 → Create → Animation
   命名为 "Mast_Lift"
   ```

4. **录制关键帧**:
   - 选择 `Mast_Inner` 对象
   - Animation 窗口 → 点击录制 (红点)
   - 时间 0:00 → 设置 Y Position = 1.8m (低位)
   - 时间 3:00 → 设置 Y Position = 4.5m (高位)
   - 停止录制

5. **连接动画**:
   - Animator 窗口 → 拖拽 `Mast_Lift` 到状态机
   - 设置默认状态为 `Mast_Lift`
   - 在 `Mast_Lift` 状态上 → Add Parameter → `MastHeight`

**方法 B: 代码控制 (更灵活)**

创建脚本 `MastController.cs`:
```csharp
using UnityEngine;

public class MastController : MonoBehaviour
{
    [Header("References")]
    public Transform mastInner;      // 内门架
    public Transform carriageFork;   // 货叉架

    [Header("Config")]
    public float minHeight = 1.8f;   // 米
    public float maxHeight = 4.5f;   // 米
    public float liftSpeed = 1.0f;   // 米/秒

    private float currentHeight = 1.8f;

    public void SetHeight(float heightMeters)
    {
        currentHeight = Mathf.Clamp(heightMeters, minHeight, maxHeight);
        float t = (currentHeight - minHeight) / (maxHeight - minHeight);

        // 内门架上升
        if (mastInner != null)
        {
            mastInner.localPosition = new Vector3(
                mastInner.localPosition.x,
                currentHeight,
                mastInner.localPosition.z
            );
        }

        // 货叉架跟随
        if (carriageFork != null)
        {
            carriageFork.localPosition = new Vector3(
                carriageFork.localPosition.x,
                currentHeight + 0.5f, // 货叉架在门架上方 0.5m
                carriageFork.localPosition.z
            );
        }
    }

    public void MastUp() => SetHeight(currentHeight + 0.3f);
    public void MastDown() => SetHeight(currentHeight - 0.3f);

    public float GetCurrentHeight() => currentHeight;
}
```

### 4.2 门架倾斜动画

创建脚本 `TiltController.cs`:
```csharp
using UnityEngine;

public class TiltController : MonoBehaviour
{
    [Header("References")]
    public Transform mastAssembly;   // 门架总成

    [Header("Config")]
    public float maxTiltForward = 6f;    // 度 (前倾)
    public float maxTiltBackward = 12f;  // 度 (后倾)
    public float tiltSpeed = 30f;        // 度/秒

    private float currentTilt = 0f;

    public void SetTiltAngle(float angle)
    {
        currentTilt = Mathf.Clamp(angle, -maxTiltBackward, maxTiltForward);
        if (mastAssembly != null)
        {
            mastAssembly.localRotation = Quaternion.Euler(currentTilt, 0, 0);
        }
    }

    public void TiltForward() => SetTiltAngle(currentTilt + 3f);
    public void TiltBackward() => SetTiltAngle(currentTilt - 3f);

    public float GetCurrentTilt() => currentTilt;
}
```

### 4.3 货叉滑动动画

创建脚本 `ForkController.cs`:
```csharp
using UnityEngine;

public class ForkController : MonoBehaviour
{
    [Header("References")]
    public Transform forkLeft;
    public Transform forkRight;

    [Header("Config")]
    public float minSpread = 0.3f;    // 米 (最小间距)
    public float maxSpread = 1.2f;    // 米 (最大间距)
    public float slideSpeed = 0.5f;   // 米/秒

    private float currentSpread = 0.6f;

    public void SetSpread(float spreadMeters)
    {
        currentSpread = Mathf.Clamp(spreadMeters, minSpread, maxSpread);
        float halfSpread = currentSpread / 2f;

        if (forkLeft != null)
        {
            forkLeft.localPosition = new Vector3(-halfSpread, forkLeft.localPosition.y, forkLeft.localPosition.z);
        }
        if (forkRight != null)
        {
            forkRight.localPosition = new Vector3(halfSpread, forkRight.localPosition.y, forkRight.localPosition.z);
        }
    }

    public void SpreadOut() => SetSpread(currentSpread + 0.1f);
    public void SpreadIn() => SetSpread(currentSpread - 0.1f);
}
```

---

## 🎮 Step 5: 创建主控制脚本

创建 `ForkliftController.cs` (整合所有控制):
```csharp
using UnityEngine;
using System.Collections.Generic;

public class ForkliftController : MonoBehaviour
{
    [Header("Components")]
    public MastController mastController;
    public TiltController tiltController;
    public ForkController forkController;

    [Header("Part References")]
    public List<GameObject> interactiveParts = new List<GameObject>();

    [Header("Config")]
    public bool enableKeyboardControl = true;

    void Update()
    {
        if (enableKeyboardControl)
        {
            HandleKeyboardInput();
        }
    }

    void HandleKeyboardInput()
    {
        // 门架升降 (W/S)
        if (Input.GetKey(KeyCode.W))
            mastController.MastUp();
        if (Input.GetKey(KeyCode.S))
            mastController.MastDown();

        // 门架倾斜 (A/D)
        if (Input.GetKey(KeyCode.A))
            tiltController.TiltBackward();
        if (Input.GetKey(KeyCode.D))
            tiltController.TiltForward();

        // 货叉开合 (Q/E)
        if (Input.GetKey(KeyCode.Q))
            forkController.SpreadIn();
        if (Input.GetKey(KeyCode.E))
            forkController.SpreadOut();
    }

    // Flutter 调用的接口
    public void SetMastHeight(float heightMeters)
    {
        mastController?.SetHeight(heightMeters);
    }

    public void SetTiltAngle(float angle)
    {
        tiltController?.SetTiltAngle(angle);
    }

    public void SetForkSpread(float spreadMeters)
    {
        forkController?.SetSpread(spreadMeters);
    }

    public void HighlightPart(int partId, Color color)
    {
        if (partId >= 0 && partId < interactiveParts.Count)
        {
            var renderer = interactiveParts[partId].GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = color;
            }
        }
    }

    public void ClearHighlight()
    {
        foreach (var part in interactiveParts)
        {
            var renderer = part.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = Color.white;
            }
        }
    }
}
```

---

## 🔧 Step 6: 场景搭建

### 6.1 创建 ThreeDViewer.unity 场景

1. **File → New Scene** → 选择 "Basic (URP)"
2. **保存为**: `Assets/Scenes/ThreeDViewer.unity`

### 6.2 设置场景内容

**Main Camera 设置**:
```
Position: (0, 3, -8)
Rotation: (15, 0, 0)
Camera Controller Script: 添加 CameraController.cs
```

**Directional Light 设置**:
```
Position: (0, 10, -10)
Rotation: (50, -30, 0)
Intensity: 1.0
Shadow Type: Soft Shadows
```

**添加叉车模型**:
```
1. 从 Project 拖拽 Forklift_Prefab 到 Scene
2. Position: (0, 0, 0)
3. Rotation: (0, 0, 0)
4. Scale: (1, 1, 1)
```

**添加控制脚本**:
```
选中 Forklift_Root → Add Component → ForkliftController
拖拽对应的子对象到脚本引用字段
```

---

## 🎨 Step 7: 材质和Shader设置

### 7.1 创建高亮Shader

创建 `Assets/Shaders/PartHighlight.shader`:
```shader
Shader "Custom/PartHighlight"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _HighlightColor ("Highlight Color", Color) = (1, 1, 0, 1)
        _HighlightIntensity ("Highlight Intensity", Range(0, 2)) = 0.5
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 100

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                UNITY_FOG_COORDS(1)
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float4 _HighlightColor;
            float _HighlightIntensity;

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                UNITY_TRANSFER_FOG(o,o.vertex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);
                col.rgb += _HighlightColor.rgb * _HighlightIntensity;
                UNITY_APPLY_FOG(i.fogCoord, col);
                return col;
            }
            ENDCG
        }
    }
}
```

### 7.2 创建透明Shader

创建 `Assets/Shaders/XRayTransparent.shader`:
```shader
Shader "Custom/XRayTransparent"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Transparency ("Transparency", Range(0, 1)) = 0.5
        _TintColor ("Tint Color", Color) = (1, 1, 1, 0.5)
    }

    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        LOD 100

        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag

            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float _Transparency;
            float4 _TintColor;

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);
                col.a = _Transparency;
                col.rgb *= _TintColor.rgb;
                return col;
            }
            ENDCG
        }
    }
}
```

### 7.3 应用材质

1. **创建材质**:
   ```
   Project 面板 → 右键 → Create → Material
   命名为 "Forklift_Body"
   Shader: Standard
   ```

2. **设置材质属性**:
   ```
   Albedo: 白色
   Metallic: 0.8
   Smoothness: 0.6
   ```

3. **应用到模型**:
   ```
   选中对应部件 → Inspector → Material Element 0 → 拖入材质
   ```

---

## 🧪 Step 8: 测试和调试

### 8.1 功能测试清单

**基础功能**:
- [ ] 模型在 Scene 中正常显示
- [ ] 可以旋转和缩放查看模型
- [ ] 材质和纹理显示正确

**控制功能**:
- [ ] 键盘 W/S 控制门架升降
- [ ] 键盘 A/D 控制门架倾斜
- [ ] 键盘 Q/E 控制货叉开合

**交互功能**:
- [ ] 点击部件可以高亮显示
- [ ] 高亮颜色正确
- [ ] 可以清除高亮

### 8.2 性能测试

**使用 Unity Profiler**:
1. `Window → Analysis → Profiler`
2. 点击 "Play" 运行场景
3. 观察:
   - FPS 应该 > 30
   - Draw Calls 应该 < 100
   - Triangles 应该 < 100k

**如果性能不达标**:
- 降低模型面数
- 减少实时阴影
- 使用 LOD (Level of Detail)
- 优化材质

---

## 📱 Step 9: Flutter 集成准备

### 9.1 确认部件ID映射

创建 `PartMapping.cs`:
```csharp
using UnityEngine;
using System.Collections.Generic;

public class PartMapping : MonoBehaviour
{
    public static readonly Dictionary<int, string> PartNames = new Dictionary<int, string>
    {
        {1, "Body_Chassis"},
        {2, "Mast_Outer"},
        {3, "Mast_Inner"},
        {4, "Carriage_Fork"},
        {5, "Fork_Left"},
        {6, "Fork_Right"},
        {7, "Counterweight"},
        {8, "Cabin"}
    };

    public static GameObject FindPartById(int partId, Transform root)
    {
        if (PartNames.ContainsKey(partId))
        {
            string partName = PartNames[partId];
            return FindChildRecursive(root, partName);
        }
        return null;
    }

    private static GameObject FindChildRecursive(Transform parent, string name)
    {
        foreach (Transform child in parent)
        {
            if (child.name == name)
                return child.gameObject;

            var result = FindChildRecursive(child, name);
            if (result != null)
                return result;
        }
        return null;
    }
}
```

### 9.2 准备AR配置

确保模型尺寸与真实叉车一致:
```csharp
public class ForkliftDimensions : MonoBehaviour
{
    public float realLength = 3.45f;    // 米
    public float realWidth = 1.2f;      // 米
    public float realHeight = 2.1f;     // 米
    public float realMastHeight = 4.5f; // 米
    public float realWheelbase = 1.65f; // 米
    public float realTurningRadius = 2.5f; // 米

    // AR 中使用这些数值进行 1:1 渲染
}
```

---

## ✅ 验证检查清单

### Unity 项目设置
- [ ] FBX 文件成功导入
- [ ] 层级结构正确
- [ ] 所有脚本编译无错误
- [ ] 材质和纹理显示正常

### 功能测试
- [ ] 门架升降动画正常
- [ ] 门架倾斜动画正常
- [ ] 货叉滑动动画正常
- [ ] 零件高亮功能正常

### 性能优化
- [ ] FPS > 30
- [ ] 三角面数 < 100k
- [ ] Draw Calls < 100

### Flutter 集成准备
- [ ] 部件ID映射正确
- [ ] 控制接口已实现
- [ ] 事件回调已设置

---

## 🚀 下一步

完成 Unity 设置后:
1. **构建 Unity 工程** (用于 Flutter 集成)
2. **测试 Flutter-Unity 通信**
3. **实现 AR 场景**
4. **性能优化和bug修复**

参考: `UNITY_INTEGRATION_PLAN.md` 中的 Step 5-6
