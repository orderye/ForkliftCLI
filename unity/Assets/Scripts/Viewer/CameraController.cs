using UnityEngine;

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// Orbit 风格相机：单指旋转、双指缩放、重置视角。
    /// </summary>
    public class CameraController : MonoBehaviour
    {
        public static CameraController Instance { get; private set; }

        [Header("Rotation")]
        public float rotateSpeed = 0.2f;

        [Header("Zoom")]
        public float zoomSpeed = 0.02f;
        public float minDistance = 0.5f;
        public float maxDistance = 15f;

        [Header("References")]
        public Transform pivot;

        private float distance = 4f;
        private float yaw = 45f;
        private float pitch = 25f;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;

            Core.UnityMessageManager.Register("resetView", ResetView);
            Core.UnityMessageManager.Register("setView", SetView);
        }

        void Start()
        {
            if (pivot == null)
            {
                pivot = new GameObject("CameraPivot").transform;
            }
        }

        void LateUpdate()
        {
            HandleTouchInput();
            ApplyTransform();
        }

        void HandleTouchInput()
        {
            if (Input.touchCount == 1)
            {
                var touch = Input.GetTouch(0);
                if (touch.phase == TouchPhase.Moved)
                {
                    yaw += touch.deltaPosition.x * rotateSpeed;
                    pitch -= touch.deltaPosition.y * rotateSpeed;
                    pitch = Mathf.Clamp(pitch, -80f, 80f);
                }
                else if (touch.phase == TouchPhase.Ended)
                {
                    // 单指抬起算一次点击：若点在模型上则回传零件 ID，让 Flutter 能联动零件列表。
                    Ray ray = Camera.main.ScreenPointToRay(touch.position);
                    if (Physics.Raycast(ray, out RaycastHit hit))
                    {
                        var meshRenderer = hit.collider.GetComponentInParent<MeshRenderer>();
                        if (meshRenderer != null)
                        {
                            string partName = meshRenderer.gameObject.name;
                            Core.UnityMessageManager.Instance?.SendToFlutter("onPartClicked",
                                $"{{\"partName\":\"{Escape(partName)}\",\"partId\":{partName.GetHashCode()}}}");
                        }
                    }
                }
            }
            else if (Input.touchCount == 2)
            {
                var t0 = Input.GetTouch(0);
                var t1 = Input.GetTouch(1);
                float prevDist = ((t0.position - t0.deltaPosition) - (t1.position - t1.deltaPosition)).magnitude;
                float currDist = (t0.position - t1.position).magnitude;
                distance += (prevDist - currDist) * zoomSpeed;
                distance = Mathf.Clamp(distance, minDistance, maxDistance);
            }
        }

        private static string Escape(string s) =>
            s?.Replace("\\", "\\\\").Replace("\"", "\\\"") ?? "";

        void ApplyTransform()
        {
            Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
            Vector3 position = pivot.position - rotation * Vector3.forward * distance;
            transform.SetPositionAndRotation(position, rotation);
        }

        public void ResetView()
        {
            yaw = 45f;
            pitch = 25f;
            distance = 4f;
        }

        public void ResetView(string _)
        {
            ResetView();
        }

        /// <summary>手动设置视角：{"yaw":45,"pitch":25,"distance":4}</summary>
        public void SetView(string jsonData)
        {
            if (string.IsNullOrEmpty(jsonData)) return;
            var p = JsonUtility.FromJson<ViewParam>(jsonData);
            if (p == null) return;
            if (!float.IsNaN(p.yaw)) yaw = p.yaw;
            if (!float.IsNaN(p.pitch)) pitch = Mathf.Clamp(p.pitch, -80f, 80f);
            if (p.distance > 0) distance = Mathf.Clamp(p.distance, minDistance, maxDistance);
        }

        [System.Serializable]
        private class ViewParam
        {
            public float yaw;
            public float pitch;
            public float distance;
        }
    }
}
