using System.Collections.Generic;
using UnityEngine;

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// partId → 物体名 映射。
    /// 没有装配层级时，Unity 侧至少能按约定名找到零件。
    /// </summary>
    public static class PartMapping
    {
        public static readonly Dictionary<int, string> PartNames = new Dictionary<int, string>
        {
            {1, "Body_Chassis"},
            {2, "Mast_Outer"},
            {3, "Mast_Inner"},
            {4, "Carriage_Fork"},
            {5, "Fork_Left"},
            {6, "Fork_Right"},
            {7, "Counterweight"},
            {8, "Cabin"}
        };

        public static GameObject FindPart(int partId, Transform root)
        {
            if (root == null) return null;
            if (!PartNames.TryGetValue(partId, out var partName)) return null;
            return FindByName(root, partName);
        }

        public static GameObject FindByName(Transform root, string name)
        {
            if (root == null || string.IsNullOrEmpty(name)) return null;
            foreach (Transform child in root.GetComponentsInChildren<Transform>(true))
            {
                if (child.name == name) return child.gameObject;
            }
            return null;
        }

        public static void AutoRegisterAll(PartHighlighter highlighter, Transform root)
        {
            if (highlighter == null || root == null) return;
            foreach (var kv in PartNames)
            {
                var go = FindPart(kv.Key, root);
                if (go != null) highlighter.RegisterPart(kv.Key, go);
            }
        }
    }
}
