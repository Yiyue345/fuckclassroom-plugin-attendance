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

\`fuckclassroom_wxscan\` 原生扩展属于插件自己维护的可选能力，不再依赖宿主或主仓的 \`rust_module/wxscan_py\`。正式版与 beta Release 会构建 Linux x86_64、Windows x86_64、macOS x86_64 / Apple Silicon 的 PyO3 ABI3 二进制，按平台打包在 \`native/\` 下，并携带 SHA-256 manifest。

扫码时先根据系统与 CPU 架构定位本插件自带的原生扩展，校验哈希后再加载；平台没有对应二进制、校验失败、原生模型不可用或初始化失败时自动回退 OpenCV QRCodeDetector。插件可在没有 Rust/Cargo 的电脑上安装，模型依然按需下载到宿主数据目录下的 \`models/wxscan\`。

本地开发仅需要 OpenCV；需要调试 Rust 扩展时可在插件仓执行：

\`\`\`bash
python -m pip install "maturin>=1.7,<2"
maturin build --release --manifest-path rust_module/wxscan_py/Cargo.toml --interpreter python --out dist
\`\`\`

GitHub Actions \`build-native.yml\` 统一负责正式版 / beta 的原生编译、stage、校验与 Registry ZIP 打包。

签到插件通过宿主 `ServiceContainer` 注入的 `classroom_client` 调用课程插件能力，不直接依赖宿主中的 Classroom 实现模块。

## 开发

开发分支为 `plugin-management`。合并到 `main` 后，CI 成功会自动发布 Registry v1 beta Release。
