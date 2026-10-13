import json
import tempfile
import unittest
from pathlib import Path
from core import Store
from recipe_format import normalize_format, toggle_selection, read_format, load_format

class FakeText:
    def __init__(self):self.tags={'sel':['1.0','1.6']}
    def tag_ranges(self,tag):return self.tags.get(tag,[])
    def compare(self,a,op,b):
        a=tuple(map(int,a.split('.')));b=tuple(map(int,b.split('.')))
        return {'<':a<b,'>':a>b,'<=':a<=b,'>=':a>=b}[op]
    def tag_add(self,tag,a,b):self.tags.setdefault(tag,[]).extend([a,b])
    def tag_remove(self,tag,a,b):self.tags[tag]=[]
    def focus_set(self):pass
    def index(self,value):return '2.5'

class RichRecipeTests(unittest.TestCase):
    def test_styles_can_overlap_toggle_and_roundtrip(self):
        editor=FakeText()
        self.assertTrue(toggle_selection(editor,'bold'))
        self.assertTrue(toggle_selection(editor,'highlight'))
        saved=read_format(editor)
        self.assertEqual(json.loads(saved),{'bold':[['1.0','1.6']],'highlight':[['1.0','1.6']]})
        restored=FakeText();load_format(restored,saved)
        self.assertEqual(read_format(restored),saved)
        toggle_selection(restored,'bold')
        self.assertEqual(json.loads(read_format(restored)),{'highlight':[['1.0','1.6']]})
        restored.tags['sel']=[]
        self.assertFalse(toggle_selection(restored,'bold'))
        for value in ['[]','invalid',{'bold':[['1.6','1.0']]},{'unknown':[]}]:
            with self.assertRaises(ValueError):normalize_format(value)

    def test_existing_notes_finish_format_persistence_duplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'db.sqlite';s=Store(path)
            try:
                s.save_material(code='PAP',name='Papel',unit='un',pack_qty=1,pack_cents=100)
                args=dict(name='Cartão',code='CAR',markup=2,table_cents=200,recipe=[('PAP',1)])
                text='Cortar\nColar'
                pid=s.save_product(production_notes=text,**args)
                for col in ('finish','production_notes_format'):s.db.execute(f'ALTER TABLE products DROP COLUMN {col}')
                s.db.commit();s.close();s=Store(path)
                self.assertEqual(s.products()[0]['production_notes'],text)
                self.assertEqual(s.products()[0]['finish'],'')
                fmt=normalize_format({'bold':[['1.0','1.6']],'highlight':[['2.0','2.5']]})
                s.save_product(id=pid,finish='Holográfico',production_notes=text,production_notes_format=fmt,**args)
                s.close();s=Store(path)
                copied=s.duplicate_product(pid)
                for row in s.products():
                    self.assertEqual(row['production_notes_format'],fmt)
                    self.assertEqual(row['finish'],'Holográfico')
                s.save_product(id=pid,**args)
                self.assertEqual(s.one('SELECT production_notes_format FROM products WHERE id=?',(pid,))[0],fmt)
                # A plain-text caller changing text must not leave stale formatting positions.
                s.save_product(id=pid,production_notes='Novo',finish='',**args)
                self.assertEqual(s.one('SELECT production_notes_format FROM products WHERE id=?',(pid,))[0],'{}')
                self.assertEqual(s.product_cost(pid)[0],100)
                self.assertEqual(s.one('SELECT production_notes FROM products WHERE id=?',(copied,))[0],text)
            finally:s.close()
