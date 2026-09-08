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

            Core.UnityMessageManager.Register("playAnimation", Play);
            Core.UnityMessageManager.Register("stopAnimation", Stop);
            Core.UnityMessageManager.Register("setMastHeight", SetMastHeight);
            Core.UnityMessageManager.Register("setTiltAngle", SetTiltAngle);
            Core.UnityMessageManager.Register("setSteerAngle", SetSteerAngle);
        }

        void Start()
        {
            animator = GetComponentInChildren<Animator>();
        }

        public void Play(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.PlayAnimParam>(jsonData);
            if (p == null) return;
            bool played = false;
            if (animator != null)
            {
                animator.speed = p.speed <= 0 ? 1f : p.speed;
                played = animator.Play(p.name);
            }
            else if (mastAssembly != null)
            {
                // 无 Animator 时的降级：名称关键字直接驱动机械结构。
                played = PlayByNameFallback(p.name);
            }

            string status = played ? "ok" : "missing";
            Core.UnityMessageManager.Instance.SendToFlutter("onAnimationComplete",
                $"{{\"name\":\"{p.name}\",\"status\":\"{status}\"}}");
        }

        /// <summary>
        /// 没有 Animator 时按动画名字关键字驱动门架/货叉/倾斜。
        /// 让 3D 交互在未制作动画剪辑前仍然可用。
        /// </summary>
        private bool PlayByNameFallback(string name)
        {
            if (string.IsNullOrEmpty(name)) return false;
            switch (name.ToLowerInvariant())
            {
                case "mast_up":
                    SetMastHeight(MastJson(mastMaxHeight));
                    return true;
                case "mast_down":
                    SetMastHeight(MastJson(mastMinHeight));
                    return true;
                case "tilt_forward":
                    SetTiltAngle(TiltJson(maxTiltForward));
                    return true;
                case "tilt_backward":
                    SetTiltAngle(TiltJson(-maxTiltBackward));
                    return true;
            }
            Debug.LogWarning($"[AnimationController] 未识别的动画名: {name}");
            return false;
        }

        private static string MastJson(float heightM) =>
            $"{{\"heightMm\":{heightM * 1000f}}}";

        private static string TiltJson(float angle) =>
            $"{{\"angle\":{angle}}}";

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
            if (p == null) return;
            currentMastHeight = Mathf.Clamp(p.heightMm / 1000f, mastMinHeight, mastMaxHeight);
            float range = Mathf.Max(mastMaxHeight - mastMinHeight, 0.0001f);
            float t = (currentMastHeight - mastMinHeight) / range;

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
            if (p == null) return;
            currentTiltAngle = Mathf.Clamp(p.angle, -maxTiltForward, maxTiltBackward);
            if (mastAssembly != null)
                mastAssembly.localRotation = Quaternion.Euler(currentTiltAngle, 0f, 0f);
        }

        public void SetSteerAngle(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.SteerParam>(jsonData);
            if (p == null) return;
            float angle = Mathf.Clamp(p.angle, -maxSteerAngle, maxSteerAngle);
            if (rearWheel != null)
                rearWheel.localRotation = Quaternion.Euler(0f, angle, 0f);
        }

        public float GetCurrentHeight() => currentMastHeight;
        public float GetCurrentTilt() => currentTiltAngle;
    }
}
