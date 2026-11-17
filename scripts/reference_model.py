import copy,time

def make_reference(data,draft,annotation_id):
 if draft.get('source',{}).get('sha256')!=data['source']['sha256']:raise ValueError('底稿版本已变化，请重新引用')
 n=next((n for n in draft.get('annotations',[]) if n['id']==annotation_id),None)
 if not n:raise ValueError('这处定位不存在或已删除')
 if n.get('sourceVersion')!=data['source']['sha256']:raise ValueError('定位属于其他版本')
 d=next(d for d in data['documents'] if d['id']==n['docId'])
 for a in n.get('anchors',[]):
  p=next((p for p in d[n['lang']] if p['id']==a['paragraphId']),None)
  if not p or p['text'].encode('utf-16-le')[a['start']*2:a['end']*2].decode('utf-16-le')!=a['quote']:raise ValueError('定位原文不一致')
 pair=None
 for a in n.get('anchors',[]):
  found={l:next((p for p in d.get(l,[]) if p['id']==a['paragraphId']),None) for l in ['en','zh']}
  if all(found.values()):
   pair={l:{'paragraphId':p['id'],'quote':p['text']} for l,p in found.items()};break
 if n.get('stage')=='annotation' and n.get('pairedReferences'):pair=copy.deepcopy(n['pairedReferences'])
 return copy.deepcopy({'id':n['id'],'label':n['docId']+':'+n['id'][:8],'source':data['source'],'docId':n['docId'],'page':d['page'],'title':d['title'],'lang':n['lang'],'anchors':n.get('anchors',[]),'quote':n.get('quote',''),'region':n.get('region'),'attention':n.get('attention'),'focusBoxes':n.get('focusBoxes'),'pairedReferences':pair,'textColor':n.get('textColor'),'modification':n.get('note',''),'suggestion':n.get('suggestion'),'stage':'reference-only','referencedAt':int(time.time()*1000)})

def annotate(data,draft,reference,text,targets=None,focus_boxes=None,suggestion=None):
 if reference['source']['sha256']!=data['source']['sha256']:raise ValueError('引用版本已变化')
 if not text.strip():raise ValueError('需先在聊天说明具体改法')
 make_reference(data,draft,reference['id'])
 out=copy.deepcopy(draft);out['deletedAnnotations']=(out.get('deletedAnnotations') or [])[:2];snapshot={k:copy.deepcopy(draft.get(k)) for k in ['deletedAnnotations','pageIndex','lang','bilingual','pointSequence']};snapshot.update(notes=copy.deepcopy(draft['annotations']),selected=draft.get('activeId'))
 out['undoStates']=(out.get('undoStates',[])+[snapshot])[-20:];out['redoStates']=[]
 n=next(n for n in out['annotations'] if n['id']==reference['id']);n['note']=text.strip();n['stage']='annotation';
 if targets:
  document=next(d for d in data['documents'] if d['id']==n['docId'])
  for lang,a in targets.items():
   if lang not in ['en','zh']:raise ValueError('引用语言无效')
   p=next((p for p in document.get(lang,[]) if p['id']==a.get('paragraphId')),None)
   if not p or not isinstance(a.get('start'),int) or not isinstance(a.get('end'),int) or a['start']<0 or a['end']<=a['start'] or p['text'].encode('utf-16-le')[a['start']*2:a['end']*2].decode('utf-16-le')!=a.get('quote'):raise ValueError('精确引文与原稿不一致')
  n.setdefault('locatorOriginalAnchors',copy.deepcopy(n['anchors']));n['anchors']=[copy.deepcopy(targets[n['lang']])];n['quote']=targets[n['lang']]['quote'];n['pairedReferences']=copy.deepcopy(targets)
 if suggestion:
  before=suggestion.get('before','');after=suggestion.get('after','');detail=suggestion.get('detail','')
  if before!=n['quote'] or not isinstance(after,str) or not after.strip():raise ValueError('替换建议需对应当前原文')
  n['suggestion']=copy.deepcopy(suggestion);n['note']=before+'\n↓\n'+after+(('\n'+detail) if detail else '')
 if focus_boxes:
  import math
  for boxes in focus_boxes.values():
   for box in boxes:
    if not all(isinstance(box.get(k),(int,float)) and math.isfinite(box[k]) for k in ['x','y','w','h']) or min(box['x'],box['y'])<0 or min(box['w'],box['h'])<=0 or box['x']+box['w']>1.000001 or box['y']+box['h']>1.000001:raise ValueError('圈选坐标无效')
  n['focusBoxes']=copy.deepcopy(focus_boxes)
 if n.get('attention'):n['attention']['cleaned']=True
 n['card']=n.get('card') or {'assignedAt':int(time.time()*1000)};out['activeId']=n['id'];return out


def reference_prompt(reference,file):
 lines=['[引用 '+reference['label']+'](<'+str(file)+'>)','定位ID：'+reference['id'],'英文原文：'+(reference.get('pairedReferences') or {}).get('en',{}).get('quote',reference.get('quote',''))]
 if reference.get('pairedReferences'):lines+=['中文对应：'+reference['pairedReferences']['zh']['quote']]
 lines+=['修改建议：',reference.get('modification') or '尚未填写；我将接着说明怎么修改，先不要生成批注。']
 return '\n'.join(lines)


def make_canvas_reference(data,draft,doc_id,reference_id):
 if draft.get('source',{}).get('sha256')!=data['source']['sha256']:raise ValueError('底稿版本已变化')
 document=next((d for d in data['documents'] if d['id']==doc_id),None)
 if not document:raise ValueError('画布篇目不存在')
 refs=[make_reference(data,draft,n['id']) for n in draft.get('annotations',[]) if n['docId']==doc_id]
 return {'id':reference_id,'kind':'canvas-reference','source':copy.deepcopy(data['source']),'docId':doc_id,'page':document['page'],'title':document['title'],'annotations':refs,'referencedAt':int(time.time()*1000)}
