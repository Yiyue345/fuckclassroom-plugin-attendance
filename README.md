# FuckClassroom 二维码签到插件

FuckClassroom 的独立二维码签到插件，插件 ID 为 `attendance`。

## 功能

- 扫描畅课 / 课堂派签到二维码
- 畅课二维码签到
- 课堂派账号与短信登录
- 课堂派签到处理
- 独立扫码 Worker，隔离 OpenCV / 原生 wxscan 运行时

## 依赖

- FuckClassroom: `>=0.1,<0.3`
- Plugin API: `1`
- Required plugin: `classroom`
- `cryptography>=43.0`
- `numpy>=1.24`
- `opencv-python>=4.8`

`fuckclassroom_wxscan` 原生扩展属于可选加速能力。若宿主已提供该扩展则优先使用；否则自动回退到 OpenCV QRCodeDetector，因此 Registry 包不声明本地路径依赖。

## 开发

开发分支为 `plugin-management`。合并到 `main` 后，CI 成功会自动发布 Registry v1 beta Release。
