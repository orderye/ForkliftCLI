#if UNITY_IOS && !UNITY_EDITOR
using System.Runtime.InteropServices;
#endif
using UnityEngine;

namespace ForkliftBao.Native
{
    /// <summary>
    /// iOS 原生桥：Unity → Flutter 事件发送。
    /// 对应 Xcode Runner 中的 NativeBridge_iOS.mm（ObjC++ 实现，见仓库根目录说明）。
    /// </summary>
    public static class NativeBridge_iOS
    {
#if UNITY_IOS && !UNITY_EDITOR
        // 必须用 char*，string 在 ObjC 侧需要 marshalling 才能拿到。
        [DllImport("__Internal")]
        private static extern void _forkliftBao_sendToFlutter(string eventName, string jsonData);

        // 由 ObjC++ 实现调用回来，把事件送进 UnityMessageManager 的处理入口。
        public static void SendMessageFromFlutter(string json)
        {
            UnityMessageManager.Instance?.OnMessageFromFlutter(json);
        }
#endif

        public static void sendMessageToFlutter(string eventName, string jsonData)
        {
#if UNITY_IOS && !UNITY_EDITOR
            _forkliftBao_sendToFlutter(eventName, jsonData);
#else
            Debug.Log($"[iOSBridge] {eventName}: {jsonData}");
#endif
        }
    }
}