using UnityEngine;

namespace ForkliftBao.AR
{
    /// <summary>
    /// AR 场景尺寸叠加：长/宽/高/轴距/转弯半径/占地面积。
    /// 所有长度按 1:1 真实尺寸绘制（单位：米），因此与放在真实世界里的叉车一致。
    /// </summary>
    public class ARDimensionOverlay : MonoBehaviour
    {
        public static ARDimensionOverlay Instance { get; private set; }

        public TMPro.TextMeshProUGUI lengthText;
        public TMPro.TextMeshProUGUI widthText;
        public TMPro.TextMeshProUGUI heightText;
        public TMPro.TextMeshProUGUI wheelbaseText;
        public TMPro.TextMeshProUGUI areaText;

        public LineRenderer lengthLine;
        public LineRenderer widthLine;
        public LineRenderer turningCircle;

        /// <summary>标注线抬离地面的高度（米），避免与 AR 平面发生 Z-fighting。</summary>
        public float overlayHeight = 0.005f;

        /// <summary>LineRenderer 线宽（世界空间米），AR 下太小看不见。</summary>
        public float lineThickness = 0.02f;

        private Core.ArConfigData _config;
        private bool _shown;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;

            Core.UnityMessageManager.Register("showARDimensions", Show);
            Core.UnityMessageManager.Register("hideARDimensions", Hide);

            if (lengthLine != null) ConfigLine(lengthLine);
            if (widthLine != null) ConfigLine(widthLine);
            if (turningCircle != null) ConfigLine(turningCircle);
        }

        private void ConfigLine(LineRenderer line)
        {
            line.startWidth = lineThickness;
            line.endWidth = lineThickness;
            line.alignment = LineAlignment.View;
            if (line.material == null)
            {
                line.material = new Material(Shader.Find("Sprites/Default"))
                { color = new Color(0f, 0.85f, 1f, 1f) };
            }
        }

        /// <summary>
        /// Flutter 侧的 showARDimensions 带 {"show": true|false} 参数，
        /// 单参重载同时作为开关和兼容旧调用（无参 Show()）。
        /// </summary>
        public void Show(string jsonData)
        {
            var p = string.IsNullOrEmpty(jsonData) ? null : JsonUtility.FromJson<Core.ShowDimParam>(jsonData);
            if (p == null) { ShowInternal(true); return; }
            ShowInternal(p.show);
        }

        /// <summary>兼容 ConfirmPlacement 之类的无参调用。</summary>
        public void Show()
        {
            ShowInternal(true);
        }

        public void Hide()
        {
            ShowInternal(false);
        }

        /// <summary>兼容注册表中以 string 传入的空调用。</summary>
        public void Hide(string _)
        {
            ShowInternal(false);
        }

        void ShowInternal(bool show)
        {
            _shown = show;
            if (lengthText != null) lengthText.gameObject.SetActive(show);
            if (widthText != null) widthText.gameObject.SetActive(show);
            if (heightText != null) heightText.gameObject.SetActive(show);
            if (wheelbaseText != null) wheelbaseText.gameObject.SetActive(show);
            if (areaText != null) areaText.gameObject.SetActive(show);
            if (lengthLine != null) lengthLine.gameObject.SetActive(show);
            if (widthLine != null) widthLine.gameObject.SetActive(show);
            if (turningCircle != null) turningCircle.gameObject.SetActive(show);
        }

        /// <summary>
        /// 用后端返回的真实尺寸（mm）生成文本与标注线。
        /// </summary>
        public void Init(Core.ArConfigData config, Transform modelTransform)
        {
            _config = config;
            if (config == null || modelTransform == null) return;

            float scale = config.ScaleFactor;
            float lengthM = config.real_length_mm / 1000f * scale;
            float widthM = config.real_width_mm / 1000f * scale;
            float heightM = config.real_height_mm / 1000f * scale;
            float wheelbaseM = config.real_wheelbase_mm / 1000f * scale;
            float turningRadiusM = config.real_turning_radius_mm / 1000f * scale;

            if (lengthText != null) lengthText.text = $"长: {lengthM:F2}m";
            if (widthText != null) widthText.text = $"宽: {widthM:F2}m";
            if (heightText != null) heightText.text = $"高: {heightM:F2}m";
            if (wheelbaseText != null) wheelbaseText.text = $"轴距: {wheelbaseM:F2}m";
            if (areaText != null)
                areaText.text = $"占地: {(lengthM * widthM):F2}m²";

            Vector3 origin = modelTransform.position + Vector3.up * overlayHeight;

            if (lengthLine != null)
            {
                lengthLine.positionCount = 2;
                // 长边沿 forward 方向，从 -半长 到 +半长。
                lengthLine.SetPosition(0, origin + Vector3.forward * (lengthM * 0.5f));
                lengthLine.SetPosition(1, origin - Vector3.forward * (lengthM * 0.5f));
            }

            if (widthLine != null)
            {
                widthLine.positionCount = 2;
                widthLine.SetPosition(0, origin + Vector3.right * (widthM * 0.5f));
                widthLine.SetPosition(1, origin - Vector3.right * (widthM * 0.5f));
            }

            if (turningCircle != null)
            {
                int segments = 64;
                turningCircle.positionCount = segments + 1;
                for (int i = 0; i <= segments; i++)
                {
                    float angle = i * 2f * Mathf.PI / segments;
                    turningCircle.SetPosition(i,
                        origin + new Vector3(Mathf.Cos(angle) * turningRadiusM, 0f, Mathf.Sin(angle) * turningRadiusM));
                }
            }

            if (!_shown) ShowInternal(true);
        }

        /// <summary>供诊断：当前配置的转弯半径（米）。</summary>
        public float TurningRadiusM =>
            _config == null ? 0f : _config.real_turning_radius_mm / 1000f * _config.ScaleFactor;
    }
}
