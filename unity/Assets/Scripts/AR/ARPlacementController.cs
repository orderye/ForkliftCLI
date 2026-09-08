using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;
using System.Collections.Generic;

namespace ForkliftBao.AR
{
    /// <summary>
    /// AR 平面检测与模型放置。使用 ARFoundation。
    /// </summary>
    public class ARPlacementController : MonoBehaviour
    {
        public static ARPlacementController Instance { get; private set; }

        [Header("AR Components")]
        public ARRaycastManager raycastManager;
        public ARPlaneManager planeManager;
        public Transform modelContainer;

        private bool _isPlaced = false;
        private bool _lastValidPoseIsSet = false;
        private Pose _lastValidPose;
        private List<ARRaycastHit> _hits = new List<ARRaycastHit>();
        private Core.ArConfigData _enteredConfig;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;

            Core.UnityMessageManager.Register("enterAR", Enter);
            Core.UnityMessageManager.Register("confirmARPlacement", ConfirmPlacement);
            Core.UnityMessageManager.Register("setARScale", SetScale);
            Core.UnityMessageManager.Register("repositionAR", Reposition);
        }

        void Update()
        {
            if (_isPlaced) return;
            TryUpdatePreviewPose();
        }

        void TryUpdatePreviewPose()
        {
            if (raycastManager == null) return;

            Vector2 screenCenter = new Vector2(Screen.width / 2f, Screen.height / 2f);
            if (raycastManager.Raycast(screenCenter, _hits, TrackableType.PlaneWithinPolygon))
            {
                _lastValidPose = _hits[0].pose;
                if (!_lastValidPoseIsSet)
                {
                    // 首次命中平面时通知 Flutter，让它显示"点击放置"提示。
                    _lastValidPoseIsSet = true;
                    Core.UnityMessageManager.Instance?.SendToFlutter("onARPlaneDetected", "{}");
                }
                if (modelContainer != null)
                {
                    modelContainer.position = _lastValidPose.position;
                    modelContainer.rotation = _lastValidPose.rotation;
                    modelContainer.gameObject.SetActive(true);
                }
            }
        }

        public void Enter(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.EnterARParam>(jsonData);
            if (p == null)
            {
                Debug.LogError("[ARPlacementController] Enter 参数解析失败");
                return;
            }

            Debug.Log($"[ARPlacementController] Enter modelId={p.modelId}");

            _enteredConfig = p.arConfig;
            _lastValidPoseIsSet = false;

            // mm → m。scale_factor 由后端给出，缺省 1.0（1:1 真实尺寸）。
            float scaleMm = p.arConfig != null && p.arConfig.scaleFactor != 0f
                ? p.arConfig.scaleFactor
                : 1f;
            if (modelContainer != null)
            {
                modelContainer.localScale = Vector3.one * (0.001f * scaleMm);
                modelContainer.gameObject.SetActive(false); // 等 raycast 命中再显示
            }

            Core.UnityMessageManager.Instance.SendToFlutter("onARSessionReady", "{}");
        }

        public void ConfirmPlacement()
        {
            if (!_lastValidPoseIsSet)
            {
                Debug.LogWarning("[ARPlacementController] 尚未检测到平面，无法放置");
                Core.UnityMessageManager.Instance.SendToFlutter("onError",
                    "{\"message\":\"未检测到AR平面\",\"method\":\"confirmARPlacement\"}");
                return;
            }

            _isPlaced = true;
            if (modelContainer != null)
            {
                modelContainer.position = _lastValidPose.position;
                modelContainer.rotation = _lastValidPose.rotation;
            }

            // 把真实尺寸配置交给尺寸叠加层，由它绘制标注与地面线。
            ARDimensionOverlay.Instance?.Init(_enteredConfig, modelContainer);
            ARDimensionOverlay.Instance?.Show();

            Core.UnityMessageManager.Instance.SendToFlutter("onARPlaced", "{}");
        }

        public void ConfirmPlacement(string _)
        {
            ConfirmPlacement();
        }

        public void SetScale(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.ScaleParam>(jsonData);
            if (p == null) return;
            if (modelContainer != null)
                modelContainer.localScale = Vector3.one * Mathf.Max(p.factor * 0.001f, 0.0001f);
        }

        public void Reposition()
        {
            _isPlaced = false;
            _lastValidPoseIsSet = false;
            if (modelContainer != null)
                modelContainer.gameObject.SetActive(false);
            ARDimensionOverlay.Instance?.Hide();
        }
    }
}
