using UnityEngine;

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// 控制门架升降/货叉升降/门架倾斜/车轮转向。
    /// 通过 Transform 直接控制（无骨骼要求）。
    /// </summary>
    public class AnimationController : MonoBehaviour
    {
        public static AnimationController Instance { get; private set; }

        [Header("门架")]
        public Transform mastInner;
        public Transform mastOuter;
        public Transform fork;
        public float mastMaxHeight = 4.5f;
        public float mastMinHeight = 1.8f;

        [Header("倾斜")]
        public Transform mastAssembly;
        public float maxTiltForward = 6f;
        public float maxTiltBackward = 12f;

        [Header("转向")]
        public Transform rearWheel;
        public float maxSteerAngle = 30f;

        private float currentMastHeight = 1.8f;
        private float currentTiltAngle = 0f;
        private Animator animator;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        void Start()
        {
            animator = GetComponentInChildren<Animator>();
        }

        public void Play(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.PlayAnimParam>(jsonData);
            if (animator != null)
            {
                animator.speed = p.speed <= 0 ? 1f : p.speed;
                animator.Play(p.name);
            }
            Core.UnityMessageManager.Instance.SendToFlutter("onAnimationComplete", $"{{\"name\":\"{p.name}\"}}");
        }

        public void Stop(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.PlayAnimParam>(jsonData);
            if (animator != null)
            {
                animator.SetFloat("Speed", 0f);
                if (!string.IsNullOrEmpty(p.name)) animator.Play(p.name, 0, 0f);
                animator.Update(0f);
                animator.speed = 0f;
            }
        }

        public void SetMastHeight(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.MastParam>(jsonData);
            currentMastHeight = Mathf.Clamp(p.heightMm / 1000f, mastMinHeight, mastMaxHeight);
            float t = (currentMastHeight - mastMinHeight) / (mastMaxHeight - mastMinHeight);

            if (mastInner != null)
                mastInner.localPosition = new Vector3(mastInner.localPosition.x, t * 1.5f, mastInner.localPosition.z);
            if (fork != null)
                fork.localPosition = new Vector3(fork.localPosition.x, t * 2.7f, fork.localPosition.z);

            Core.UnityMessageManager.Instance.SendToFlutter("onMastHeightChanged",
                $"{{\"heightMm\":{currentMastHeight * 1000f}}}");
        }

        public void SetTiltAngle(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.TiltParam>(jsonData);
            currentTiltAngle = Mathf.Clamp(p.angle, -maxTiltForward, maxTiltBackward);
            if (mastAssembly != null)
                mastAssembly.localRotation = Quaternion.Euler(currentTiltAngle, 0f, 0f);
        }

        public void SetSteerAngle(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.SteerParam>(jsonData);
            float angle = Mathf.Clamp(p.angle, -maxSteerAngle, maxSteerAngle);
            if (rearWheel != null)
                rearWheel.localRotation = Quaternion.Euler(0f, angle, 0f);
        }

        public float GetCurrentHeight() => currentMastHeight;
        public float GetCurrentTilt() => currentTiltAngle;
    }
}
