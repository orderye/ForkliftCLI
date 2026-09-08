using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
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

        private int _currentVersion = 1;
        private string _currentHash = "";
        private string _currentFormat = "glb";

        private static string CacheDir =>
            Path.Combine(Application.persistentDataPath, "ForkliftCLI", "Models");

        private static string CacheIndexFile =>
            Path.Combine(CacheDir, "cache_index.json");

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            Core.UnityMessageManager.Register("loadModel", LoadModel);
            Core.UnityMessageManager.Register("clearModel", ClearModel);
        }

        /// <summary>
        /// 入口：接收 {"url": "...", "modelId": 1, "version": 2, "contentHash": "ab12...", "format": "glb"}。
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
            _currentVersion = param.version;
            _currentHash = param.contentHash ?? "";
            _currentFormat = string.IsNullOrEmpty(param.format) ? "glb" : param.format.ToLowerInvariant();

            Debug.Log($"[ModelLoader] 开始加载 modelId={param.modelId} v{_currentVersion} url={param.url}");

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

            // 本地缓存命中：相同 modelId + version + hash 视为同一资源，直接解析。
            string cachedPath = ResolveCachePath();
            if (!string.IsNullOrEmpty(cachedPath) && File.Exists(cachedPath))
            {
                byte[] cached = File.ReadAllBytes(cachedPath);
                Debug.Log($"[ModelLoader] 缓存命中 {cachedPath} ({cached.Length} bytes)");
                if (TryImport(cached, cachedPath))
                {
                    _loading = false;
                    SendEvent("onModelLoaded",
                        $"{{\"success\":true,\"modelId\":{currentModelId},\"bytes\":{cached.Length}," +
                        $"\"rendererCount\":{renderersCount(loadedRoot)},\"fromCache\":true}}");
                    yield break;
                }
                // 缓存损坏则继续下载。
                Debug.LogWarning("[ModelLoader] 缓存解析失败，重新下载");
            }

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

            // 写入本地缓存（按 modelId + version + hash 命名，便于版本失效与清理）。
            if (!string.IsNullOrEmpty(cachedPath))
            {
                try
                {
                    Directory.CreateDirectory(CacheDir);
                    File.WriteAllBytes(cachedPath, data);
                    UpdateCacheIndex(currentModelId, _currentVersion, _currentHash, cachedPath);
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[ModelLoader] 写缓存失败: {e.Message}");
                }
            }

            try
            {
                if (TryImport(data, cachedPath ?? url))
                {
                    _loading = false;
                    SendEvent("onModelLoaded",
                        $"{{\"success\":true,\"modelId\":{currentModelId},\"bytes\":{data.Length}," +
                        $"\"rendererCount\":{renderersCount(loadedRoot)},\"fromCache\":false}}");
                    yield break;
                }

                _loading = false;
                SendError("模型解析失败：格式不受支持或内容为空", "loadModel");
            }
            catch (Exception ex)
            {
                _loading = false;
                Debug.LogError($"[ModelLoader] 导入异常: {ex}");
                SendError($"模型导入失败: {ex.Message}", "loadModel");
            }
        }

        /// <summary>
        /// 统一解析入口（GLTFast 或降级）。成功返回 true 并把 root 挂到 modelContainer。
        /// </summary>
        private bool TryImport(byte[] data, string sourcePath)
        {
            if (data == null || data.Length == 0) return false;
            GameObject root = ImportModel(data, sourcePath, out string cachePath);
            if (root == null)
            {
                if (cachePath != null)
                    Debug.LogWarning($"[ModelLoader] 已缓存 {cachePath}，但未安装 com.unity.cloud.gltfast，无法解析");
                return false;
            }
            loadedRoot = root;
            root.transform.SetParent(modelContainer, false);
            NormalizeScale(root);
            return true;
        }

        /// <summary>
        /// 缓存文件名：model_{id}_v{version}_{hash8}.glb
        /// 没有 hash 时退化为仅按 modelId（仍可被新版本覆盖）。
        /// </summary>
        private string ResolveCachePath()
        {
            string hashPart = string.IsNullOrEmpty(_currentHash)
                ? "v" + _currentVersion
                : _currentHash.Substring(0, Mathf.Min(8, _currentHash.Length));
            string ext = (_currentFormat == "gltf") ? "gltf" : "glb";
            return Path.Combine(CacheDir, $"model_{currentModelId}_v{_currentVersion}_{hashPart}.{ext}");
        }

        private void UpdateCacheIndex(int modelId, int version, string hash, string path)
        {
            try
            {
                // 简单索引：一行一条 "modelId|version|hash|path"
                var lines = File.Exists(CacheIndexFile)
                    ? new List<string>(File.ReadAllLines(CacheIndexFile))
                    : new List<string>();
                lines.RemoveAll(l => l.StartsWith(modelId.ToString() + "|"));
                lines.Add($"{modelId}|{version}|{hash}|{path}");
                File.WriteAllLines(CacheIndexFile, lines);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[ModelLoader] 更新缓存索引失败: {e.Message}");
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
