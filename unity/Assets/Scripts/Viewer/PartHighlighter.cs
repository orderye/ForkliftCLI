using UnityEngine;
using System.Collections.Generic;

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// 零件高亮/透明模式。通过覆盖材质实现。
    /// </summary>
    public class PartHighlighter : MonoBehaviour
    {
        public static PartHighlighter Instance { get; private set; }

        [Header("Materials")]
        public Material highlightMaterial;
        public Material transparentMaterial;

        private Dictionary<int, Renderer[]> _partRenderers = new Dictionary<int, Renderer[]>();
        private Dictionary<Renderer, Material[]> _originalMats = new Dictionary<Renderer, Material[]>();

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        public void RegisterPart(int partId, GameObject partObj)
        {
            var renderers = partObj.GetComponentsInChildren<Renderer>();
            _partRenderers[partId] = renderers;
            foreach (var r in renderers)
                if (!_originalMats.ContainsKey(r))
                    _originalMats[r] = r.sharedMaterials;
        }

        public void Highlight(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.HighlightParam>(jsonData);
            if (!_partRenderers.TryGetValue(p.partId, out var renderers))
            {
                Debug.LogWarning($"[PartHighlighter] 未注册 partId={p.partId}");
                return;
            }

            Color color = Color.yellow;
            if (!string.IsNullOrEmpty(p.color))
                ColorUtility.TryParseHtmlString(p.color, out color);

            foreach (var r in renderers)
            {
                var orig = _originalMats.TryGetValue(r, out var m) ? m : r.sharedMaterials;
                var mats = new Material[orig.Length];
                orig.CopyTo(mats, 0);
                if (highlightMaterial != null)
                {
                    var hl = new Material(highlightMaterial);
                    hl.color = color;
                    if (hl.HasProperty("_EmissionColor"))
                        hl.SetColor("_EmissionColor", color * 0.5f);
                    mats[0] = hl;
                }
                r.sharedMaterials = mats;
            }
        }

        public void Clear()
        {
            foreach (var kvp in _partRenderers)
                foreach (var r in kvp.Value)
                    if (_originalMats.TryGetValue(r, out var m))
                        r.sharedMaterials = m;
        }

        public void SetTransparent(string jsonData)
        {
            var p = JsonUtility.FromJson<Core.TransparentParam>(jsonData);
            foreach (var kvp in _partRenderers)
            {
                foreach (var r in kvp.Value)
                {
                    if (!_originalMats.TryGetValue(r, out var orig)) continue;
                    var mats = new Material[orig.Length];
                    if (p.enabled && transparentMaterial != null)
                    {
                        var tr = new Material(transparentMaterial);
                        tr.color = new Color(0.7f, 0.7f, 0.7f, 0.2f);
                        for (int i = 0; i < mats.Length; i++) mats[i] = tr;
                    }
                    else
                        orig.CopyTo(mats, 0);
                    r.sharedMaterials = mats;
                }
            }
        }
    }
}
