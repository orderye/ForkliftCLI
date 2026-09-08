using System;
using System.IO;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
#if FORKLIFT_GLTFAST
using GLTFast;
#endif

namespace ForkliftBao.Viewer
{
    /// <summary>
    /// 从 URL 加载 .glb/.gltf 模型到 modelContainer。
    ///
    /// 依赖 com.unity.cloud.gltfast 包（见 Packages/manifest.json）。
    /// 装上后编译时定义 FORKLIFT_GLTFAST，走真正的异步解析导入；
    /// 未安装时降级为「下载并缓存到 StreamingAssets/models/」，
    /// 保证桥接链路可跑通、错误可回传，而不是静默假装成功。
    /// </summary>
    public class ModelLoader : MonoBehaviour
    {
        public static ModelLoader Instance { get; private set; }

        [Header("Target")]
        public Transform modelContainer;

        [Header("Cache")]
        [Tooltip("下载到 StreamingAssets 之外时改用 persistentDataPath，避免打包后只读。")]
        public bool cacheInPersistentData = true;

        [Header("Timeout")]
        public float downloadTimeoutSeconds = 60f;

        private int currentModelId;
        private string currentModelName = "";
        private GameObject loadedRoot;
        private bool _loading;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            Core.UnityMessageManager.Register("loadModel", LoadModel);
            Core.UnityMessageManager.Register("clearModel", ClearModel);
        }

        /// <summary>
        /// 入口：接收 {"url": "...", "modelId": 1}。
        /// </summary>
        public void LoadModel(string jsonData)
        {
            var param = JsonUtility.FromJson<Core.LoadModelParam>(jsonData);
            if (param == null || string.IsNullOrEmpty(param.url))
            {
                Debug.LogWarning("[ModelLoader] URL 为空，忽略");
                SendError("模型 URL 为空", "loadModel");
                return;
            }

            if (_loading)
            {
                Debug.LogWarning("[ModelLoader] 已有加载任务进行中，忽略本次请求");
                return;
            }

            currentModelId = param.modelId;
            currentModelName = param.url;
            Debug.Log($"[ModelLoader] 开始加载 modelId={param.modelId} url={param.url}");

            // 清掉旧模型，避免叠加。
            DestroyLoadedModel();

            EnsureContainer();

            _loading = true;
            StartCoroutine(LoadRoutine(param));
        }

        public void ClearModel(string _)
        {
            DestroyLoadedModel();
            SendEvent("onModelCleared", "{}");
        }

        private IEnumerator LoadRoutine(Core.LoadModelParam param)
        {
            string url = param.url;

            UnityWebRequest request = UnityWebRequestAssetBundle.GetAssetBundle(url);
            request.timeout = Mathf.Max(1, (int)downloadTimeoutSeconds);

            yield return request.SendWebRequest();

            bool failed = false;
#if UNITY_2020_1_OR_NEWER
            failed = request.result != UnityWebRequest.Result.Success;
#else
            failed = request.isNetworkError || request.isHttpError;
#endif
            if (failed)
            {
                _loading = false;
                string detail = $"HTTP {request.responseCode}: {request.error}";
                Debug.LogError($"[ModelLoader] 下载失败 {url} -> {detail}");
                SendError(detail, "loadModel");
                yield break;
            }

            byte[] data = request.downloadHandler.data;
            request.Dispose();

            try
            {
                string cachePath = null;
                GameObject root = ImportModel(data, url, out cachePath);
                if (root == null)
                {
                    _loading = false;
                    string msg = cachePath != null
                        ? $"已缓存到 {cachePath}，但未安装 com.unity.cloud.gltfast，无法解析 glTF"
                        : "模型解析失败：格式不受支持或内容为空";
                    SendError(msg, "loadModel");
                    yield break;
                }

                loadedRoot = root;
                root.transform.SetParent(modelContainer, false);
                NormalizeScale(root);

                _loading = false;
                SendEvent("onModelLoaded",
                    $"{{\"success\":true,\"modelId\":{currentModelId},\"bytes\":{data.Length}," +
                    $"\"rendererCount\":{renderersCount(loadedRoot)}}}");
            }
            catch (Exception ex)
            {
                _loading = false;
                Debug.LogError($"[ModelLoader] 导入异常: {ex}");
                SendError($"模型导入失败: {ex.Message}", "loadModel");
            }
        }

        /// <summary>
        /// 把原始字节解析成 Unity GameObject。
        /// 返回 null 表示无法显示模型，此时 cachePath 给出诊断信息。
        /// </summary>
        private GameObject ImportModel(byte[] data, string url, out string cachePath)
        {
            cachePath = null;
            if (data == null || data.Length == 0) return null;

#if FORKLIFT_GLTFAST
            return ImportWithGltfast(data, url, out cachePath);
#else
            return ImportFallback(data, url, out cachePath);
#endif
        }

#if FORKLIFT_GLTFAST
        /// <summary>
        /// GLTFast 异步导入：解析 glTF/GLB → MeshRenderer / Animator / SkinnedMeshRenderer。
        /// 这是唯一的正确路径；缺包时应装包而不是长期依赖降级分支。
        /// </summary>
        private GameObject ImportWithGltfast(byte[] data, string url, out string cachePath)
        {
            string dir = TemporaryFolder;
            if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);

            string path = Path.Combine(dir, FileWithoutExt(url) + ".glb");
            File.WriteAllBytes(path, data);
            cachePath = path;

            var importer = new GltfImport();
            var result = importer.Load(path);
            if (!result.IsSuccess)
            {
                Debug.LogError($"[ModelLoader] GLTFast 解析失败: {result.Error}");
                return null;
            }

            importer.FinalizeMeshes();

            Transform scene = importer.GetSceneRootNode();
            if (scene == null) return null;

            GameObject root = new GameObject("Model_" + currentModelId);
            scene.SetParent(root.transform, false);
            importer.Parent = root.transform;
            importer.FinalizeNodes();

            return root;
        }

        private static string TemporaryFolder =>
            Path.Combine(Application.temporaryCachePath, "forklift_cli_3d");
#else
        /// <summary>
        /// 降级分支：没有 GLTFast 时无法解析 glTF，把字节落到缓存目录并提示装包。
        /// 目的：让链路可诊断，而不是像旧版本那样谎报加载成功。
        /// </summary>
        private GameObject ImportFallback(byte[] data, string url, out string cachePath)
        {
            string dir = cacheInPersistentData
                ? Application.persistentDataPath
                : Application.streamingAssetsPath;
            dir = Path.Combine(dir, "models");
            if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);

            string filename = $"{currentModelId}_{FileWithoutExt(url)}.{ExtensionOf(url)}";
            cachePath = Path.Combine(dir, filename);
            File.WriteAllBytes(cachePath, data);

            Debug.LogWarning($"[ModelLoader] 已缓存 {cachePath}（{data.Length} bytes），" +
                             "但未安装 com.unity.cloud.gltfast，无法解析 glTF，模型不会显示。");
            return null;
        }
#endif

        private static int renderersCount(GameObject root)
        {
            return root == null ? 0 : root.GetComponentsInChildren<Renderer>().Length;
        }

        private static string FileWithoutExt(string url)
        {
            string name = Path.GetFileNameWithoutExtension(new Uri(url).ToString());
            return name.Length > 0 ? name : "model";
        }

        private static string ExtensionOf(string url)
        {
            string ext = Path.GetExtension(new Uri(url).ToString());
            return string.IsNullOrEmpty(ext) ? "glb" : ext.Substring(1).ToLowerInvariant();
        }

        /// <summary>
        /// 把模型归一到合理尺寸：按包围盒最长边缩放到 1m 左右。
        /// 各模型制作单位不一致（mm / cm / m），不归一会导致 AR 下尺度混乱。
        /// </summary>
        private void NormalizeScale(GameObject root)
        {
            var bounds = new Bounds();
            var renderers = root.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return;

            bool initialized = false;
            foreach (var r in renderers)
            {
                if (!initialized) { bounds = r.bounds; initialized = true; }
                else bounds.Encapsulate(r.bounds);
            }

            float largest = Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z);
            if (largest <= 0f) return;

            float target = 1f;
            root.transform.localScale = Vector3.one * (target / largest);
            root.transform.position = Vector3.zero;
        }

        private void EnsureContainer()
        {
            if (modelContainer == null)
            {
                var go = new GameObject("ModelContainer");
                modelContainer = go.transform;
            }
        }

        private void DestroyLoadedModel()
        {
            if (loadedRoot != null)
            {
                Destroy(loadedRoot);
                loadedRoot = null;
            }
        }

        private void OnDestroy()
        {
            DestroyLoadedModel();
            Core.UnityMessageManager.Unregister("loadModel");
            Core.UnityMessageManager.Unregister("clearModel");
        }

        private void SendEvent(string eventName, string jsonData)
        {
            Core.UnityMessageManager.Instance?.SendToFlutter(eventName, jsonData);
        }

        private void SendError(string message, string method)
        {
            SendEvent("onError", $"{{\"message\":\"{message}\",\"method\":\"{method}\"}}");
        }

        public GameObject GetLoadedModel() => loadedRoot;
        public int GetCurrentModelId() => currentModelId;
        public bool IsLoading => _loading;
    }
}
