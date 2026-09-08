using UnityEngine;
using System.Collections.Generic;

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// 爆炸图：按指定方向和距离分离零件。
    /// </summary>
    public class ExplodedView : MonoBehaviour
    {
        public static ExplodedView Instance { get; private set; }

        [System.Serializable]
        public class PartExplosion
        {
            public Transform part;
            public Vector3 originalPos;
            public Vector3 explodeDirection;
            public float explodeDistance;
        }

        public List<PartExplosion> parts = new List<PartExplosion>();
        public float defaultDistance = 1.5f;

        private float _currentProgress = 0f;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        void Start()
        {
            AutoCollectParts();
        }

        void AutoCollectParts()
        {
            if (parts.Count > 0) return;
            foreach (Transform child in GetComponentsInChildren<Transform>(true))
            {
                if (child == transform) continue;
                parts.Add(new PartExplosion
                {
                    part = child,
                    originalPos = child.localPosition,
                    explodeDirection = (child.localPosition - transform.position).normalized,
                    explodeDistance = defaultDistance
                });
            }
        }

        public void SetProgress(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.ExplodedParam>(jsonData);
            _currentProgress = Mathf.Clamp01(p.progress);
            foreach (var entry in parts)
            {
                if (entry.part == null) continue;
                entry.part.localPosition = entry.originalPos + entry.explodeDirection * entry.explodeDistance * _currentProgress;
            }
        }
    }
}
