using UnityEngine;
using System;
using System.Collections.Generic;

namespace ForkliftBao.Core
{
    /// <summary>
    /// Flutter ↔ Unity 双向通信桥。
    /// Flutter 侧通过 MethodChannel 调用 OnMessageFromFlutter 传入 JSON，
    /// Unity 侧通过 SendToFlutter 回传事件（由原生插件转发到 EventChannel）。
    /// </summary>
    public class UnityMessageManager : MonoBehaviour
    {
        public static UnityMessageManager Instance { get; private set; }

        /// <summary>
        /// JSON data 字符串 → 处理函数。
        /// </summary>
        public delegate void MessageHandler(string jsonData);

        // 静态注册表：必须在 Awake 阶段可查。
        // 早期版本用 RegisterDefaults() 在 Awake 里集中注册，但那要求所有单例的
        // Instance 都已就绪；任一单例不在场景中就会抛 NPE，直接中断整个 Awake，
        // 导致后续 SendToFlutter 全部失效。改为惰性注册 + 运行时容错。
        private static Dictionary<string, MessageHandler> s_handlers =
            new Dictionary<string, MessageHandler>();

        /// <summary>
        /// 供各功能脚本在自身 Awake 中注册。可重复调用，后者覆盖前者。
        /// </summary>
        public static void Register(string method, MessageHandler handler)
        {
            s_handlers[method] = handler;
        }

        public static void Unregister(string method)
        {
            s_handlers.Remove(method);
        }

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            s_handlers.Clear();
        }

        /// <summary>
        /// 解析 Flutter 发来的 JSON 消息并分发。任何异常都被吞掉并回传给 Flutter，
        /// 绝不让单个 handler 的错误影响桥本身。
        /// </summary>
        public void OnMessageFromFlutter(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                SendToFlutter("onError", "{\"message\":\"空消息\",\"method\":\"\"}");
                return;
            }

            FlutterMessage msg;
            try
            {
                msg = JsonUtility.FromJson<FlutterMessage>(json);
            }
            catch (System.Exception ex)
            {
                SendToFlutter("onError", $"{{\"message\":\"JSON 解析失败: {Escape(ex.Message)}\",\"method\":\"\"}}");
                return;
            }

            if (msg == null || string.IsNullOrEmpty(msg.method))
            {
                SendToFlutter("onError", "{\"message\":\"缺少 method 字段\",\"method\":\"\"}");
                return;
            }

            if (!s_handlers.TryGetValue(msg.method, out MessageHandler handler))
            {
                Debug.LogWarning($"[UnityMessageManager] 未注册方法: {msg.method}");
                SendToFlutter("onError", $"{{\"message\":\"未注册方法\",\"method\":\"{msg.method}\"}}");
                return;
            }

            try
            {
                handler(msg.data ?? "{}");
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[UnityMessageManager] 方法 {msg.method} 执行异常: {ex}");
                SendToFlutter("onError",
                    $"{{\"message\":\"{Escape(ex.Message)}\",\"method\":\"{msg.method}\"}}");
            }
        }

        public void SendToFlutter(string eventName, string jsonData = "{}")
        {
            var payload = $"{{\"eventName\":\"{Escape(eventName)}\",\"data\":{(string.IsNullOrEmpty(jsonData) ? "{}" : jsonData)}}}";
#if UNITY_ANDROID && !UNITY_EDITOR
            using (var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
            using (var activity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity"))
            {
                activity.Call("sendMessageToFlutter", eventName, jsonData);
            }
#elif UNITY_IOS && !UNITY_EDITOR
            ForkliftBao.Native.NativeBridge_iOS.sendMessageToFlutter(eventName, jsonData);
#else
            Debug.Log($"[Unity→Flutter] {payload}");
#endif
        }

        private static string Escape(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            return s.Replace("\\", "\\\\").Replace("\"", "\\\"")
                    .Replace("\n", "\\n").Replace("\r", "").Replace("\t", " ");
        }
    }

    [System.Serializable]
    public class FlutterMessage
    {
        public string method;
        public string data;
    }
}
