using UnityEngine;

namespace ForkliftBao.AR
{
    /// <summary>
    /// V3: AR 维修指导。在真实叉车上叠加箭头和文字提示。
    /// </summary>
    public class ARRepairGuide : MonoBehaviour
    {
        public static ARRepairGuide Instance { get; private set; }

        [Header("UI")]
        public Transform arrowPrefab;
        public TMPro.TextMeshProUGUI stepText;
        public GameObject guidePanel;

        private Transform currentArrow;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            if (guidePanel != null) guidePanel.SetActive(false);

            Core.UnityMessageManager.Register("beginARGuide", BeginGuide);
            Core.UnityMessageManager.Register("endARGuide", EndGuide);
        }

        /// <summary>
        /// Flutter 侧调用：{"step":"第一步：打开前盖","anchor":{"x":1.2,"y":0.4,"z":0.8}}
        /// </summary>
        public void BeginGuide(string jsonData)
        {
            var p = string.IsNullOrEmpty(jsonData) ? null : JsonUtility.FromJson<GuideStepParam>(jsonData);
            string step = p != null ? p.step : "";
            if (string.IsNullOrEmpty(step))
            {
                Debug.LogWarning("[ARRepairGuide] BeginGuide 缺少 step 字段");
                Core.UnityMessageManager.Instance?.SendToFlutter("onError",
                    "{\"message\":\"缺少 step 字段\",\"method\":\"beginARGuide\"}");
                return;
            }

            if (guidePanel != null) guidePanel.SetActive(true);
            if (stepText != null) stepText.text = step;
            Debug.Log($"[ARRepairGuide] 开始指导: {step}");

            if (p != null && p.anchor != null && arrowPrefab != null)
                PlaceArrow(p.anchor.x, p.anchor.y, p.anchor.z);

            Core.UnityMessageManager.Instance?.SendToFlutter("onARGuideStep",
                $"{{\"step\":\"{Escape(step)}\"}}");
        }

        private void PlaceArrow(float x, float y, float z)
        {
            if (arrowPrefab == null) return;
            if (currentArrow == null) currentArrow = Instantiate(arrowPrefab);
            currentArrow.position = new Vector3(x, y, z);
        }

        public void ShowArrow(Vector3 worldPos, Quaternion rotation)
        {
            if (arrowPrefab == null) return;
            if (currentArrow == null) currentArrow = Instantiate(arrowPrefab);
            currentArrow.position = worldPos;
            currentArrow.rotation = rotation;
        }

        public void EndGuide(string _)
        {
            EndGuideInternal();
        }

        public void EndGuide()
        {
            EndGuideInternal();
        }

        private void EndGuideInternal()
        {
            if (guidePanel != null) guidePanel.SetActive(false);
            if (currentArrow != null)
            {
                Destroy(currentArrow.gameObject);
                currentArrow = null;
            }
            Core.UnityMessageManager.Instance?.SendToFlutter("onARGuideEnded", "{}");
        }

        private static string Escape(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"")
                    .Replace("\n", "\\n").Replace("\r", "");
        }

        [System.Serializable]
        private class GuideStepParam
        {
            public string step;
            public Vector3 anchor;
        }
    }
}