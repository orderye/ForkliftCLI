using UnityEngine;
using System.Collections.Generic;

namespace ForkliftBao.Core
{
    /// <summary>
    /// Flutter ↔ Unity 双向通信桥。Flutter 侧通过 MethodChannel 调用 OnMessageFromFlutter 传入 JSON，
    /// Unity 侧通过 SendToFlutter 回传事件（由原生插件转发到 EventChannel）。
    /// </summary>
    public class UnityMessageManager : MonoBehaviour
    {
        public static UnityMessageManager Instance { get; private set; }

        public delegate void MessageHandler(string jsonData);
        private Dictionary<string, MessageHandler> _handlers = new Dictionary<string, MessageHandler>();

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            RegisterDefaults();
        }

        void RegisterDefaults()
        {
            Register("loadModel", Viewer.ModelLoader.Instance.LoadModel);
            Register("playAnimation", Viewer.AnimationController.Instance.Play);
            Register("stopAnimation", Viewer.AnimationController.Instance.Stop);
            Register("setMastHeight", Viewer.AnimationController.Instance.SetMastHeight);
            Register("setTiltAngle", Viewer.AnimationController.Instance.SetTiltAngle);
            Register("setSteerAngle", Viewer.AnimationController.Instance.SetSteerAngle);
            Register("highlightPart", Viewer.PartHighlighter.Instance.Highlight);
            Register("clearHighlight", Viewer.PartHighlighter.Instance.Clear);
            Register("setTransparent", Viewer.PartHighlighter.Instance.SetTransparent);
            Register("setExploded", Viewer.ExplodedView.Instance.SetProgress);
            Register("enterAR", AR.ARPlacementController.Instance.Enter);
            Register("confirmARPlacement", AR.ARPlacementController.Instance.ConfirmPlacement);
            Register("showARDimensions", AR.ARDimensionOverlay.Instance.Show);
            Register("setARScale", AR.ARPlacementController.Instance.SetScale);
            Register("resetView", Viewer.CameraController.Instance.ResetView);
        }

        public void Register(string method, MessageHandler handler) => _handlers[method] = handler;

        public void OnMessageFromFlutter(string json)
        {
            if (string.IsNullOrEmpty(json)) return;
            FlutterMessage msg = JsonUtility.FromJson<FlutterMessage>(json);
            if (msg == null || string.IsNullOrEmpty(msg.method)) return;

            if (_handlers.TryGetValue(msg.method, out var handler))
                handler(msg.data);
            else
                Debug.LogWarning($"[UnityMessageManager] 未注册方法: {msg.method}");
        }

        public void SendToFlutter(string eventName, string jsonData = "{}")
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            using (var unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
            using (var activity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity"))
            {
                activity.Call("sendMessageToFlutter", eventName, jsonData);
            }
#elif UNITY_IOS && !UNITY_EDITOR
            ForkliftBao.Native.NativeBridge_iOS.sendMessageToFlutter(eventName, jsonData);
#else
            Debug.Log($"[Unity→Flutter] {eventName}: {jsonData}");
#endif
        }
    }

    [System.Serializable]
    public class FlutterMessage
    {
        public string method;
        public string data;
    }
}
