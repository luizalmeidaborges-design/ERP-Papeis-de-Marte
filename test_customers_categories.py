"""Regressões de migração e categorias sobre a base 2.2.0."""
import tempfile
import unittest
from pathlib import Path
from core import Store


class CustomersCategoriesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'marte.db'
        self.store=Store(self.path)

    def tearDown(self):self.store.close();self.tmp.cleanup()

    def test_customer_create_edit_reopen_and_validation(self):
        cid=self.store.save_customer(name=' Thayna ',phone='11912345678',email='t@example.com',birthday='1995-04-20',address='Rua A, 10')
        self.store.save_customer(id=cid,name='Thayna Donadei',phone='11912345678',email='t@example.com',birthday='1995-04-20',address='Rua B, 20')
        for values in [dict(name=''),dict(name='X',email='sem-arroba'),dict(name='X',birthday='2026-02-30'),dict(name='X',birthday='2999-01-01')]:
            with self.assertRaises(ValueError):self.store.save_customer(**values)
        with self.assertRaises(ValueError):self.store.save_customer(id=999,name='Não existe')
        self.store.close();self.store=Store(self.path)
        self.assertEqual(len(self.store.customers()),1)
        c=self.store.customers()[0]
        self.assertEqual((c['id'],c['name'],c['address']),(cid,'Thayna Donadei','Rua B, 20'))
        self.assertEqual(c['phone'],'11912345678');self.assertEqual(c['birthday'],'1995-04-20')

    def test_legacy_database_gains_category_preserving_orders_and_stock(self):
        mid=self.store.save_material(name='Papel',code='PAP',pack_qty=1,unit='folha',pack_cents=600)
        self.store.adjust_stock(mid,'entry',10,'Inicial')
        pid=self.store.save_product(name='Marcador',code='MAR',markup=2,table_cents=None,base_yield=6,recipe=[('PAP',1)])
        oid=self.store.save_order(customer='Cliente histórico',due_date='2026-10-01',payment='Pendente',production='Novo',notes='',
            items=[dict(product_id=pid,description='Marcador',qty=1,unit_cents=200)])
        order=dict(self.store.order(oid));stock=[dict(r) for r in self.store.stock()]
        self.store.db.execute('ALTER TABLE materials DROP COLUMN category')
        self.store.db.execute('DROP TABLE customers');self.store.db.commit()
        self.store.close();self.store=Store(self.path)
        self.assertEqual(self.store.materials()[0]['category'],'Produção')
        self.assertEqual(dict(self.store.order(oid)),order)
        self.assertEqual([dict(r) for r in self.store.stock()],stock)
        self.assertEqual(self.store.product_cost(pid)[0],100)
        self.assertEqual(self.store.customers(),[])

    def test_category_groups_share_same_pricing_and_fractional_stock_rules(self):
        paper=self.store.save_material(name='Papel',code='PAP',pack_qty=1,unit='folha',pack_cents=600,category='Produção')
        bag=self.store.save_material(name='Saco',code='SAC',pack_qty=100,unit='un',pack_cents=1000,category='Embalagem')
        pid=self.store.save_product(name='Marcador',code='MAR',markup=2,table_cents=None,base_yield=6,recipe=[('PAP',1),('SAC',6)])
        self.assertEqual([r['category'] for r in self.store.recipe(pid)],['Produção','Embalagem'])
        self.assertEqual(self.store.product_cost(pid)[0],110)
        self.assertEqual(self.store.suggested(self.store.products()[0])[0],220)
        oid=self.store.save_order(customer='Teste',due_date='2026-10-01',payment='Pendente',production='Novo',notes='',
            items=[dict(product_id=pid,description='Marcador',qty=1,unit_cents=220)])
        balances={r['id']:r['balance'] for r in self.store.stock()}
        self.assertAlmostEqual(balances[paper],-1/6);self.assertEqual(balances[bag],-1)
        self.store.delete_order(oid)
        self.assertTrue(all(r['balance']==0 for r in self.store.stock()))

    def test_edit_category_preserves_recipe_and_omitted_category_keeps_value(self):
        mid=self.store.save_material(name='Saco',code='SAC',pack_qty=1,unit='un',pack_cents=10)
        pid=self.store.save_product(name='Produto',code='PRO',markup=2,table_cents=None,recipe=[('SAC',2)])
        self.store.save_material(id=mid,name='Saco',code='SAC',pack_qty=1,unit='un',pack_cents=10,category='Embalagem')
        self.store.save_material(id=mid,name='Saco',code='SAC',pack_qty=1,unit='un',pack_cents=20)
        row=self.store.recipe(pid)[0]
        self.assertEqual((row['category'],row['qty']),('Embalagem',2))
        self.assertEqual(self.store.product_cost(pid)[0],40)
        with self.assertRaises(ValueError):
            self.store.save_material(id=mid,name='Saco',code='SAC',pack_qty=1,unit='un',pack_cents=99,category='Inválida')
        self.assertEqual(self.store.product_cost(pid)[0],40)

if __name__=='__main__':unittest.main()
