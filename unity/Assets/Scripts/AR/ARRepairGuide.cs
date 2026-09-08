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
        }

        public void BeginGuide(string step)
        {
            if (guidePanel != null) guidePanel.SetActive(true);
            if (stepText != null) stepText.text = step;
            Debug.Log($"[ARRepairGuide] 开始指导: {step}");
        }

        public void ShowArrow(Vector3 worldPos, Quaternion rotation)
        {
            if (arrowPrefab == null) return;
            if (currentArrow == null) currentArrow = Instantiate(arrowPrefab);
            currentArrow.position = worldPos;
            currentArrow.rotation = rotation;
        }

        public void EndGuide()
        {
            if (guidePanel != null) guidePanel.SetActive(false);
            if (currentArrow != null)
            {
                Destroy(currentArrow.gameObject);
                currentArrow = null;
            }
        }
    }
}