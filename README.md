# chexie-related

这个仓库保存和 chexie.net / CAPUBBS 相关的本地工具、Codex skills 和少量可公开的签名档草稿。

## 内容概览

- `.codex/skills/chexie-signature/`: 车协签名档制作、预览、检查和发布辅助 skill。
- `.codex/skills/chexie-image-upload/`: 车协论坛图片上传、图片引用和签名档图片处理辅助 skill。
- `chexie_agent/`: 账户 agent 的 Python package 骨架，包含 forum-independent 数据模型、安全 gate、legacy/new forum adapters 和 workflow 入口。
- `docs/`: 新版论坛迁移、账户 agent 规划等可公开设计文档。
- `scripts/`: 用于检查论坛页面、导出签名档、更新或恢复签名档的辅助脚本。
- `data/`: 本地草稿、预览、抓取快照等运行产物。这个目录不上传到 GitHub。
- `notes/`: 本地工作记录。这个目录不上传到 GitHub。
- `login_info/`: 本地登录信息。这个目录不上传到 GitHub。

## Skills

### `chexie-signature`

用于创建和维护 chexie.net CAPUBBS 签名档。它支持两类主要场景：

- 个人签名档：骑行经历、活动历史、角色、队伍、引语、链接、折叠区块等。
- 团号签名档：团名、口号、路线、成员名单、头像/图片和统一视觉样式。

它还记录了长签名档的稳定做法：把完整 HTML 放在普通论坛楼层里，再用短 JavaScript loader 从签名档加载该楼层内容。这样可以绕开直接写入签名档时可能遇到的长度限制，并方便以后只编辑源楼层。

该 skill 强调先生成本地草稿和预览，除非用户明确授权，不直接登录论坛修改签名档、发帖或改资料。

### `chexie-image-upload`

用于处理 chexie.net CAPUBBS 上的图片上传和图片引用。它把几种容易混淆的情况分开：

- 外链图片：论坛只展示外部 URL，不占用论坛存储。
- 论坛托管图片：图片保存在 `https://chexie.net/bbs/images/...` 之类的地址。
- 编辑器图片上传：通过回复编辑器的 `上传图片` 按钮上传到 `/bbs/content/test.php`，返回可复用的论坛托管图片 URL。
- 帖子附件：通过发帖编辑器的 `添加附件` 上传，并用 attachment id 绑定到帖子。
- 签名档图片：在签名档 HTML 或动态 source floor 里引用图片 URL。

它还记录了论坛公开教程里关于“链接”和“上传”的区别，以及从帖子里复用论坛托管图片时应把 `../images/...` 转成绝对 URL。

## 安全约定

不要把以下内容提交到 GitHub：

- 论坛用户名、密码、cookie、session id、token。
- `login_info/`。
- `data/` 下的抓取快照、草稿、预览、数据库。
- `notes/` 下的本地工作记录。

`.gitignore` 已经默认忽略这些本地目录和常见 Python 缓存。

## 常用命令

查看当前 Git 状态：

```bash
git status --short --branch
```

提交改动：

```bash
git add .
git commit -m "Describe the change"
git push
```

生成签名档预览时，优先使用 skill 自带脚本：

```bash
python3 .codex/skills/chexie-signature/scripts/make_preview.py input.html output.html
```

只读解析一个 legacy CAPUBBS 帖子页面为结构化 JSON：

```bash
python3 scripts/chexie_read_thread.py "https://chexie.net/bbs/content/?bid=28&tid=150&p=1"
```

这个命令只做一次公开 GET 请求，不使用登录信息，也不会写论坛。

只读搜索 legacy CAPUBBS 公开帖子并输出结构化 JSON：

```bash
python3 scripts/chexie_search_threads.py "新版论坛"
python3 scripts/chexie_search_threads.py "暑期" --author "蓝" --type post
```

这个命令只提交一次公开搜索表单，不使用登录信息，也不会写论坛。
