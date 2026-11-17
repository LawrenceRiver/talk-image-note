# 工作区与批注协议

## 工作区

```text
workspace/
  app/                    从 assets/app 复制；用户界面
  data.json               源版本、篇目、原文、双语对应和透明文字坐标
  pages/                  原图及高清导出专用图
  annotations/
    draft.json            用户实时状态，不能被测试或旧副本覆盖
    latest-reference.json
    references/<ID>.json
    history/
  exports/                PNG、单文件 HTML
  archives/               带时间戳的快照和 ZIP
  checks/                 验证结果，与真实草稿分离
```

用 `scripts/bootstrap_workspace.py --root PATH` 初始化 UI。已有 app 文件内容不同时，默认拒绝覆盖；只有本轮确实需要更新界面，才加 `--refresh-ui`。这个脚本不会写 `data.json`、图片或用户草稿。

服务命令：`python scripts/server.py --root PATH --port 8847`。只监听 127.0.0.1。端口被占用时，先确认已有服务是不是这个 root；不要随意终止进程或打开别人的画布。

## 导入本地原件

只使用用户明确提供的本地 PNG/JPEG，或从本地 PDF 渲染得到的原页图片。
不连接云盘、不读取在线文档、不收集账号或聊天历史。将实际文件和批注保存在仓库外的工作区。

`import_images.py --root /absolute/workspace page1.png page2.png` 原字节复制图片，使用 macOS Vision 创建透明 OCR 定位层。
需要 macOS、Swift 编译器和 Pillow。其他系统可以按下方协议建立 data.json，并使用圈画定位。
文件名使用 `/pages/p1-en.png`、`/pages/p2-en.png` 等服务支持的命名形式。
PDF 应先通过本地渲染工具转成清晰 PNG；不要重排或重绘原文。中文对照只有在用户提供可靠对应稿时才导入。

## data 与定位

```json
{
  "source": {"url":"...","title":"...","modified_time":"...","sha256":"..."},
  "documents": [{
    "id":"DOC01","title":"...","page":1,
    "en":[{"id":"DOC01-P01","text":"...","source_shape":123,"source_paragraph":0}],
    "zh":[{"id":"DOC01-P01","text":"..."}],
    "images":{"en":{"url":"/pages/p1-en.png","width":595,"height":842,"boxes":[]}}
  }],
  "original_images":true
}
```

字框含 paragraphId、start/end、text 和相对原图归一化 x/y/w/h。start/end 使用 **UTF-16 code units**，不是 Python 字符数：`len(text.encode('utf-16-le')) // 2`。用完全一致的引文检查范围；中英各自校验，不能复制英文范围给中文。

基本注释：

```json
{
  "id":"UUID","docId":"DOC01","lang":"en","sourceVersion":"source sha256",
  "anchors":[{"paragraphId":"DOC01-P01","start":0,"end":5,"offset_unit":"utf16","quote":"..."}],
  "quote":"...","pairedReferences":{"en":{},"zh":{}},
  "stage":"locator","note":"",
  "attention":{"cleaned":false,"sourceLang":"en","points":[[0.2,0.3]],"sequence":0,"paragraphId":"DOC01-P01"},
  "textColor":"#397b70","pad":[],"ink":[],"example":false,
  "suggestion":{"before":"...","after":"...","detail":"..."},
  "translationSuggestion":"...","userInstruction":"...",
  "card":{"manualPosition":{"x":0.1,"y":0.1,"w":0.2,"h":0.1},"userSized":true}
}
```

图片区域可另存 region。只有可靠的双语对应才填 pairedReferences；缺少中文时不伪造。手动 card 坐标相对 sheet 保存，可落在扩展留白里，不用原图内 0–1 范围限制旁批。

## 从口述更新到已显示

1. 读取 `/api/draft` 和 `/data.json`。通过 activeId、latest-reference、引用 ID、用户引文及上下文唯一定位。先检查是否已有同处批注，避免重复创建。
2. 新辅助笔迹为 stage=locator、cleaned=false，允许 note 为空。引用只是保存位置，不创建修改文字。
3. `POST /api/reference {"id":"完整ID"}` 保存引用，取得准确中英引文和源版本。
4. 用户说了具体改法后，`POST /api/annotate-reference`，带 id、text；需要时提供 targets、focusBoxes、suggestion。targets 是两语各自的精确范围；跨行短语用每行单独的 focusBoxes，贴文字而非整段大矩形。
5. 该操作在**同一 ID** 写 note、整理圈选并保存撤销。后续用户改一个词，同步更新 note、suggestion.after、translationSuggestion 的相关部分，保留位置、颜色、原文、ID 和之前记录。
6. 用当前草稿做增量更新，不把早先读到的整份 JSON 覆盖较新的用户操作。发现用户刚移动框时先重新读取草稿／当前布局，再保存。
7. 刷新**用户正在看的真实标签页**，读到该条新文才算已显示。服务端保存成功不等于用户侧栏刷新成功。不能只回“已经改了”。

辅助脚本：`annotate_reference.py --url http://127.0.0.1:8847 --id UUID --text '批注'`；复杂 targets 使用结构化 POST，避免 shell 引号／命令替换破坏英文或泄露内容。

## 撤销、版本与恢复

根状态保留 source、annotations、deletedAnnotations、undoStates/redoStates、activeId、pageIndex、bilingual、pointSequence、lastCopied、canvasTrimLeft/Right、openingZoom、openingCenter、toolsOpen 等。

- 已有 draft.source.sha256 与新底稿不一致时，先存档并重定位，不能默默在新图上使用旧坐标。
- 不能只按页码迁移批注。用 docId、原句、上下文查找新位置，并重新计算双语范围；不唯一时保留未定位记录。
- 旧画布可作为冻结审阅快照继续看，但必须说明它不是已更新的在线母稿。
- 复制当前 note 的内容优先于过期 suggestion；新措辞写回后同步结构化字段，避免再次复制出旧版。
- 把测试放独立临时 root、独立端口；不要向真实用户的 `/api/draft` 写测试数据。
