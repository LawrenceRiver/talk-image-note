# talk-image-&note

在原页图片上圈画，在聊天中说明修改，再把改法整理成贴着原句的旁批。适合逐节修改论文、审阅图表和讨论文档。

保留原件排版和高亮；支持注意点、圈线、旁批拖拽与缩放、翻页、撤销、最近删除、单条／整页复制、PNG 导出，以及内嵌图片的可编辑 HTML。

## Contributors

<a href="https://github.com/jason0917-eng"><img src="https://avatars.githubusercontent.com/u/211797332?v=4" width="64" height="64" alt="Chen Zhuoxuan (jason0917-eng)"></a>

**[Chen Zhuoxuan · @jason0917-eng](https://github.com/jason0917-eng)** — Windows 适配：无需 Swift／OCR 的图片导入、区域批注及相关保存与导出支持。见 [PR #1](https://github.com/LawrenceRiver/talk-image-note/pull/1)。

## 安装为 Codex skill

克隆本仓库到 `~/.codex/skills/talk-image-note`。如果那里已经有本地版本，请先保留备份，不直接覆盖。重新加载技能后调用 `$talk-image-note`。

也可以先克隆到普通开发目录，检查后再复制到技能目录。

## 本地使用

需要 Python 3.10+、Pillow 和现代浏览器。运行测试还需要 Node.js。

### Windows（PowerShell）

在项目目录运行以下命令。示例把两张合成图和工作数据放在临时工作区，便于验证。

```powershell
python -m venv .venv
$python = ".\.venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt

$workspace = Join-Path $env:TEMP ("talk-image-note-" + [guid]::NewGuid().ToString("N"))
& $python scripts/bootstrap_workspace.py --root "$workspace"
$page1 = Join-Path $workspace "example-1.png"
$page2 = Join-Path $workspace "example-2.jpg"
& $python -c "from PIL import Image, ImageDraw; import sys; im=Image.new('RGB',(600,850),'white'); ImageDraw.Draw(im).rectangle((80,90,500,240),fill='skyblue'); im.save(sys.argv[1]); im=Image.new('RGB',(600,850),'white'); ImageDraw.Draw(im).ellipse((120,100,480,460),fill='orange'); im.save(sys.argv[2])" "$page1" "$page2"
& $python scripts/import_images.py --root "$workspace" "$page1" "$page2"
& $python scripts/server.py --root "$workspace" --port 8847
```

用 Edge 或 Chrome 打开 `http://127.0.0.1:8847/`。用「加点点」在图上圈画定位，或用「圈画」工具在图上画一圈以标记矩形区域。也可在页边空白处双击新建旁批，输入文字后把卡片拖到图上定位。草稿自动写入工作区的 `annotations/draft.json`。用左右箭头翻页，用工具包里的「导出图片」或「可编辑文件」导出当前页。文件保存在工作区的 `exports`，浏览器也会下载一份。用自己的 PNG／JPEG 时，把工作区放在仓库外的持久目录。

Windows 直接导入原图，无需 Swift 或 OCR。此模式按图片区域定位，无法自动选取原文文字或把手写转成文字。手写墨迹仍可保存。切换 OCR 模式时请使用新工作区，以免已有的选字批注失去定位。

### macOS

macOS 默认使用 Swift／Vision 做图像和手写识别。图像导入可以加 `--no-ocr` 跳过识别。Vision 不可用时仍可导入和圈画。

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

本工具不内置 AI 服务。聊天中的助手读取定位记录后更新批注。

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
