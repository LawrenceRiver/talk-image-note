---
name: talk-image-note
description: >-
  Open a local original-image annotation canvas for paper sections and document pages.
  Preserve source images, collect attention marks and spoken revision instructions in chat,
  and update linked annotations without changing the underlying document.
---

# talk-image-&note

把论文或文档原页放在本地画布，先圈画定位，在聊天里说明，再将确认的微调写进同一条旁批。

## 使用

- 继续已有画布：读工作区 `data.json`、`annotations/draft.json` 和必要的 `annotations/latest-reference.json`。保留源图、笔迹、批注 ID、手动位置和历史。
- 新建：使用 `scripts/bootstrap_workspace.py --root /absolute/workspace`，再用 `scripts/import_images.py --root /absolute/workspace page1.png page2.png` 导入原图。实际工作区必须放在本仓库外。
- 启动：`python scripts/server.py --root /absolute/workspace --port 8847`。只监听本机。检查端口归属，不终止其他任务的服务。
- 在宿主侧栏打开 `http://127.0.0.1:8847/`；没有宿主工具时用普通浏览器。用实际截图确认图片加载成功，不能仅凭文字层或 HTTP 200 判断。
- 编辑前读 [画布约定](references/canvas-contract.md)；状态、定位和 API 见 [工作区协议](references/workflow-and-state.md)；交付见 [导出与存档](references/exports-and-archive.md)。

## 批注规则

1. 原件始终保留为图片，字体、版式和已有高亮不变。OCR 仅用于透明定位，不把重排正文当作原件。
2. 默认只加批注。用户确认“批注上去”不等于批准改底稿。没有明确授权，不改源文件。
3. 辅助笔迹先停留；在用户解释改法后，才将同一条 ID 整理为精确圈选、引线与旁批。不圈整段代替短语。
4. 微调保留作者框架和已确认措辞。逐段口述时返回完整当前段落；只修当次改点及必要语法。研究设想不自动变成已完成成果，不补造实验或指标。
5. 一处一条记录，重叠改点合并。明确替换用“原文 ↓ 改后”。后续纠正词语必须更新同一条批注及结构化字段，保存后刷新用户正在看的页面并验证。
6. 定位同时核对文档 ID、原句、上下文和源版本。字符范围采用 UTF-16。双语各算坐标，没有可靠译稿不伪造对应。
7. 新的正文修改标记可用薄荷绿 D7F2DE 加下划线，只覆盖实际改点；原图已有高亮不动。旁批颜色按用户选择保留。
8. 导出图片、保存可编辑 HTML、冻结存档和应用底稿是独立动作。复制不等于发送，保存不等于已显示。

## 数据边界

这是本地单用户工具，不是多人同步服务。禁止将它直接开放到公网；没有认证与团队权限。
本技能不接入云盘、在线文档或邮箱，不包含同步、上传、评论账号流程。
原文、截图、批注、导出、压缩包和账号信息只属于本地工作区，不能放进技能仓库。
发布前运行 `python scripts/check_release.py`，并检查待提交文件清单与差异。

## 验证

`node --test tests/*.test.cjs`

`python -m unittest discover -s tests -p '*_test.py'`

检查图片解码、翻页、引用、同 ID 更新、松手结束拖拽、撤销删除、导出完整性。仅在隔离工作区测试，不能覆盖真实笔迹。
