#if UNITY_IOS && !UNITY_EDITOR
using System.Runtime.InteropServices;
#endif
using UnityEngine;

namespace ForkliftBao.Native
{
    /// <summary>
    /// iOS 原生桥：Unity → Flutter 事件发送。
    /// 对应 Xcode Runner 中的 NativeBridge_iOS.swift。
    /// </summary>
    public static class NativeBridge_iOS
    {
#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")]
        private static extern void _forkliftBao_sendToFlutter(string eventName, string jsonData);
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