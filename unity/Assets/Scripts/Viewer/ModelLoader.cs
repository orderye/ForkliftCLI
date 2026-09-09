using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
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
    /// ForkliftBao.asmdef 的 versionDefines 会在包装上时自动定义 FORKLIFT_GLTFAST，
    /// 走真正的异步解析导入；未安装时降级为「下载并缓存到本地」，保证桥接链路可跑通、
    /// 错误可回传，而不是静默假装成功。
    ///
    /// 缓存策略：modelId + version + contentHash 命中本地文件则跳过下载。
    /// </summary>
    public class ModelLoader : MonoBehaviour
    {
        public static ModelLoader Instance { get; private set; }

        [Header("Target")]
        public Transform modelContainer;

        [Header("Timeout")]
        public float downloadTimeoutSeconds = 60f;

        private int currentModelId;
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
            _currentVersion = param.version > 0 ? param.version : 1;
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
            StopAllCoroutines();
            _loading = false;
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
                byte[] cached = null;
                try { cached = File.ReadAllBytes(cachedPath); }
                catch (Exception e) { Debug.LogWarning($"[ModelLoader] 读缓存失败: {e.Message}"); }

                if (cached != null && cached.Length > 0)
                {
                    Debug.Log($"[ModelLoader] 缓存命中 {cachedPath} ({cached.Length} bytes)");
                    bool fromCacheOk = false;
                    yield return ImportRoutine(cached, v => fromCacheOk = v);
                    if (fromCacheOk)
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
            }

            using (var request = UnityWebRequest.Get(url))
            {
                request.timeout = Mathf.Max(1, (int)downloadTimeoutSeconds);
                var op = request.SendWebRequest();
                while (!op.isDone) yield return null;

                bool failed;
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

                // 写入本地缓存（按 modelId + version + hash 命名，便于版本失效与清理）。
                if (!string.IsNullOrEmpty(cachedPath) && data != null && data.Length > 0)
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

                bool ok = false;
                yield return ImportRoutine(data, v => ok = v);
                _loading = false;

                if (!ok || data == null || data.Length == 0)
                {
                    SendError("模型解析失败：格式不受支持或内容为空", "loadModel");
                    yield break;
                }

                SendEvent("onModelLoaded",
                    $"{{\"success\":true,\"modelId\":{currentModelId},\"bytes\":{data.Length}," +
                    $"\"rendererCount\":{renderersCount(loadedRoot)},\"fromCache\":false}}");
            }
        }

        /// <summary>
        /// 统一解析入口：GLTFast（Task 轮询转协程）或降级缓存。完成后回调 done(success)。
        /// </summary>
        private IEnumerator ImportRoutine(byte[] data, Action<bool> done)
        {
#if FORKLIFT_GLTFAST
            yield return ImportWithGltfast(data, done);
#else
            ImportFallback(data);
            done(false);
            yield break;
#endif
        }

#if FORKLIFT_GLTFAST
        /// <summary>
        /// GLTFast 导入：LoadGltfBinaryAsync + InstantiateSceneAsync。
        /// 每次导入新建 GltfImport 实例（官方建议一实例一次导入），用完 Dispose。
        /// </summary>
        private IEnumerator ImportWithGltfast(byte[] data, Action<bool> done)
        {
            if (data == null || data.Length == 0) { done(false); yield break; }

            GltfImport importer = null;
            GameObject root = null;
            try
            {
                importer = new GltfImport();

                Task<bool> loadTask = importer.LoadGltfBinaryAsync(data);
                while (!loadTask.IsCompleted) yield return null;

                if (!loadTask.Result)
                {
                    Debug.LogError("[ModelLoader] GLTFast 解析失败");
                    done(false);
                    yield break;
                }

                root = new GameObject($"Model_{currentModelId}");
                Task<bool> instTask = importer.InstantiateSceneAsync(root.transform);
                while (!instTask.IsCompleted) yield return null;

                if (!instTask.Result)
                {
                    Destroy(root);
                    root = null;
                    Debug.LogError("[ModelLoader] GLTFast 实例化失败");
                    done(false);
                    yield break;
                }

                loadedRoot = root;
                root.transform.SetParent(modelContainer, false);
                NormalizeScale(root);
                done(true);
            }
            catch (Exception ex)
            {
                if (root != null) Destroy(root);
                Debug.LogError($"[ModelLoader] 导入异常: {ex}");
                done(false);
            }
            finally
            {
                if (importer != null) importer.Dispose();
            }
        }
#else
        /// <summary>
        /// 降级分支：没有 GLTFast 时无法解析 glTF，把字节落到缓存目录并提示装包。
        /// 目的：让链路可诊断，而不是谎报加载成功。
        /// </summary>
        private void ImportFallback(byte[] data)
        {
            string dir = Path.Combine(Application.persistentDataPath, "models");
            if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);

            string hashPart = string.IsNullOrEmpty(_currentHash)
                ? "v" + _currentVersion
                : _currentHash.Substring(0, Mathf.Min(8, _currentHash.Length));
            string filename = $"model_{currentModelId}_{hashPart}.{_currentFormat}";
            string cachePath = Path.Combine(dir, filename);
            try { File.WriteAllBytes(cachePath, data); }
            catch (Exception e) { Debug.LogWarning($"[ModelLoader] 落盘失败: {e.Message}"); }

            Debug.LogWarning($"[ModelLoader] 已缓存 {cachePath}（{data?.Length ?? 0} bytes），" +
                             "但未安装 com.unity.cloud.gltfast，无法解析 glTF，模型不会显示。");
        }
#endif

        /// <summary>
        /// 缓存文件名：model_{id}_v{version}_{hash8}.glb
        /// 没有 hash 时退化为仅按 modelId + version。
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

        private static int renderersCount(GameObject root)
        {
            return root == null ? 0 : root.GetComponentsInChildren<Renderer>().Length;
        }

        /// <summary>
        /// 把模型归一到合理尺寸：按包围盒最长边缩放到 1m 左右。
        /// 各模型制作单位不一致（mm / cm / m），不归一会导致 AR 下尺度混乱。
        /// </summary>
        private void NormalizeScale(GameObject root)
        {
            var renderers = root.GetComponentsInChildren<Renderer>();
            if (renderers.Length == 0) return;

            var bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++) bounds.Encapsulate(renderers[i].bounds);

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
