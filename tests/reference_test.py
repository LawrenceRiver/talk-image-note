import unittest,importlib.util,copy
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'scripts/reference_model.py';R=None
if p.exists():
 s=importlib.util.spec_from_file_location('reference_model',p);R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
class ReferenceTest(unittest.TestCase):
 def setUp(self):
  self.data={'source':{'sha256':'v1'},'documents':[{'id':'DOC01','page':1,'title':'Methods','en':[{'id':'p','text':'Exact English'}],'zh':[{'id':'p','text':'对应中文'}],'images':{}}]};self.draft={'source':self.data['source'],'annotations':[{'id':'full-id','docId':'DOC01','lang':'en','sourceVersion':'v1','anchors':[{'paragraphId':'p','start':0,'end':13,'quote':'Exact English'}],'quote':'Exact English','note':'','attention':{'points':[[.1,.2]]},'stage':'locator'}]}
 def test_reference_is_location_only_and_does_not_create_comment(self):
  self.assertIsNotNone(R,'reference model exists');before=copy.deepcopy(self.draft);ref=R.make_reference(self.data,self.draft,'full-id');self.assertEqual(ref['id'],'full-id');self.assertEqual(ref['pairedReferences']['zh']['quote'],'对应中文');self.assertEqual(self.draft,before);self.assertNotIn('card',self.draft['annotations'][0])
 def test_annotation_requires_later_text_and_keeps_same_anchor(self):
  self.assertIsNotNone(R);ref=R.make_reference(self.data,self.draft,'full-id');out=R.annotate(self.data,self.draft,ref,'保留原来的感受，只微调衔接。');self.assertEqual(out['annotations'][0]['stage'],'annotation');self.assertEqual(out['annotations'][0]['id'],'full-id');self.assertTrue(out['annotations'][0]['attention'].get('cleaned',False));self.assertEqual(len(out['undoStates']),1);self.assertEqual(self.draft['annotations'][0]['note'],'')
 def test_exact_bilingual_target_ranges_replace_only_the_selected_phrase(self):
  self.assertIsNotNone(R);ref=R.make_reference(self.data,self.draft,'full-id');targets={'en':{'paragraphId':'p','start':6,'end':13,'quote':'English'},'zh':{'paragraphId':'p','start':2,'end':4,'quote':'中文'}}
  out=R.annotate(self.data,self.draft,ref,'补课号',targets=targets,focus_boxes={'en':[{'x':.1,'y':.2,'w':.3,'h':.02}]});self.assertEqual(out['annotations'][0]['quote'],'English');self.assertEqual(out['annotations'][0]['pairedReferences']['zh']['quote'],'中文');self.assertEqual(out['annotations'][0]['focusBoxes']['en'][0]['x'],.1)
 def test_quote_contains_original_bilingual_text_and_modification(self):
  self.assertTrue(hasattr(R,'reference_prompt'),'reference prompt builder exists');self.draft['annotations'][0]['note']='Exact English\n↓\nIMT 570 Exact English';ref=R.make_reference(self.data,self.draft,'full-id');prompt=R.reference_prompt(ref,'/workspace/reference.json');self.assertIn('Exact English',prompt);self.assertIn('对应中文',prompt);self.assertIn('修改建议',prompt);self.assertIn('↓',prompt);self.assertEqual(ref['modification'],self.draft['annotations'][0]['note'])
 def test_whole_canvas_reference_includes_each_live_id_and_suggestion(self):
  self.assertTrue(hasattr(R,'make_canvas_reference'));self.draft['annotations'][0]['note']='保留措辞';second=copy.deepcopy(self.draft['annotations'][0]);second['id']='second-id';second['note']='补方法说明';self.draft['annotations'].append(second);whole=R.make_canvas_reference(self.data,self.draft,'DOC01','canvas-test');self.assertEqual(whole['kind'],'canvas-reference');self.assertEqual([r['id'] for r in whole['annotations']],['full-id','second-id']);self.assertEqual(whole['annotations'][1]['modification'],'补方法说明')
 def test_stale_reference_is_rejected(self):
  self.assertIsNotNone(R);ref=R.make_reference(self.data,self.draft,'full-id');self.data['source']['sha256']='v2'
  with self.assertRaises(ValueError):R.annotate(self.data,self.draft,ref,'改这里')
if __name__=='__main__':unittest.main()
