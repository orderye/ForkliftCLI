using UnityEngine;

namespace ForkliftBao.Core
{
    /// <summary>
    /// 全局管理器：保持 UnityMessageManager 在所有场景中存在。
    /// </summary>
    public class AppManager : MonoBehaviour
    {
        void Awake()
        {
            if (FindObjectOfType<UnityMessageManager>() == null)
            {
                var go = new GameObject("UnityMessageManager");
                go.AddComponent<UnityMessageManager>();
            }
        }
    }
}
