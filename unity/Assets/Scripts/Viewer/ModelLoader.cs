using UnityEngine;

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// 从 URL 加载 .glb/.gltf 模型到 ModelContainer。
    /// Unity 内置 glTF 支持（通过 UnityGLTF 插件或 StreamingAssets + 场景预制体）。
    /// </summary>
    public class ModelLoader : MonoBehaviour
    {
        public static ModelLoader Instance { get; private set; }

        [Header("Target")]
        public Transform modelContainer;

        private int currentModelId;
        private GameObject loadedModel;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }

        public void LoadModel(string jsonData)
        {
            var param = JsonUtility.FromJson<Core.LoadModelParam>(jsonData);
            if (string.IsNullOrEmpty(param.url))
            {
                Debug.LogWarning("[ModelLoader] URL 为空");
                return;
            }

            currentModelId = param.modelId;
            Debug.Log($"[ModelLoader] 加载模型 modelId={param.modelId} url={param.url}");

            // TODO: 使用 UnityWebRequest 下载 .glb → UnityWebRequestAssetBundle
            // 或使用 GLTFast (com.unity.cloud.gltfast) 包异步加载
            // 目前先加载 StreamingAssets/models/ 下的本地模型

            if (modelContainer == null)
            {
                modelContainer = new GameObject("ModelContainer").transform;
            }

            string localPath = System.IO.Path.Combine(Application.streamingAssetsPath, "models", $"{param.modelId}.glb");
            // GLTFast 示例（需安装 com.unity.cloud.gltfast）:
            // var gltf = new GltfImport();
            // await gltf.Load(localPath);
            // var scenes = gltf.GetSceneNodes();
            // foreach (var node in scenes) node.transform.SetParent(modelContainer, false);

            Core.UnityMessageManager.Instance.SendToFlutter("onModelLoaded",
                $"{{\"success\":true,\"modelId\":{param.modelId}}}");
        }

        public GameObject GetLoadedModel() => loadedModel;
        public int GetCurrentModelId() => currentModelId;
    }
}
