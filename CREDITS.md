# 星野铃 · 模型来源与许可

**基底：VRM1_Constraint_Twist_Sample v1.0.1，© 2022 pixiv Inc.**

- [Pixiv 官方原文件（固定版本）](https://github.com/pixiv/three-vrm/blob/f0a0e13ebcb7a70230bb1768dcafc8dbe84ad672/packages/three-vrm/examples/models/VRM1_Constraint_Twist_Sample.vrm)
- [VRM 联盟样例的作者与许可声明](https://github.com/vrm-c/vrm-specification/tree/master/samples/VRM1_Constraint_Twist_Sample)
- [VRM Public License 1.0 完整正文](https://vrm.dev/en/licenses/1.0/) · [官方英文 PDF](https://vrm.dev/licenses/1.0/pdf/en.pdf)。
- 原文件 SHA-256：`12c2b97e95e700783a6a550dc0eee2d7880aeedccef9ae67bc4c5a2f0f2631a2`。

原文件许可设置如下。星野铃改作保留基底的版权与许可标识，基底部分按原许可提供；Phase A 开发改作沿用相同条款。

```json
{
  "authors": ["pixiv Inc."],
  "copyrightInformation": "(c) 2022 pixiv Inc.",
  "licenseUrl": "https://vrm.dev/licenses/1.0/",
  "avatarPermission": "everyone",
  "commercialUsage": "corporation",
  "creditNotation": "unnecessary",
  "allowRedistribution": true,
  "modification": "allowModificationRedistribution",
  "allowExcessivelyViolentUsage": true,
  "allowExcessivelySexualUsage": true,
  "allowPoliticalOrReligiousUsage": true,
  "allowAntisocialOrHateUsage": false
}
```

项目在基底上制作星野铃身材比例、脸部、2K 试妆纹理与表情预设。源模型的角色和测试服装不作为星野铃原创内容。法律条款及免责声明见上列官方许可全文。

## 供体胸廓（Phase A 素体）

**Base_Female，VRoid Project / pixiv Inc.**：原样例以 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) 发布。参阅 [Pixiv 官方样模许可分类](https://vroid.pixiv.help/hc/en-us/articles/4402614652569) 与 [样模存档](https://opengameart.org/content/vroid-studio-cc0-models)。只取原始皮肤胸廓，转接至本项目的 Pixiv Twist 素体；不使用供体脸、测试衣物或供体骨架。
供体原文件 SHA-256：`1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b`。

## Phase D 网页检视器依赖

- [Three.js r180](https://github.com/mrdoob/three.js/tree/r180)（0.180.0，MIT）：核心、WebGL Renderer、OrbitControls、GLTFLoader 与 BufferGeometryUtils。原作者与许可保留在 [`viewer/vendor/three/LICENSE`](viewer/vendor/three/LICENSE)。运行所需脚本全部随仓库提供，不访问 CDN。
- [Playwright](https://playwright.dev/)（1.56.1，Apache-2.0）仅用于开发验收，不作为检视器的运行依赖。
