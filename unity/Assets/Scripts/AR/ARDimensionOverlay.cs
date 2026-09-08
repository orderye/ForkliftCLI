using UnityEngine;

namespace ForkliftBao.AR
{
    /// <summary>
    /// AR 场景尺寸叠加：长/宽/高/轴距/转弯半径/占地面积。
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

        private Core.ArConfigData _config;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        public void Show()
        {
            ShowInternal(true);
        }

        public void Show(string _)
        {
            ShowInternal(true);
        }

        void ShowInternal(bool show)
        {
            if (lengthText != null) lengthText.gameObject.SetActive(show);
            if (lengthLine != null) lengthLine.gameObject.SetActive(show);
            if (widthLine != null) widthLine.gameObject.SetActive(show);
            if (turningCircle != null) turningCircle.gameObject.SetActive(show);
        }

        public void Init(Core.ArConfigData config, Transform modelTransform)
        {
            _config = config;
            if (config == null) return;

            if (lengthText != null) lengthText.text = $"长: {config.real_length_mm / 1000f:F2}m";
            if (widthText != null) widthText.text = $"宽: {config.real_width_mm / 1000f:F2}m";
            if (heightText != null) heightText.text = $"高: {config.real_height_mm / 1000f:F2}m";
            if (wheelbaseText != null) wheelbaseText.text = $"轴距: {config.real_wheelbase_mm / 1000f:F2}m";
            if (areaText != null) areaText.text = $"面积: {(config.real_length_mm * config.real_width_mm / 1000000f):F2}m²";

            if (lengthLine != null)
            {
                lengthLine.positionCount = 2;
                lengthLine.SetPosition(0, modelTransform.position + Vector3.forward * (config.real_length_mm / 2000f));
                lengthLine.SetPosition(1, modelTransform.position - Vector3.forward * (config.real_length_mm / 2000f));
            }

            if (turningCircle != null)
            {
                int segments = 64;
                turningCircle.positionCount = segments + 1;
                float r = config.real_turning_radius_mm / 1000f;
                for (int i = 0; i <= segments; i++)
                {
                    float angle = i * 2f * Mathf.PI / segments;
                    turningCircle.SetPosition(i, modelTransform.position + new Vector3(Mathf.Cos(angle) * r, 0.01f, Mathf.Sin(angle) * r));
                }
            }
        }
    }
}
