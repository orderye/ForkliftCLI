#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ForkliftBao.Editor
{
    /// <summary>
    /// 一键创建最小场景骨架。
    /// 只做空场景 + 必要节点，不依赖 FBX。
    /// </summary>
    public static class CreateScenes
    {
        [MenuItem("ForkliftCLI/Scenes/Create ThreeDViewer Scene")]
        public static void CreateThreeDViewer()
        {
            NewScene();
            var root = new GameObject("ForkliftCLI_Root");
            root.AddComponent<ForkliftBao.Core.AppManager>();

            var cameraGo = new GameObject("Main Camera");
            cameraGo.tag = "MainCamera";
            cameraGo.AddComponent<Camera>();
            cameraGo.transform.position = new Vector3(0, 3, -8);
            cameraGo.transform.rotation = Quaternion.Euler(15, 0, 0);

            var lightGo = new GameObject("Directional Light");
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.0f;
            lightGo.transform.rotation = Quaternion.Euler(50, -30, 0);

            var modelRoot = new GameObject("Forklift_Root");
            modelRoot.transform.position = Vector3.zero;
            var bootstrap = root.AddComponent<ForkliftBao.Viewer.SceneBootstrap>();
            bootstrap.modelContainer = modelRoot.transform;

            root.AddComponent<ForkliftBao.Viewer.AnimationController>();
            root.AddComponent<ForkliftBao.Viewer.ExplodedView>();
            root.AddComponent<ForkliftBao.Viewer.PartHighlighter>();

            EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), "Assets/Scenes/ThreeDViewer.unity");
        }

        [MenuItem("ForkliftCLI/Scenes/Create ARView Scene")]
        public static void CreateARView()
        {
            NewScene();
            var root = new GameObject("ForkliftCLI_Root");
            root.AddComponent<ForkliftBao.Core.AppManager>();

            var cameraGo = new GameObject("AR Camera");
            cameraGo.tag = "MainCamera";
            cameraGo.AddComponent<Camera>();
            cameraGo.transform.position = new Vector3(0, 1.6f, 0);

            var modelRoot = new GameObject("Forklift_Root");
            var placement = root.AddComponent<ForkliftBao.AR.ARPlacementController>();
            placement.modelContainer = modelRoot.transform;

            EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), "Assets/Scenes/ARView.unity");
        }

        private static void NewScene()
        {
            EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
        }
    }
}
#endif
