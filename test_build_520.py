"""Migration, catalog identity and customer/recipe integration regressions."""
import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path
from core import Store
from test_build_510 import ProductFormTests


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db.sqlite'
        self.s=Store(self.path)
        self.mid=self.s.save_material(code='PAP',name='Papel',pack_qty=100,pack_cents=2000,unit='un')
        self.pid=self.s.save_product(code='PRO',name='Produto',markup=2,table_cents=400,recipe=[('PAP',2)])
    def tearDown(self):self.s.close();self.tmp.cleanup()
    def order(self,**kwargs):
        args=dict(customer='Cliente',due_date='2026-10-01',payment='Pendente',production='Novo',notes='',
            items=[dict(product_id=self.pid,description='Produto',qty=1,unit_cents=400)])
        args.update(kwargs);return self.s.save_order(**args)
    def test_rename_updates_all_recipes_and_preserves_identity(self):
        second=self.s.duplicate_product(self.pid);oid=self.order()
        stock=[dict(r) for r in self.s.stock()]
        self.s.save_material(id=self.mid,code='NOVO',name='Papel',pack_qty=100,pack_cents=2000,unit='un')
        for pid in (self.pid,second):self.assertEqual(self.s.recipe(pid)[0]['material_code'],'NOVO')
        self.s.save_product(id=self.pid,code='RENOMEADO',name='Produto',markup=2,table_cents=400,recipe=[('NOVO',2)])
        self.assertEqual(self.s.items(oid)[0]['product_id'],self.pid)
        self.assertEqual([r['balance'] for r in self.s.stock()],[r['balance'] for r in stock])
        self.s.save_material(code='OUTRO',name='Outro',pack_qty=1,pack_cents=1,unit='un')
        with self.assertRaises(sqlite3.IntegrityError):
            self.s.save_material(id=self.mid,code='OUTRO',name='Papel',pack_qty=1,pack_cents=1,unit='un')
        self.assertEqual(self.s.recipe(self.pid)[0]['material_code'],'NOVO')
    def test_categories_sections_duplication_and_reopen(self):
        self.s.add_category('materials','Papéis');self.s.add_category('products','Lembranças')
        self.s.save_material(id=self.mid,code='PAP',name='Papel',pack_qty=100,pack_cents=2000,unit='un',category='Papéis')
        self.s.save_product(id=self.pid,code='PRO',name='Produto',markup=2,table_cents=400,
            category='Lembranças',recipe=[('PAP',2),('PAP',1)],sections=['Embalagem','Produção'])
        other=self.s.duplicate_product(self.pid)
        self.assertNotEqual(self.s.products()[0]['code'],self.s.products()[1]['code'])
        self.s.delete_category('materials','Papéis');self.s.delete_category('products','Lembranças')
        self.s.close();self.s=Store(self.path)
        for pid in (self.pid,other):
            self.assertEqual([r['section'] for r in self.s.recipe(pid)],['Embalagem','Produção'])
            self.assertEqual(self.s.product_cost(pid)[0],60)
        self.assertTrue(all(p['category']=='Sem categoria' for p in self.s.products()))
        self.assertEqual(self.s.all('PRAGMA foreign_key_check'),[])
    def test_customer_reuse_new_ambiguous_and_failed_order(self):
        cid=self.s.save_customer(name='Maria Silva',phone='11999999999')
        oid=self.order(customer='  MARIA   SILVA ')
        self.assertEqual(self.s.order(oid)['customer_id'],cid)
        self.assertEqual(len(self.s.customers()),1)
        self.order(customer='Nova cliente');self.assertEqual(len(self.s.customers()),2)
        cid2=self.s.save_customer(name='Maria Silva',phone='11888888888')
        with self.assertRaises(ValueError):self.order(customer='Maria Silva')
        selected=self.order(customer='Maria Silva',customer_id=cid2)
        self.assertEqual(self.s.order(selected)['customer_id'],cid2)
        with self.assertRaises(ValueError):self.order(customer='Não salvar',items=[])
        self.assertEqual(len(self.s.customers()),3)


class FormTests(ProductFormTests):
    def test_automatic_code_manual_override_and_unrestricted_selectors(self):
        self.form();self.fields['NOME DO PRODUTO'].set('Marcador')
        code=self.fields['CÓDIGO DO PRODUTO'];self.assertEqual(code.get(),'MAR')
        code.set('MEU01');self.fields['TAMANHO'].set('A4');self.assertEqual(code.get(),'MEU01')
        self.assertEqual(self.combos[1].options['values'],self.combos[2].options['values'])
        # Papel belongs to Produção, but must stay in Embalagem when chosen there.
        self.combos[2].set(self.combos[2].options['values'][0]);self.actions['Adicionar'][1]()
        self.actions['Salvar produto'][0]()
        self.assertEqual(self.store.recipe(self.store.products()[0]['id'])[0]['section'],'Embalagem')

if __name__=='__main__':unittest.main()
