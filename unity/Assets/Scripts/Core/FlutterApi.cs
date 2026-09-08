namespace ForkliftBao.Core
{
    [System.Serializable]
    public class LoadModelParam
    {
        public string url;
        public int modelId;
    }

    [System.Serializable]
    public class PlayAnimParam
    {
        public string name;
        public float speed = 1f;
    }

    [System.Serializable]
    public class MastParam
    {
        public float heightMm;
    }

    [System.Serializable]
    public class TiltParam
    {
        public float angle;
    }

    [System.Serializable]
    public class SteerParam
    {
        public float angle;
    }

    [System.Serializable]
    public class HighlightParam
    {
        public int partId;
        public string color;
    }

    [System.Serializable]
    public class TransparentParam
    {
        public bool enabled;
        public string group;
    }

    [System.Serializable]
    public class ExplodedParam
    {
        public float progress;
    }

    [System.Serializable]
    public class EnterARParam
    {
        public int modelId;
        public ArConfigData arConfig;
    }

    [System.Serializable]
    public class ArConfigData
    {
        public float real_length_mm;
        public float real_width_mm;
        public float real_height_mm;
        public float real_mast_height_mm;
        public float real_wheelbase_mm;
        public float real_turning_radius_mm;
    }

    [System.Serializable]
    public class ScaleParam
    {
        public float factor;
    }

    [System.Serializable]
    public class ShowDimParam
    {
        public bool show;
    }

    [System.Serializable]
    public class EventPayload
    {
        public string eventName;
        public string data;
    }
}
