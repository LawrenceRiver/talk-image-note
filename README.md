# talk-image-&note

在原页图片上圈画，在聊天中说明修改，再把改法整理成贴着原句的旁批。适合逐节修改论文、审阅图表和讨论文档。

保留原件排版和高亮；支持注意点、圈线、旁批拖拽与缩放、翻页、撤销、最近删除、单条／整页复制、PNG 导出，以及内嵌图片的可编辑 HTML。

## 安装为 Codex skill

克隆本仓库到 `~/.codex/skills/talk-image-note`。如果那里已经有本地版本，请先保留备份，不直接覆盖。重新加载技能后调用 `$talk-image-note`。

也可以先克隆到普通开发目录，检查后再复制到技能目录。

## 本地使用

需要 Python 3.10+；图像导入需要 Pillow，以及 macOS 的 Swift／Vision。运行测试还需要 Node.js。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# 把真实材料放在仓库外
python scripts/bootstrap_workspace.py --root "$HOME/Documents/paper-review-workspace"
python scripts/import_images.py --root "$HOME/Documents/paper-review-workspace" /absolute/path/page1.png /absolute/path/page2.png
python scripts/server.py --root "$HOME/Documents/paper-review-workspace" --port 8847
```

在浏览器打开 `http://127.0.0.1:8847/`。本地 PDF 请先渲染成 PNG，保留原始版式和清晰度。

图像导入的自动 OCR 目前依赖 macOS；界面在浏览器运行。其他系统可按工作区协议自行准备图片和定位数据。本工具不内置 AI 服务；聊天中的助手读取定位记录后更新批注。

## 修改和保存

先圈画注意区域，再在聊天说明。助手按同一 ID 更新旁批；默认不改原件。只导出 PNG 会失去交互，继续编辑应导出单文件 HTML。HTML 的编辑保存在浏览器中，修改后需重新导出才能交给别人。

这是本地单用户版，没有登录、多人同步、云盘或在线评论集成。不应将服务暴露到公网。

## 发布边界

仓库只包含通用技能、界面代码、脚本和合成测试。实际论文、文档、推荐材料、原图、批注记录、导出文件、账号、云盘链接与文件 ID 均不属于仓库。

`.gitignore` 阻止常见材料被意外加入。发布前还要检查实际暂存内容：

```bash
python scripts/check_release.py
node --test tests/*.test.cjs
python -m unittest discover -s tests -p '*_test.py'
git diff --cached --stat
```

隐私扫描是辅助检查，不能替代对新增文件和差异的人工核对。
