# ForkliftCLI 重建方案下一步

## 现在状态
- STEP 文件已确认：有装配关系，能保留层级
- Unity 导入指南已写
- 元数据脚本已写
- 动画模板已写

## 下一步
1. 在 SolidWorks 里打开 `Glb/Forklift.STEP`
2. 按导出指南整理部件名
3. 导出 `forklift_main.fbx`
4. 放入 `unity/Assets/StreamingAssets/models/`
5. 运行：
   `python3 tools/generate_model_metadata.py --output unity/Assets/StreamingAssets/models/`
6. 用 Unity 导入指南配场景和脚本

## 目标
- 8 个可识别部件
- 3 个基础动画
- 1 个 AR 1:1 模型
- 1 套 Flutter→Unity 控制桥
