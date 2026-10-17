"""Positive and negative information-flow regressions; not a teaching-quality score."""
import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('story_map',HERE/'story-map.py')
lint=importlib.util.module_from_spec(sp);sp.loader.exec_module(lint)
EXAMPLE=json.loads((HERE.parent/'assets/continuity/story-map.example.json').read_text(encoding='utf-8'))

class NarrativeTests(unittest.TestCase):
    def check_failure(self,mutation,needle):
        doc=deepcopy(EXAMPLE);mutation(doc);report=lint.inspect(doc)
        self.assertFalse(report['passed']);self.assertTrue(any(needle in f['message'] for f in report['findings']),report)
    def test_example(self):self.assertTrue(lint.inspect(EXAMPLE)['passed'])
    def test_missing_return(self):self.check_failure(lambda d:d['states'].pop(3),'Unclosed')
    def test_new_scene_on_return(self):self.check_failure(lambda d:d['states'][3].update(scene='new-diagram'),'Return changes')
    def test_unknown_prerequisite(self):self.check_failure(lambda d:d['states'][0]['requires'].append('complete-spectrum'),'not-yet')
    def test_no_origin(self):self.check_failure(lambda d:d['branches'][0].update(originState='future-page'),'origin has not')
    def test_focus_object_absent(self):self.check_failure(lambda d:d['states'][0]['objects'].remove('samples'),'Focus object was absent')
    def test_focus_identity_switched(self):self.check_failure(lambda d:d['states'][1].update(activeObject='pulse'),'Focus active object differs')
    def test_active_object_declared_invisible(self):self.check_failure(lambda d:d['states'][1].update(objects=['pulse']),'Active object is absent')
    def test_return_without_result(self):self.check_failure(lambda d:d['states'][3].update(carries=[]),'does not retain')
    def test_prior_result_forgotten(self):self.check_failure(lambda d:d['states'][6].update(carries=['pulse-response']),'Previously returned')
    def test_no_consumer(self):self.check_failure(lambda d:d['states'][-1].update(requires=['product']),'never used')
    def test_orphaned_branch(self):self.check_failure(lambda d:d['branches'].append({'id':'unused'}),'orphaned')
    def test_undefined_symbol(self):self.check_failure(lambda d:d['states'][2].update(activeObject='g'),'Active object is undefined')
    def test_key_rule_visible_during_use(self):
        doc=deepcopy(EXAMPLE);doc['results']['sample-copies']['keepVisibleDuringUse']=True
        self.assertTrue(lint.inspect(doc)['passed'])
        doc['states'][-1]['carries'].remove('sample-copies')
        report=lint.inspect(doc);self.assertFalse(report['passed'])
        self.assertTrue(any('keepVisibleDuringUse' in f['message'] for f in report['findings']))
    def test_nested_result_stays_in_its_parent_branch(self):
        doc=deepcopy(EXAMPLE);doc['states'][1]['objects']=['samples']
        doc['results']['clock-train']={'statement':'Known periodic sampling impulse train','conditions':['Ideal clock'],'scope':'general'}
        doc['branches'].append({'id':'clock','originState':'sampling-focus','focusObject':'samples','result':'clock-train','returnState':'clock-back'})
        common={'scene':'same-signal-product','context':'inspect-s','activeObject':'samples','branch':'clock',
                'why':'Compute the sampling factor needed by the parent operation','objects':['samples']}
        doc['states'][2]['requires'].append('clock-train')
        doc['states'][2:2]=[
            {**common,'id':'clock-focus','kind':'focus','purpose':'Select the periodic sampling clock','requires':['samples'],'produces':[],'carries':[]},
            {**common,'id':'clock-calculation','kind':'derive','purpose':'Establish the clock train','requires':['samples'],'produces':['clock-train'],'carries':[]},
            {**common,'id':'clock-back','kind':'return','purpose':'Use the clock in the sampling operation','requires':['clock-train'],'produces':[],'carries':['clock-train']}]
        self.assertTrue(lint.inspect(doc)['passed'],lint.inspect(doc))
    def test_mainline_without_forced_branch(self):
        doc={'objects':{'x':'input','y':'output'},'initialKnown':['x'],'results':{},'branches':[],
             'states':[{'id':'apply','kind':'main','scene':'same-data','context':'compute','activeObject':'x',
                        'purpose':'Apply an already known doubling operation','why':'Compute the requested output',
                        'requires':['x'],'produces':['y'],'carries':[]}]}
        self.assertTrue(lint.inspect(doc)['passed'])

if __name__=='__main__':unittest.main()
