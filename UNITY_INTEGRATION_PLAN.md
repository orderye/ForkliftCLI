# ForkliftCLI — Unity + AR Foundation 集成方案

**目标：** 用 Unity 替代 model_viewer_plus，实现 3D 机械动画、零件交互、AR 真实尺寸、AR 维修指导  
**前置条件：** Phase 1 完成（Flutter 壳 + FastAPI 后端已就绪）  
**预计工期：** 4 周（与 Phase 2 并行）  
**最后更新：** 2026-09-08

---

## 一、架构总览

```
┌──────────────────────────────────────────────────────┐
│                   Flutter 主壳                        │
│                                                      │
│  首页 │ 车型库 │ OCR │ AI维修 │ 我的叉车 │ 个人中心    │
│                         │                            │
│              ┌──────────┴──────────┐                  │
│              │  Platform Channel   │                  │
│              │  (MethodChannel)    │                  │
│              └──────────┬──────────┘                  │
│                         ↓                            │
│  ┌─────────────────────────────────────────────┐     │
│  │              Unity Player                    │     │
│  │                                             │     │
│  │  Scene 1: 3D Viewer                         │     │
│  │  - 模型加载/旋转/缩放                        │     │
│  │  - 机械动画（门架/货叉/倾斜/转向）            │     │
│  │  - 零件高亮/透明/拆解                        │     │
│  │  - 爆炸图                                   │     │
│  │                                             │     │
│  │  Scene 2: AR View                           │     │
│  │  - AR Foundation 平面检测                    │     │
│  │  - 1:1 真实尺寸放置                          │     │
│  │  - 门架高度实时叠加                          │     │
│  │  - 转弯半径圈线                              │     │
│  │  - V3: AR 维修指导                           │     │
│  └─────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘
```

---

## 二、技术选型

| 组件 | 方案 | 说明 |
|------|------|------|
| Unity 版本 | **Unity 2022 LTS** | 稳定长期支持 |
| AR 框架 | **AR Foundation 5.x** | 跨平台 AR（底层 ARCore/ARKit） |
| 3D 渲染 | **Universal RP (URP)** | 轻量级渲染管线，适合移动端 |
| Flutter-Unity 桥接 | **flutter_unity_widget** | 嵌入 Unity 视图到 Flutter 页面 |
| 模型格式 | **glTF/GLB** | 已有格式，Unity 原生支持 |
| 动画系统 | **Animator + Timeline** | 关键帧动画 + 可编程控制 |
| Shader | **URP Shader Graph** | 零件高亮/透明/线框 |

---

## 三、分步实施计划

### Step 1：Unity 项目初始化（Day 1-2）

#### 1.1 创建 Unity 项目

```
Unity Hub → New Project → 3D (URP)
项目名: ForkliftBao3D
路径: /Volumes/aigo S7 Med/ForkliftCLI/unity/
```

#### 1.2 安装必要 Package

通过 Unity Package Manager 安装：

| Package | 版本 | 用途 |
|---------|------|------|
| `com.unity.xr.arfoundation` | 5.x | AR 跨平台接口 |
| `com.unity.xr.arcore` | 5.x | Android AR 底层 |
| `com.unity.xr.arkit` | 5.x | iOS AR 底层 |
| `com.unity.xr.management` | 4.x | XR 插件管理 |
| `com.unity.render-pipelines.universal` | 14.x | URP 渲染 |
| `com.unity.inputsystem` | 1.x | 新输入系统 |
| `com.unity.textmeshpro` | 3.x | UI 文字 |

#### 1.3 项目目录结构

```
unity/
├── Assets/
│   ├── Scenes/
│   │   ├── ThreeDViewer.unity        # 3D查看场景
│   │   └── ARView.unity              # AR实景场景
│   ├── Scripts/
│   │   ├── Core/
│   │   │   ├── UnityMessageManager.cs    # Flutter通信桥
│   │   │   ├── ModelLoader.cs            # 模型加载器
│   │   │   └── AppManager.cs             # 全局管理
│   │   ├── Viewer/
│   │   │   ├── CameraController.cs       # 相机控制（旋转/缩放/平移）
│   │   │   ├── AnimationController.cs    # 机械动画控制
│   │   │   ├── PartHighlighter.cs        # 零件高亮/透明
│   │   │   ├── ExplodedView.cs           # 爆炸图控制
│   │   │   └── MeasurementOverlay.cs     # 尺寸标注叠加
│   │   └── AR/
│   │       ├── ARPlacementController.cs  # AR放置控制
│   │       ├── ARDimensionOverlay.cs     # AR尺寸叠加
│   │       ├── ARMastIndicator.cs        # 门架高度指示
│   │       └── ARRepairGuide.cs          # V3: AR维修指导
│   ├── Shaders/
│   │   ├── PartHighlight.shader          # 零件高亮
│   │   └── XRay透明.shader               # X光透明模式
│   ├── Materials/
│   ├── Prefabs/
│   │   ├── ForkliftBase.prefab           # 叉车基础预制体
│   │   └── ARAnchor.prefab              # AR锚点
│   ├── StreamingAssets/
│   │   └── models/                       # .glb 模型文件
│   └── Plugins/
│       ├── Android/
│       └── iOS/
├── Packages/
│   └── manifest.json
└── ProjectSettings/
    ├── ProjectVersion.txt
    ├── AndroidManifest.xml
    └── XRGeneralSettings.asset
```

#### 1.4 Flutter 侧集成 flutter_unity_widget

在 `pubspec.yaml` 添加依赖：

```yaml
dependencies:
  flutter_unity_widget: ^2.3.0
```

---

### Step 2：Flutter-Unity 通信桥（Day 2-3）

#### 2.1 通信协议设计

Flutter → Unity（MethodChannel: `forklift_bao_3d`）：

| 方法名 | 参数 | 说明 |
|--------|------|------|
| `loadModel` | `{url, modelId}` | 加载 3D 模型 |
| `playAnimation` | `{name, speed}` | 播放动画 |
| `stopAnimation` | `{name}` | 停止动画 |
| `setMastHeight` | `{heightMm}` | 设置门架高度 |
| `setTiltAngle` | `{angle}` | 设置倾斜角度 |
| `highlightPart` | `{partId, color}` | 高亮零件 |
| `clearHighlight` | `{}` | 清除高亮 |
| `setTransparent` | `{enabled, group}` | 透明模式 |
| `setExploded` | `{progress}` | 爆炸图进度 |
| `enterAR` | `{modelId, arConfig}` | 进入AR模式 |
| `setARScale` | `{factor}` | AR缩放 |
| `showARDimensions` | `{show}` | 显示/隐藏AR尺寸 |

Unity → Flutter（EventChannel: `forklift_bao_3d_events`）：

| 事件名 | 数据 | 说明 |
|--------|------|------|
| `onModelLoaded` | `{success, bounds}` | 模型加载完成 |
| `onAnimationComplete` | `{name}` | 动画播放完成 |
| `onPartClicked` | `{partId, partName}` | 零件被点击 |
| `onARPlaneDetected` | `{center, normal}` | AR平面检测到 |
| `onARSessionReady` | `{}` | AR会话就绪 |
| `onError` | `{code, message}` | 错误信息 |

#### 2.2 Flutter 侧代码

```dart
// mobile/lib/core/unity/unity_bridge.dart

import 'package:flutter/services.dart';
import 'dart:async';

class UnityBridge {
  static const _channel = MethodChannel('forklift_bao_3d');
  static const _eventChannel = EventChannel('forklift_bao_3d_events');

  StreamSubscription? _eventSubscription;
  final _eventController = StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get events => _eventController.stream;

  void init() {
    _eventSubscription = _eventChannel.receiveBroadcastStream().listen(
      (event) => _eventController.add(Map<String, dynamic>.from(event)),
    );
  }

  // --- Flutter → Unity ---

  Future<void> loadModel(String url, int modelId) async {
    await _channel.invokeMethod('loadModel', {
      'url': url,
      'modelId': modelId,
    });
  }

  Future<void> playAnimation(String name, {double speed = 1.0}) async {
    await _channel.invokeMethod('playAnimation', {
      'name': name,
      'speed': speed,
    });
  }

  Future<void> setMastHeight(double heightMm) async {
    await _channel.invokeMethod('setMastHeight', {'heightMm': heightMm});
  }

  Future<void> highlightPart(int partId, {String color = '#FFD700'}) async {
    await _channel.invokeMethod('highlightPart', {
      'partId': partId,
      'color': color,
    });
  }

  Future<void> setExploded(double progress) async {
    await _channel.invokeMethod('setExploded', {'progress': progress});
  }

  Future<void> enterAR(int modelId, Map<String, dynamic> arConfig) async {
    await _channel.invokeMethod('enterAR', {
      'modelId': modelId,
      'arConfig': arConfig,
    });
  }

  void dispose() {
    _eventSubscription?.cancel();
    _eventController.close();
  }
}
```

#### 2.3 Unity 侧代码

```csharp
// Assets/Scripts/Core/UnityMessageManager.cs

using UnityEngine;
using System.Collections.Generic;

public class UnityMessageManager : MonoBehaviour
{
    public static UnityMessageManager Instance { get; private set; }

    // Flutter → Unity 消息处理
    // 通过 UnityPlayer.UnitySendMessage 或原生插件接收

    private Dictionary<string, System.Action<string>> handlers = new();

    void Awake()
    {
        Instance = this;
        handlers["loadModel"] = HandleLoadModel;
        handlers["playAnimation"] = HandlePlayAnimation;
        handlers["setMastHeight"] = HandleSetMastHeight;
        handlers["highlightPart"] = HandleHighlightPart;
        handlers["setExploded"] = HandleSetExploded;
        handlers["enterAR"] = HandleEnterAR;
    }

    public void OnMessageFromFlutter(string json)
    {
        var msg = JsonUtility.FromJson<FlutterMessage>(json);
        if (handlers.TryGetValue(msg.method, out var handler))
            handler(msg.data);
    }

    // Unity → Flutter 发送事件
    public void SendToFlutter(string eventName, string jsonData)
    {
        // 通过原生插件回调 Flutter MethodChannel
        #if UNITY_ANDROID
        using (var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using (var activity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity"))
        {
            activity.Call("sendMessageToFlutter", eventName, jsonData);
        }
        #elif UNITY_IOS
        UnityMessageToFlutter(eventName, jsonData);
        #endif
    }

    private void HandleLoadModel(string data)
    {
        var param = JsonUtility.FromJson<LoadModelParam>(data);
        ModelLoader.Instance.LoadModel(param.url, param.modelId);
    }

    private void HandlePlayAnimation(string data)
    {
        var param = JsonUtility.FromJson<PlayAnimParam>(data);
        AnimationController.Instance.Play(param.name, param.speed);
    }

    private void HandleSetMastHeight(string data)
    {
        var param = JsonUtility.FromJson<MastParam>(data);
        AnimationController.Instance.SetMastHeight(param.heightMm);
    }

    private void HandleHighlightPart(string data)
    {
        var param = JsonUtility.FromJson<HighlightParam>(data);
        PartHighlighter.Instance.Highlight(param.partId, param.color);
    }

    private void HandleSetExploded(string data)
    {
        var param = JsonUtility.FromJson<ExplodedParam>(data);
        ExplodedView.Instance.SetProgress(param.progress);
    }

    private void HandleEnterAR(string data)
    {
        var param = JsonUtility.FromJson<EnterARParam>(data);
        ARPlacementController.Instance.EnterAR(param.modelId, param.arConfig);
    }
}

// 数据类
[System.Serializable]
public class FlutterMessage { public string method; public string data; }
[System.Serializable]
public class LoadModelParam { public string url; public int modelId; }
[System.Serializable]
public class PlayAnimParam { public string name; public float speed; }
[System.Serializable]
public class MastParam { public float heightMm; }
[System.Serializable]
public class HighlightParam { public int partId; public string color; }
[System.Serializable]
public class ExplodedParam { public float progress; }
[System.Serializable]
public class EnterARParam { public int modelId; public ArConfigData arConfig; }
[System.Serializable]
public class ArConfigData
{
    public float real_length_mm;
    public float real_width_mm;
    public float real_height_mm;
    public float real_mast_height_mm;
    public float real_wheelbase_mm;
    public float real_turning_radius_mm;
}
```

---

### Step 3：3D 查看器场景（Day 3-5）

#### 3.1 场景搭建

**ThreeDViewer.unity 场景层级：**

```
Scene Root
├── Camera
│   ├── OrbitCamera (脚本: CameraController.cs)
│   └── URP Camera
├── Directional Light
├── ModelContainer (空物体，挂载加载的模型)
├── UI Canvas
│   ├── ControlPanel (门架↑↓ / 前倾后倾 / 货叉↑↓)
│   ├── PartsListPanel (零件列表)
│   ├── TransparencyToggle
│   ├── ExplodedSlider
│   └── ScreenshotButton
└── EventSystem
```

#### 3.2 相机控制

```csharp
// Assets/Scripts/Viewer/CameraController.cs

using UnityEngine;

public class CameraController : MonoBehaviour
{
    [Header("Rotation")]
    public float rotateSpeed = 5f;
    public float damping = 5f;

    [Header("Zoom")]
    public float zoomSpeed = 2f;
    public float minDistance = 1f;
    public float maxDistance = 20f;

    private Transform target;
    private float currentDistance = 5f;
    private Vector3 currentAngles = new Vector3(30, 45, 0);

    public void SetTarget(Transform t) => target = t;

    void LateUpdate()
    {
        if (target == null) return;

        // 从 Flutter 接收的旋转输入
        // 通过 Touch 或 Mouse 控制
        if (Input.touchCount == 1)
        {
            var touch = Input.GetTouch(0);
            if (touch.phase == TouchPhase.Moved)
            {
                currentAngles.y += touch.deltaPosition.x * rotateSpeed * 0.1f;
                currentAngles.x -= touch.deltaPosition.y * rotateSpeed * 0.1f;
                currentAngles.x = Mathf.Clamp(currentAngles.x, -80, 80);
            }
        }

        // 双指缩放
        if (Input.touchCount == 2)
        {
            float prevDist = (Input.GetTouch(0).position - Input.GetTouch(1).position).magnitude;
            // ... 计算缩放
        }

        var rotation = Quaternion.Euler(currentAngles);
        var position = target.position - rotation * Vector3.forward * currentDistance;
        transform.position = Vector3.Lerp(transform.position, position, Time.deltaTime * damping);
        transform.rotation = Quaternion.Slerp(transform.rotation, rotation, Time.deltaTime * damping);
    }

    // Flutter 调用：重置视角
    public void ResetView()
    {
        currentAngles = new Vector3(30, 45, 0);
        currentDistance = 5f;
    }

    // Flutter 调用：聚焦到特定零件
    public void FocusOnPart(Vector3 partPosition, float distance)
    {
        target.position = partPosition;
        currentDistance = distance;
    }
}
```

#### 3.3 机械动画控制

```csharp
// Assets/Scripts/Viewer/AnimationController.cs

using UnityEngine;

public class AnimationController : MonoBehaviour
{
    [Header("门架")]
    public Transform mastInner;      // 内门架
    public Transform mastOuter;      // 外门架
    public Transform fork;           // 货叉
    public float mastMaxHeight = 4500f;  // mm
    public float mastMinHeight = 1800f;  // mm

    [Header("倾斜")]
    public Transform mastAssembly;   // 门架总成
    public float maxTiltForward = 6f;    // 度
    public float maxTiltBackward = 12f;  // 度

    [Header("转向")]
    public Transform rearWheel;      // 后轮
    public float maxSteerAngle = 30f;

    private Animator animator;
    private float currentMastHeight = 1800f;
    private float currentTiltAngle = 0f;

    void Start()
    {
        animator = GetComponentInChildren<Animator>();
    }

    // === 门架升降 ===
    public void SetMastHeight(float heightMm)
    {
        currentMastHeight = Mathf.Clamp(heightMm, mastMinHeight, mastMaxHeight);
        float t = (currentMastHeight - mastMinHeight) / (mastMaxHeight - mastMinHeight);

        // 内门架上升
        if (mastInner != null)
        {
            float innerRise = t * 1.5f; // 外门架高度的1.5倍
            mastInner.localPosition = new Vector3(
                mastInner.localPosition.x,
                innerRise,
                mastInner.localPosition.z
            );
        }

        // 货叉跟随
        if (fork != null)
        {
            fork.localPosition = new Vector3(
                fork.localPosition.x,
                t * 2.7f, // 总升程
                fork.localPosition.z
            );
        }

        // 通知 Flutter
        UnityMessageManager.Instance.SendToFlutter(
            "onMastHeightChanged",
            JsonUtility.ToJson(new { heightMm = currentMastHeight })
        );
    }

    public void MastUp()
    {
        SetMastHeight(currentMastHeight + 300f); // 每次300mm
    }

    public void MastDown()
    {
        SetMastHeight(currentMastHeight - 300f);
    }

    // === 倾斜 ===
    public void SetTiltAngle(float angle)
    {
        currentTiltAngle = Mathf.Clamp(angle, -maxTiltForward, maxTiltBackward);
        if (mastAssembly != null)
        {
            mastAssembly.localRotation = Quaternion.Euler(currentTiltAngle, 0, 0);
        }
    }

    public void TiltForward() => SetTiltAngle(currentTiltAngle + 3f);
    public void TiltBackward() => SetTiltAngle(currentTiltAngle - 3f);

    // === 转向 ===
    public void SetSteerAngle(float angle)
    {
        float clamped = Mathf.Clamp(angle, -maxSteerAngle, maxSteerAngle);
        if (rearWheel != null)
        {
            rearWheel.localRotation = Quaternion.Euler(0, clamped, 0);
        }
    }

    // === 动画播放（从后端加载的动画片段） ===
    public void Play(string animName, float speed = 1f)
    {
        if (animator != null)
        {
            animator.speed = speed;
            animator.Play(animName);
        }
    }

    public float GetCurrentHeight() => currentMastHeight;
    public float GetCurrentTilt() => currentTiltAngle;
}
```

#### 3.4 零件高亮与透明

```csharp
// Assets/Scripts/Viewer/PartHighlighter.cs

using UnityEngine;
using System.Collections.Generic;

public class PartHighlighter : MonoBehaviour
{
    private Dictionary<int, Renderer[]> partRenderers = new();
    private Dictionary<Renderer, Material[]> originalMaterials = new();
    private Material highlightMaterial;
    private Material transparentMaterial;

    void Start()
    {
        highlightMaterial = Resources.Load<Material>("Materials/Highlight");
        transparentMaterial = Resources.Load<Material>("Materials/Transparent");
    }

    // 注册零件的 MeshRenderer
    public void RegisterPart(int partId, GameObject partObj)
    {
        var renderers = partObj.GetComponentsInChildren<Renderer>();
        partRenderers[partId] = renderers;

        foreach (var r in renderers)
        {
            if (!originalMaterials.ContainsKey(r))
                originalMaterials[r] = r.sharedMaterials;
        }
    }

    // 高亮零件
    public void Highlight(int partId, string colorHex = "#FFD700")
    {
        if (!partRenderers.ContainsKey(partId)) return;

        var mat = new Material(highlightMaterial);
        mat.color = HexToColor(colorHex);
        mat.SetColor("_EmissionColor", mat.color * 0.5f);

        foreach (var r in partRenderers[partId])
        {
            var mats = new Material[r.sharedMaterials.Length + 1];
            r.sharedMaterials.CopyTo(mats, 0);
            mats[mats.Length - 1] = mat;
            r.sharedMaterials = mats;
        }
    }

    // 清除高亮
    public void ClearHighlight()
    {
        foreach (var kvp in partRenderers)
        {
            foreach (var r in kvp.Value)
            {
                if (originalMaterials.ContainsKey(r))
                    r.sharedMaterials = originalMaterials[r];
            }
        }
    }

    // 透明模式
    public void SetTransparent(bool enabled, string group = "all")
    {
        foreach (var kvp in partRenderers)
        {
            foreach (var r in kvp.Value)
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++)
                {
                    var newMat = new Material(enabled ? transparentMaterial : originalMaterials[r][0]);
                    if (enabled)
                    {
                        newMat.color = new Color(0.7f, 0.7f, 0.7f, 0.2f);
                    }
                    mats[i] = newMat;
                }
                r.sharedMaterials = mats;
            }
        }
    }

    private Color HexToColor(string hex)
    {
        ColorUtility.TryParseHtmlString(hex, out Color color);
        return color;
    }
}
```

#### 3.5 爆炸图

```csharp
// Assets/Scripts/Viewer/ExplodedView.cs

using UnityEngine;
using System.Collections.Generic;

public class ExplodedView : MonoBehaviour
{
    [System.Serializable]
    public class PartExplosion
    {
        public Transform part;
        public Vector3 originalPos;
        public Vector3 explodeDirection;
        public float explodeDistance;
    }

    public List<PartExplosion> parts = new();
    private float currentProgress = 0f;

    void Start()
    {
        // 自动收集所有子零件的原始位置
        foreach (Transform child in GetComponentsInChildren<Transform>())
        {
            if (child == transform) continue;
            parts.Add(new PartExplosion
            {
                part = child,
                originalPos = child.localPosition,
                explodeDirection = (child.localPosition - transform.position).normalized,
                explodeDistance = 1.5f
            });
        }
    }

    public void SetProgress(float progress)
    {
        currentProgress = Mathf.Clamp01(progress);

        foreach (var p in parts)
        {
            p.part.localPosition = p.originalPos + p.explodeDirection * p.explodeDistance * currentProgress;
        }
    }

    public void Toggle()
    {
        SetProgress(currentProgress > 0.5f ? 0f : 1f);
    }
}
```

---

### Step 4：AR 场景（Day 5-8）

#### 4.1 AR 场景搭建

**ARView.unity 场景层级：**

```
AR Scene Root
├── AR Session
├── AR Session Origin
│   ├── AR Camera (挂载 ARCameraManager)
│   ├── AR Plane Manager (平面检测)
│   ├── AR Raycast Manager (射线检测)
│   ├── ModelContainer (放置的叉车模型)
│   └── AR Dimension Overlay (尺寸标注Canvas)
├── AR Input Manager
├── UI Canvas
│   ├── DimensionPanel (车辆尺寸)
│   ├── MastHeightIndicator (门架高度仪表)
│   ├── ControlButtons (对齐/截图/切换)
│   └── ScanPrompt (扫描地面提示)
└── EventSystem
```

#### 4.2 AR 放置控制器

```csharp
// Assets/Scripts/AR/ARPlacementController.cs

using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using System.Collections.Generic;

public class ARPlacementController : MonoBehaviour
{
    [Header("AR Components")]
    public ARRaycastManager raycastManager;
    public ARPlaneManager planeManager;
    public Transform modelContainer;

    [Header("Config")]
    public float scaleFactor = 0.001f; // mm → m

    private bool isPlaced = false;
    private Pose lastValidPose;
    private List<ARRaycastHit> hits = new();

    void Update()
    {
        if (isPlaced) return;

        // 从屏幕中心射线检测平面
        var screenCenter = new Vector2(Screen.width / 2f, Screen.height / 2f);

        if (raycastManager.Raycast(screenCenter, hits, TrackableType.PlaneWithinPolygon))
        {
            lastValidPose = hits[0].pose;

            // 显示放置预览
            modelContainer.position = lastValidPose.position;
            modelContainer.rotation = lastValidPose.rotation;
            modelContainer.gameObject.SetActive(true);
        }
    }

    // Flutter 调用：确认放置
    public void ConfirmPlacement()
    {
        isPlaced = true;
        modelContainer.position = lastValidPose.position;

        // 应用真实尺寸缩放
        ApplyRealScale();

        // 显示尺寸标注
        ARDimensionOverlay.Instance.ShowDimensions();

        UnityMessageManager.Instance.SendToFlutter("onARPlaced", "{}");
    }

    // 应用真实尺寸（1:1）
    private void ApplyRealScale()
    {
        // 从 ArModelConfig 获取真实尺寸
        // 模型单位是米，真实尺寸是毫米
        // scale = real_mm / model_m / 1000
        modelContainer.localScale = Vector3.one * scaleFactor;
    }

    // Flutter 调用：设置缩放因子
    public void SetScale(float factor)
    {
        modelContainer.localScale = Vector3.one * factor;
    }

    // Flutter 调用：重新定位
    public void Reposition()
    {
        isPlaced = false;
        modelContainer.gameObject.SetActive(false);
    }
}
```

#### 4.3 AR 尺寸叠加

```csharp
// Assets/Scripts/AR/ARDimensionOverlay.cs

using UnityEngine;
using TMPro;

public class ARDimensionOverlay : MonoBehaviour
{
    [Header("UI References")]
    public TextMeshProUGUI lengthText;
    public TextMeshProUGUI widthText;
    public TextMeshProUGUI heightText;
    public TextMeshProUGUI wheelbaseText;
    public TextMeshProUGUI areaText;

    [Header("3D Line Renderers")]
    public LineRenderer lengthLine;   // 长度线
    public LineRenderer widthLine;    // 宽度线
    public LineRenderer turningCircle; // 转弯半径圈

    private ArConfigData config;
    private Transform modelTransform;

    public void Init(ArConfigData arConfig, Transform model)
    {
        config = arConfig;
        modelTransform = model;
    }

    public void ShowDimensions()
    {
        if (config == null) return;

        // 更新文字
        lengthText.text = $"长: {(config.real_length_mm / 1000f):F2}m";
        widthText.text = $"宽: {(config.real_width_mm / 1000f):F2}m";
        heightText.text = $"高: {(config.real_height_mm / 1000f):F2}m";
        wheelbaseText.text = $"轴距: {(config.real_wheelbase_mm / 1000f):F2}m";

        float area = (config.real_length_mm / 1000f) * (config.real_width_mm / 1000f);
        areaText.text = $"占地面积: {area:F2}m²";

        // 绘制长度线
        DrawLine(lengthLine,
            modelTransform.position + Vector3.forward * (config.real_length_mm / 2000f),
            modelTransform.position - Vector3.forward * (config.real_length_mm / 2000f));

        // 绘制宽度线
        DrawLine(widthLine,
            modelTransform.position + Vector3.right * (config.real_width_mm / 2000f),
            modelTransform.position - Vector3.right * (config.real_width_mm / 2000f));

        // 绘制转弯半径圈
        DrawCircle(turningCircle, modelTransform.position,
            config.real_turning_radius_mm / 1000f, 64);
    }

    private void DrawLine(LineRenderer lr, Vector3 start, Vector3 end)
    {
        lr.positionCount = 2;
        lr.SetPosition(0, start);
        lr.SetPosition(1, end);
        lr.startWidth = 0.01f;
        lr.endWidth = 0.01f;
    }

    private void DrawCircle(LineRenderer lr, Vector3 center, float radius, int segments)
    {
        lr.positionCount = segments + 1;
        for (int i = 0; i <= segments; i++)
        {
            float angle = i * 2f * Mathf.PI / segments;
            lr.SetPosition(i, center + new Vector3(
                Mathf.Cos(angle) * radius,
                0.01f,
                Mathf.Sin(angle) * radius
            ));
        }
    }
}
```

#### 4.4 AR 门架高度指示

```csharp
// Assets/Scripts/AR/ARMastIndicator.cs

using UnityEngine;
using TMPro;

public class ARMastIndicator : MonoBehaviour
{
    public TextMeshProUGUI heightText;
    public RectTransform heightBar;    // 垂直进度条
    public float minHeight = 1.8f;     // 米
    public float maxHeight = 4.5f;     // 米

    private AnimationController mastController;

    void Start()
    {
        mastController = FindObjectOfType<AnimationController>();
    }

    void Update()
    {
        if (mastController == null) return;

        float currentM = mastController.GetCurrentHeight() / 1000f;
        heightText.text = $"{currentM:F1}m";

        // 更新进度条
        float t = (currentM - minHeight) / (maxHeight - minHeight);
        heightBar.anchorMax = new Vector2(1, t);
    }

    // Flutter 调用：门架上升
    public void MastUp()
    {
        mastController?.MastUp();
    }

    // Flutter 调用：门架下降
    public void MastDown()
    {
        mastController?.MastDown();
    }
}
```

---

### Step 5：Flutter 侧集成（Day 8-10）

#### 5.1 Unity 视图包装组件

```dart
// mobile/lib/core/unity/unity_view_wrapper.dart

import 'package:flutter/material.dart';
import 'package:flutter_unity_widget/flutter_unity_widget.dart';
import 'unity_bridge.dart';

class UnityViewWrapper extends StatefulWidget {
  final int? forkliftModelId;
  final String? modelUrl;
  final bool enableAR;
  final VoidCallback? onPartClicked;

  const UnityViewWrapper({
    super.key,
    this.forkliftModelId,
    this.modelUrl,
    this.enableAR = false,
    this.onPartClicked,
  });

  @override
  State<UnityViewWrapper> createState() => _UnityViewWrapperState();
}

class _UnityViewWrapperState extends State<UnityViewWrapper> {
  UnityWidgetController? _unityController;
  final _bridge = UnityBridge();

  @override
  void initState() {
    super.initState();
    _bridge.init();
    _bridge.events.listen(_handleUnityEvent);
  }

  @override
  Widget build(BuildContext context) {
    return UnityWidget(
      onUnityCreated: _onUnityCreated,
      // 嵌入模式（非全屏）
      isPlaceholder: false,
    );
  }

  void _onUnityCreated(UnityWidgetController controller) {
    _unityController = controller;

    // 加载模型
    if (widget.modelUrl != null && widget.forkliftModelId != null) {
      _bridge.loadModel(widget.modelUrl!, widget.forkliftModelId!);
    }

    // AR 模式
    if (widget.enableAR) {
      _bridge.enterAR(widget.forkliftModelId ?? 0, {});
    }
  }

  void _handleUnityEvent(Map<String, dynamic> event) {
    switch (event['eventName']) {
      case 'onPartClicked':
        widget.onPartClicked?.call();
        break;
      case 'onModelLoaded':
        setState(() {});
        break;
    }
  }

  @override
  void dispose() {
    _bridge.dispose();
    _unityController?.dispose();
    super.dispose();
  }
}
```

#### 5.2 改造 ThreeDViewerPage

```dart
// mobile/lib/features/threed/threed_viewer_page.dart (改造后)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/unity/unity_view_wrapper.dart';
import '../../core/unity/unity_bridge.dart';
import '../../core/api/api_client.dart';

class ThreeDViewerPage extends ConsumerStatefulWidget {
  final String? forkliftModelId;
  final String? modelUrl;
  final String? title;

  const ThreeDViewerPage({
    super.key,
    this.forkliftModelId,
    this.modelUrl,
    this.title,
  });

  @override
  ConsumerState<ThreeDViewerPage> createState() => _ThreeDViewerPageState();
}

class _ThreeDViewerPageState extends ConsumerState<ThreeDViewerPage> {
  final _bridge = UnityBridge();
  bool _isLoading = true;
  bool _showPartsList = false;
  double _explodedProgress = 0.0;
  String? _selectedPart;

  @override
  void initState() {
    super.initState();
    _bridge.init();
    _bridge.events.listen(_onUnityEvent);
    _loadModel();
  }

  Future<void> _loadModel() async {
    // 从后端获取 3D 模型数据
    // 已有 API: GET /api/v1/3d/forklift/{forkliftModelId}
    setState(() => _isLoading = false);
  }

  void _onUnityEvent(Map<String, dynamic> event) {
    switch (event['eventName']) {
      case 'onModelLoaded':
        setState(() => _isLoading = false);
        break;
      case 'onPartClicked':
        setState(() => _selectedPart = event['partName']);
        _showPartDetail(event['partId']);
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title ?? '3D 叉车'),
        actions: [
          IconButton(
            icon: const Icon(Icons.view_list),
            onPressed: () => setState(() => _showPartsList = !_showPartsList),
          ),
          IconButton(
            icon: const Icon(Icons.center_focus_strong),
            onPressed: () => _bridge.resetView(),
          ),
        ],
      ),
      body: Stack(
        children: [
          // Unity 3D 视图
          UnityViewWrapper(
            forkliftModelId: int.tryParse(widget.forkliftModelId ?? ''),
            modelUrl: widget.modelUrl,
            onPartClicked: () {},
          ),

          // 加载指示
          if (_isLoading)
            const Center(child: CircularProgressIndicator()),

          // 控制面板
          Positioned(
            left: 16,
            bottom: 100,
            child: _buildControlPanel(),
          ),

          // 爆炸图滑块
          Positioned(
            right: 16,
            top: 80,
            child: _buildExplodedSlider(),
          ),

          // 零件列表
          if (_showPartsList)
            Positioned(
              right: 0,
              bottom: 0,
              child: _buildPartsListPanel(),
            ),
        ],
      ),
    );
  }

  Widget _buildControlPanel() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 门架升降
            Row(
              children: [
                _controlButton('门架↑', () => _bridge.setMastHeight(
                  _currentMastHeight + 300)),
                const SizedBox(width: 8),
                _controlButton('门架↓', () => _bridge.setMastHeight(
                  _currentMastHeight - 300)),
              ],
            ),
            const SizedBox(height: 8),
            // 倾斜
            Row(
              children: [
                _controlButton('前倾', () => _bridge.playAnimation('tilt_forward')),
                const SizedBox(width: 8),
                _controlButton('后倾', () => _bridge.playAnimation('tilt_backward')),
              ],
            ),
            const SizedBox(height: 8),
            // 货叉
            Row(
              children: [
                _controlButton('货叉↑', () => _bridge.playAnimation('fork_up')),
                const SizedBox(width: 8),
                _controlButton('货叉↓', () => _bridge.playAnimation('fork_down')),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _controlButton(String label, VoidCallback onPressed) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(64, 36),
      ),
      child: Text(label, style: const TextStyle(fontSize: 12)),
    );
  }

  Widget _buildExplodedSlider() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('拆解', style: TextStyle(fontSize: 12)),
            RotatedBox(
              quarterTurns: -1,
              child: Slider(
                value: _explodedProgress,
                onChanged: (v) {
                  setState(() => _explodedProgress = v);
                  _bridge.setExploded(v);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPartsListPanel() {
    return Container(
      width: 280,
      height: 300,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
        boxShadow: [BoxShadow(blurRadius: 8, color: Colors.black26)],
      ),
      child: Column(
        children: [
          const Padding(
            padding: EdgeInsets.all(12),
            child: Text('零部件', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
          Expanded(
            child: ListView(
              children: [
                // 从 API 加载零件列表
                // 每个零件可点击 → 高亮 3D 模型中的对应零件
              ],
            ),
          ),
        ],
      ),
    );
  }

  double _currentMastHeight = 1800;

  void _showPartDetail(int partId) {
    // 跳转到配件详情页
    context.push('/parts?partId=$partId');
  }

  @override
  void dispose() {
    _bridge.dispose();
    super.dispose();
  }
}
```

#### 5.3 改造 ArViewPage

```dart
// mobile/lib/features/ar/ar_view_page.dart (改造后)

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/unity/unity_view_wrapper.dart';
import '../../core/unity/unity_bridge.dart';

class ArViewPage extends ConsumerStatefulWidget {
  final String? forkliftModelId;

  const ArViewPage({super.key, this.forkliftModelId});

  @override
  ConsumerState<ArViewPage> createState() => _ArViewPageState();
}

class _ArViewPageState extends ConsumerState<ArViewPage> {
  final _bridge = UnityBridge();
  bool _isARReady = false;
  bool _showDimensions = true;
  double _mastHeight = 1.8;
  Map<String, dynamic>? _arConfig;

  @override
  void initState() {
    super.initState();
    _bridge.init();
    _bridge.events.listen(_onAREvent);
    _loadARConfig();
  }

  Future<void> _loadARConfig() async {
    // 从后端获取 AR 配置
    // 已有 API: GET /api/v1/ar/config/{forkliftModelId}
    final config = await ApiClient().getArConfig(widget.forkliftModelId ?? '');
    setState(() => _arConfig = config);
  }

  void _onAREvent(Map<String, dynamic> event) {
    switch (event['eventName']) {
      case 'onARSessionReady':
        setState(() => _isARReady = true);
        break;
      case 'onARPlaneDetected':
        // 显示"点击放置"提示
        break;
      case 'onARPlaced':
        // 模型已放置，显示控制面板
        break;
      case 'onMastHeightChanged':
        setState(() => _mastHeight = event['heightMm'] / 1000.0);
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AR 实景'),
        backgroundColor: Colors.black87,
        actions: [
          IconButton(
            icon: Icon(_showDimensions ? Icons.straighten : Icons.straighten),
            onPressed: () => setState(() => _showDimensions = !_showDimensions),
          ),
          IconButton(
            icon: const Icon(Icons.camera_alt),
            onPressed: _takeScreenshot,
          ),
        ],
      ),
      body: Stack(
        children: [
          // Unity AR 视图
          UnityViewWrapper(
            forkliftModelId: int.tryParse(widget.forkliftModelId ?? ''),
            enableAR: true,
          ),

          // 扫描提示（AR 未就绪时）
          if (!_isARReady)
            Center(
              child: Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.view_in_ar, size: 48, color: Colors.white),
                    SizedBox(height: 12),
                    Text('请缓慢移动手机扫描地面',
                        style: TextStyle(color: Colors.white, fontSize: 16)),
                  ],
                ),
              ),
            ),

          // 门架高度指示器（左侧）
          Positioned(
            left: 16,
            top: 80,
            child: _buildMastIndicator(),
          ),

          // 车辆尺寸（右上角）
          if (_showDimensions && _arConfig != null)
            Positioned(
              right: 16,
              top: 80,
              child: _buildDimensionPanel(),
            ),

          // 底部控制栏
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: _buildBottomControls(),
          ),
        ],
      ),
    );
  }

  Widget _buildMastIndicator() {
    return Card(
      color: Colors.black87,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('门架高度',
                style: TextStyle(color: Colors.white70, fontSize: 12)),
            const SizedBox(height: 8),
            Text('${_mastHeight.toStringAsFixed(1)}m',
                style: const TextStyle(
                    color: Colors.greenAccent,
                    fontSize: 24,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _arButton('▲', () => _bridge.setMastHeight((_mastHeight + 0.3) * 1000)),
            const SizedBox(height: 4),
            _arButton('▼', () => _bridge.setMastHeight((_mastHeight - 0.3) * 1000)),
          ],
        ),
      ),
    );
  }

  Widget _buildDimensionPanel() {
    final c = _arConfig!;
    return Card(
      color: Colors.black87,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            _dimRow('长', c['real_length_mm'] ?? 0),
            _dimRow('宽', c['real_width_mm'] ?? 0),
            _dimRow('高', c['real_height_mm'] ?? 0),
            _dimRow('轴距', c['real_wheelbase_mm'] ?? 0),
            _dimRow('转弯半径', c['real_turning_radius_mm'] ?? 0),
            const Divider(color: Colors.white30),
            _dimRow('占地面积',
              (c['real_length_mm'] ?? 0) * (c['real_width_mm'] ?? 0) / 1000000,
              unit: 'm²'),
          ],
        ),
      ),
    );
  }

  Widget _dimRow(String label, dynamic value, {String unit = 'm'}) {
    final display = unit == 'm²'
        ? '${(value as num).toDouble().toStringAsFixed(2)}$unit'
        : '${((value as num).toDouble() / 1000).toStringAsFixed(2)}$unit';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Text('$label: $display',
          style: const TextStyle(color: Colors.white, fontSize: 12)),
    );
  }

  Widget _buildBottomControls() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(color: Colors.black87),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _bottomButton('对齐', Icons.center_focus_strong, () {}),
          _bottomButton('截图', Icons.camera_alt, _takeScreenshot),
          _bottomButton(
            _showDimensions ? '隐藏尺寸' : '显示尺寸',
            Icons.straighten,
            () => setState(() => _showDimensions = !_showDimensions),
          ),
        ],
      ),
    );
  }

  Widget _bottomButton(String label, IconData icon, VoidCallback onPressed) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          icon: Icon(icon, color: Colors.white),
          onPressed: onPressed,
        ),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
      ],
    );
  }

  Widget _arButton(String text, VoidCallback onPressed) {
    return SizedBox(
      width: 40,
      height: 32,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.white24,
          padding: EdgeInsets.zero,
        ),
        child: Text(text, style: const TextStyle(color: Colors.white)),
      ),
    );
  }

  void _takeScreenshot() {
    _bridge.playAnimation('screenshot', speed: 1.0);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('截图已保存')),
    );
  }

  @override
  void dispose() {
    _bridge.dispose();
    super.dispose();
  }
}
```

---

### Step 6：Android/iOS 原生桥接（Day 10-12）

#### 6.1 Android 端（Kotlin）

```
mobile/android/app/src/main/kotlin/com/example/forklift_bao/
├── MainActivity.kt
├── FlutterUnityPlugin.kt
└── UnityPlayerFragment.kt
```

**关键文件：FlutterUnityPlugin.kt**

```kotlin
package com.example.forklift_bao

import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import com.unity3d.player.UnityPlayer

class FlutterUnityPlugin : FlutterPlugin, MethodChannel.MethodCallHandler {
    private lateinit var channel: MethodChannel
    private var unityPlayer: UnityPlayer? = null

    override fun onAttachedToEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel = MethodChannel(binding.binaryMessenger, "forklift_bao_3d")
        channel.setMethodCallHandler(this)

        // 初始化 Unity Player
        unityPlayer = UnityPlayer(binding.applicationContext, null)
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "loadModel" -> {
                val url = call.argument<String>("url") ?: ""
                val modelId = call.argument<Int>("modelId") ?: 0
                // 调用 Unity 侧
                UnityPlayer.UnitySendMessage(
                    "UnityMessageManager",
                    "OnMessageFromFlutter",
                    """{"method":"loadModel","data":"{\"url\":\"$url\",\"modelId\":$modelId}"}"""
                )
                result.success(null)
            }
            "playAnimation" -> {
                val name = call.argument<String>("name") ?: ""
                val speed = call.argument<Double>("speed") ?: 1.0
                UnityPlayer.UnitySendMessage(
                    "UnityMessageManager",
                    "OnMessageFromFlutter",
                    """{"method":"playAnimation","data":"{\"name\":\"$name\",\"speed\":$speed}"}"""
                )
                result.success(null)
            }
            "setMastHeight" -> {
                val height = call.argument<Double>("heightMm") ?: 1800.0
                UnityPlayer.UnitySendMessage(
                    "UnityMessageManager",
                    "OnMessageFromFlutter",
                    """{"method":"setMastHeight","data":"{\"heightMm\":$height}"}"""
                )
                result.success(null)
            }
            // ... 其他方法
            else -> result.notImplemented()
        }
    }

    // Unity → Flutter 回调
    fun sendMessageToFlutter(eventName: String, data: String) {
        channel.invokeEvent(eventName, mapOf("data" to data))
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel.setMethodCallHandler(null)
        unityPlayer?.destroy()
    }
}
```

#### 6.2 iOS 端（Swift）

```
mobile/ios/Runner/
├── AppDelegate.swift
├── FlutterUnityPlugin.swift
└── UnityUtils.swift
```

**关键文件：FlutterUnityPlugin.swift**

```swift
import Flutter
import UIKit
import UnityFramework

class FlutterUnityPlugin: NSObject, FlutterPlugin, FlutterStreamHandler {
    private var eventSink: FlutterEventSink?
    private var unityFramework: UnityFramework?

    static func register(with registrar: FlutterPluginRegistrar) {
        let channel = FlutterMethodChannel(
            name: "forklift_bao_3d",
            binaryMessenger: registrar.messenger()
        )
        let eventChannel = FlutterEventChannel(
            name: "forklift_bao_3d_events",
            binaryMessenger: registrar.messenger()
        )
        let instance = FlutterUnityPlugin()
        registrar.addMethodCallDelegate(instance, channel: channel)
        eventChannel.setStreamHandler(instance)
    }

    func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "loadModel":
            guard let args = call.arguments as? [String: Any],
                  let url = args["url"] as? String,
                  let modelId = args["modelId"] as? Int else {
                result(FlutterError(code: "INVALID_ARGS", message: nil, details: nil))
                return
            }
            // 调用 Unity
            unityFramework?.appController.sendMessageToGameObject(
                withName: "UnityMessageManager",
                methodName: "OnMessageFromFlutter",
                message: """
                {"method":"loadModel","data":"{\\"url\\":\\"$url\\",\\"modelId\\":$modelId}"}
                """
            )
            result(nil)
        // ... 其他方法
        default:
            result(FlutterMethodNotImplemented)
        }
    }

    // FlutterStreamHandler
    func onListen(withArguments arguments: Any?, eventSink events: @escaping FlutterEventSink) -> FlutterError? {
        self.eventSink = events
        return nil
    }

    func onCancel(withArguments arguments: Any?) -> FlutterError? {
        self.eventSink = nil
        return nil
    }

    // Unity → Flutter 回调
    func sendToFlutter(eventName: String, data: String) {
        eventSink?(["eventName": eventName, "data": data])
    }
}
```

---

### Step 7：3D 模型管线（Day 12-14）

#### 7.1 模型标准（对应文档第三十八章）

每个叉车模型需要：

```
Forklift_8FG30/
├── Forklift_8FG30.glb          # 主模型文件
├── Forklift_8FG30_thumbnail.png # 缩略图
└── metadata.json                # 元数据
```

**metadata.json 示例：**

```json
{
  "name": "丰田 8FG30",
  "format": "glb",
  "scale_unit": "meters",
  "parts": [
    {
      "mesh_name": "Body",
      "part_id": 1,
      "name": "车身",
      "group": "body",
      "is_interactive": true
    },
    {
      "mesh_name": "Mast_Inner",
      "part_id": 2,
      "name": "内门架",
      "group": "mast",
      "is_interactive": true
    },
    {
      "mesh_name": "Fork",
      "part_id": 3,
      "name": "货叉",
      "group": "fork",
      "is_interactive": true
    }
  ],
  "animations": [
    {
      "name": "mast_up",
      "clip_name": "Mast_Raise",
      "duration_ms": 3000,
      "loop": false
    },
    {
      "name": "mast_down",
      "clip_name": "Mast_Lower",
      "duration_ms": 3000,
      "loop": false
    },
    {
      "name": "tilt_forward",
      "clip_name": "Tilt_Forward",
      "duration_ms": 2000,
      "loop": false
    }
  ],
  "ar_config": {
    "real_length_mm": 3450,
    "real_width_mm": 1200,
    "real_height_mm": 2100,
    "real_mast_height_mm": 4500,
    "real_wheelbase_mm": 1650,
    "real_turning_radius_mm": 2500
  }
}
```

#### 7.2 模型制作规范

| 规范 | 要求 |
|------|------|
| 格式 | glTF 2.0 / GLB |
| 面数 | 单台叉车 ≤ 50,000 三角面 |
| 贴图 | 2048×2048 最大，PBR 材质 |
| 命名 | mesh_name 必须与 metadata 中一致 |
| 动画 | 使用 Animator Controller，clip 命名清晰 |
| 分组 | 每个可交互零件单独 mesh |
| 坐标 | Y 轴向上，原点在车辆底部中心 |
| 缩放 | 1 单位 = 1 米 |

#### 7.3 模型上传流程

```
3D 建模师制作模型 (.blend/.max/.c4d)
        ↓
导出为 .glb（保持 PBR 材质）
        ↓
编写 metadata.json
        ↓
上传到后端 storage
        ↓
后端 Model3D 表写入 file_url
        ↓
前端调用 API → Unity 加载
```

---

### Step 8：后端 API 扩展（Day 14-15）

#### 8.1 新增接口

```python
# backend/app/api/model3d.py 新增

@router.get("/forklift/{forklift_model_id}/full")
async def get_full_3d_data(
    forklift_model_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """一次返回 3D 模型 + 零件 + 动画 + AR 配置"""
    model = db.query(Model3D).filter(
        Model3D.forklift_model_id == forklift_model_id
    ).first()
    if not model:
        raise HTTPException(404, "未找到3D模型")

    ar_config = db.query(ArModelConfig).filter(
        ArModelConfig.forklift_model_id == forklift_model_id
    ).first()

    return {
        "model": Model3DOut.model_validate(model),
        "parts": [Model3DPartOut.model_validate(p) for p in model.parts],
        "animations": [Model3DAnimationOut.model_validate(a) for a in model.animations],
        "ar_config": ArConfigOut.model_validate(ar_config) if ar_config else None,
    }
```

#### 8.2 模型文件服务

```python
# backend/app/api/model3d.py 新增

import os
from fastapi.responses import FileResponse

@router.get("/file/{model_id}")
async def get_model_file(
    model_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """返回 .glb 模型文件"""
    model = db.query(Model3D).get(model_id)
    if not model or not model.file_url:
        raise HTTPException(404, "模型文件不存在")

    file_path = os.path.join(config.UPLOAD_DIR, model.file_url)
    if not os.path.exists(file_path):
        raise HTTPException(404, "模型文件未找到")

    return FileResponse(
        file_path,
        media_type="model/gltf-binary",
        filename=f"{model.name}.glb"
    )
```

---

## 四、开发排期

```
Week 1 (Day 1-5):
├── Day 1-2: Unity 项目初始化 + Package 安装 + 目录结构
├── Day 2-3: Flutter-Unity 通信桥（MethodChannel/EventChannel）
├── Day 3-5: 3D Viewer 场景（相机控制 + 机械动画 + 零件高亮）

Week 2 (Day 5-10):
├── Day 5-8: AR 场景（平面检测 + 放置 + 尺寸叠加 + 门架指示）
├── Day 8-10: Flutter 侧集成（改造 ThreeDViewerPage + ArViewPage）

Week 3 (Day 10-14):
├── Day 10-12: Android/iOS 原生桥接
├── Day 12-14: 3D 模型管线（制作规范 + 上传流程 + 首批模型）

Week 4 (Day 14-18):
├── Day 14-15: 后端 API 扩展
├── Day 15-17: 联调测试（Flutter ↔ Unity ↔ 后端）
├── Day 17-18: 性能优化 + Bug 修复
```

---

## 五、验收标准

| # | 功能 | 验收条件 | 对应章节 |
|---|------|----------|----------|
| 1 | Unity 嵌入 Flutter | Unity 视图正常显示在 Flutter 页面内 | — |
| 2 | 模型加载 | .glb 模型从后端下载并渲染 | 十三 |
| 3 | 360° 旋转 | 单指拖动旋转模型 | 十三 |
| 4 | 缩放 | 双指缩放模型 | 十三 |
| 5 | 门架升降 | 点击按钮，门架动画升降 | 十四 |
| 6 | 门架倾斜 | 点击前倾/后倾，门架角度变化 | 十四 |
| 7 | 货叉升降 | 点击按钮，货叉动画升降 | 十四 |
| 8 | 零件高亮 | 点击零件列表，3D 模型中对应零件高亮 | 十三 |
| 9 | 透明模式 | 切换透明，模型变为半透明 | 二十 |
| 10 | 爆炸图 | 拖动滑块，零件分离 | 二十 |
| 11 | AR 平面检测 | 手机移动检测到地面平面 | 十六 |
| 12 | AR 放置 | 点击确认放置叉车模型 | 十六 |
| 13 | AR 真实尺寸 | 模型按 1:1 真实尺寸显示 | 十七 |
| 14 | AR 尺寸叠加 | 显示长宽高/轴距/转弯半径 | 十八 |
| 15 | AR 门架高度 | 实时显示当前门架高度 | 十九 |
| 16 | Flutter↔Unity 通信 | 双向消息正常传递 | — |
| 17 | 跨平台 | iOS + Android 均可运行 | — |

---

## 六、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| flutter_unity_widget 兼容性 | Unity 视图黑屏/崩溃 | 锁定版本，充分测试；备选方案：全屏 Unity Activity |
| Unity 包体积过大 | App 增加 50-80MB | 使用 AssetBundle 按需下载模型 |
| AR 设备兼容性 | 旧设备不支持 AR | 检测 AR 能力，不支持时降级为 3D 查看 |
| Unity 编辑器 license | 开发成本 | 个人版免费（收入<$100K） |
| 模型制作周期 | 3D 模型耗时 | 首批用简化模型，后续迭代 |
| 热更新 | Unity 代码无法热更 | 关键逻辑放 Flutter/后端，Unity 只做渲染 |

---

## 七、文件变更清单

### 新增文件

```
mobile/
├── lib/core/unity/
│   ├── unity_bridge.dart              # 通信桥
│   └── unity_view_wrapper.dart        # Unity 视图包装

unity/                                  # 全新 Unity 项目
├── Assets/Scripts/
│   ├── Core/
│   │   ├── UnityMessageManager.cs
│   │   ├── ModelLoader.cs
│   │   └── AppManager.cs
│   ├── Viewer/
│   │   ├── CameraController.cs
│   │   ├── AnimationController.cs
│   │   ├── PartHighlighter.cs
│   │   ├── ExplodedView.cs
│   │   └── MeasurementOverlay.cs
│   └── AR/
│       ├── ARPlacementController.cs
│       ├── ARDimensionOverlay.cs
│       ├── ARMastIndicator.cs
│       └── ARRepairGuide.cs
├── Assets/Scenes/
│   ├── ThreeDViewer.unity
│   └── ARView.unity
└── Assets/Shaders/
    ├── PartHighlight.shader
    └── XRayTransparent.shader

mobile/android/app/src/main/kotlin/.../
├── FlutterUnityPlugin.kt
└── UnityPlayerFragment.kt

mobile/ios/Runner/
├── FlutterUnityPlugin.swift
└── UnityUtils.swift
```

### 修改文件

```
mobile/pubspec.yaml                    # 添加 flutter_unity_widget 依赖
mobile/lib/features/threed/threed_viewer_page.dart   # 改用 Unity 视图
mobile/lib/features/ar/ar_view_page.dart             # 改用 Unity AR 视图
mobile/lib/app/router.dart             # 路由不变
backend/app/api/model3d.py             # 新增 full 接口 + 文件服务
```

---

## 八、后续演进

| 版本 | Unity 功能 | 说明 |
|------|-----------|------|
| V1 (本方案) | 3D 查看 + 机械动画 + 基础 AR | 核心 3D/AR 能力 |
| V2 | 拆解动画 + 3D 发动机 + 维修动画 | 完整 3D 交互 |
| V3 | AR 维修指导 + AR 拆装 + 多人协作 | AR 终极形态 |
| V4 | 本地 AI + Unity 推理 | 端侧智能 |
