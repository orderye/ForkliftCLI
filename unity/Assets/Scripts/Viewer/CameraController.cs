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
    }
}
