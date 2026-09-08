using UnityEngine;

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// 最小场景挂接器。
    /// 把模型根节点和控制脚本接起来。
    /// </summary>
    public class SceneBootstrap : MonoBehaviour
    {
        [Header("Model")]
        public Transform modelContainer;

        [Header("Auto-link")]
        public bool autoLinkOnStart = true;

        void Start()
        {
            if (autoLinkOnStart) Link();
        }

        public void Link()
        {
            if (modelContainer == null)
            {
                Debug.LogWarning("[SceneBootstrap] modelContainer 为空");
                return;
            }

            var ac = FindObjectOfType<AnimationController>();
            if (ac == null)
            {
                var go = new GameObject("AnimationController");
                ac = go.AddComponent<AnimationController>();
            }

            ac.mastInner = PartMapping.FindPart(3, modelContainer);
            ac.mastOuter = PartMapping.FindPart(2, modelContainer)?.transform;
            ac.fork = PartMapping.FindPart(4, modelContainer)?.transform;
            ac.mastAssembly = ac.mastOuter != null ? ac.mastOuter : modelContainer;

            var ph = FindObjectOfType<PartHighlighter>();
            if (ph != null)
            {
                PartMapping.AutoRegisterAll(ph, modelContainer);
            }
        }
    }
}