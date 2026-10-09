import tempfile
import unittest
from pathlib import Path
from core import Store

class ProductNotesTests(unittest.TestCase):
    def test_notes_migration_persistence_copy_and_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'db.sqlite';s=Store(path)
            try:
                s.save_material(code='PAP',name='Papel',unit='un',pack_qty=1,pack_cents=100)
                args=dict(name='Cartão',code='CAR',markup=2,table_cents=200,recipe=[('PAP',1)])
                pid=s.save_product(**args)
                s.db.execute('ALTER TABLE products DROP COLUMN production_notes');s.db.commit()
                s.close();s=Store(path)
                self.assertEqual(s.products()[0]['production_notes'],'')
                text='1 folha A4 → 6 peças\n  Cortar 5 × 10 cm\nColar e embalar.\n'
                s.save_product(id=pid,production_notes=text,**args)
                s.close();s=Store(path)
                self.assertEqual(s.products()[0]['production_notes'],text)
                s.save_product(id=pid,**args)
                self.assertEqual(s.products()[0]['production_notes'],text)
                copied=s.duplicate_product(pid)
                self.assertEqual(s.one('SELECT production_notes FROM products WHERE id=?',(copied,))[0],text)
                s.save_product(id=pid,production_notes='',**args)
                self.assertEqual(s.one('SELECT production_notes FROM products WHERE id=?',(pid,))[0],'')
                self.assertEqual(s.product_cost(pid)[0],100)
                with self.assertRaises(ValueError):s.save_product(id=pid,production_notes=123,**args)
            finally:s.close()

    def test_form_applies_draft_only_when_product_is_saved(self):
        import test_build_510
        harness=test_build_510.ProductFormTests()
        harness.setUp()
        try:
            harness.form();harness.add_material(0)
            harness.fields['NOME DO PRODUTO'].set('Produto')
            harness.fields['CÓDIGO DO PRODUTO'].set('PRO')
            opened=[]
            def editor(parent,initial,apply):
                opened.append(initial);apply('Cortar → Colar\nEmbalar')
            harness.ui.product_notes_dialog=editor
            harness.actions['Receita do Produto'][0]()
            self.assertEqual(harness.store.products(),[])
            harness.actions['Receita do Produto'][0]()
            self.assertEqual(opened,['','Cortar → Colar\nEmbalar'])
            harness.actions['Salvar produto'][0]()
            self.assertEqual(harness.store.products()[0]['production_notes'],'Cortar → Colar\nEmbalar')
        finally:
            harness.doCleanups();harness.tearDown()
