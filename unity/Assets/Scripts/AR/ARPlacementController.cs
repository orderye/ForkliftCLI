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
        private Pose _lastValidPose;
        private List<ARRaycastHit> _hits = new List<ARRaycastHit>();

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
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
            Debug.Log($"[ARPlacementController] Enter modelId={p.modelId}");
            if (modelContainer != null && p.arConfig != null)
            {
                modelContainer.localScale = Vector3.one * 0.001f; // mm → m
            }
            Core.UnityMessageManager.Instance.SendToFlutter("onARSessionReady", "{}");
        }

        public void ConfirmPlacement()
        {
            _isPlaced = true;
            if (modelContainer != null)
                modelContainer.position = _lastValidPose.position;
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
            if (modelContainer != null)
                modelContainer.localScale = Vector3.one * Mathf.Max(p.factor, 0.0001f);
        }

        public void Reposition()
        {
            _isPlaced = false;
            if (modelContainer != null)
                modelContainer.gameObject.SetActive(false);
        }
    }
}
