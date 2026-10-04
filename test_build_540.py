import tempfile
import unittest
from pathlib import Path
from core import Store

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'test.sqlite'
        self.s=Store(self.path)
        self.m=self.s.save_material(name='Papel',code='PAP',unit='un',pack_qty=1,pack_cents=100)
        self.p=self.s.save_product(name='Cartão',code='CAR',markup=2,table_cents=200,recipe=[('PAP',2)])
    def tearDown(self):
        self.s.close();self.tmp.cleanup()
    def order(self):
        return self.s.save_order(customer='Cliente',due_date='2026-10-10',payment='Pago',production='Novo',notes='',
            items=[dict(product_id=self.p,description='Cartão',qty=3,unit_cents=200)])
    def test_archive_reactivate_preserves_stock_money_and_items(self):
        oid=self.order()
        before=[dict(r) for r in self.s.all('SELECT * FROM stock_movements')]
        self.s.toggle_order(oid)
        self.assertEqual(self.s.order(oid)['active'],0)
        self.assertEqual(self.s.dashboard()['open'],0)
        self.assertEqual(self.s.dashboard()['due'],[])
        self.assertEqual(self.s.dashboard()['revenue'],600)
        self.assertEqual(len(self.s.items(oid)),1)
        self.s.close();self.s=Store(self.path)
        self.assertEqual(self.s.order(oid)['active'],0)
        self.s.toggle_order(oid)
        self.assertEqual(self.s.dashboard()['open'],1)
        self.assertEqual([dict(r) for r in self.s.all('SELECT * FROM stock_movements')],before)
    def test_delete_archived_order_reverses_stock_once(self):
        oid=self.order();self.s.toggle_order(oid);self.s.delete_order(oid)
        self.assertIsNone(self.s.order(oid))
        self.assertEqual(self.s.stock()[0]['balance'],0)
        with self.assertRaises(ValueError):self.s.delete_order(oid)
        self.assertEqual(self.s.stock()[0]['balance'],0)
        self.assertEqual(self.s.dashboard()['revenue'],0)
    def test_protected_products_and_materials_can_be_inactivated(self):
        oid=self.order()
        for action,id in [(self.s.delete_product,self.p),(self.s.delete_material,self.m)]:
            with self.assertRaises(ValueError):action(id)
        self.s.toggle_product(self.p);self.s.toggle_material(self.m)
        self.assertEqual(self.s.product_cost(self.p)[0],200)
        self.assertEqual(self.s.items(oid)[0]['product_id'],self.p)
    def test_component_protection_and_unused_deletion(self):
        parent=self.s.save_product(name='Kit',code='KIT',markup=2,table_cents=400,recipe=[],components=[(self.p,2,'Produção')])
        with self.assertRaises(ValueError):self.s.delete_product(self.p)
        self.s.delete_product(parent);self.s.delete_product(self.p);self.s.delete_material(self.m)
        self.assertEqual(self.s.products(),[]);self.assertEqual(self.s.materials(),[])
        self.assertEqual(self.s.all('PRAGMA foreign_key_check'),[])
    def test_migration_defaults_existing_orders_to_active(self):
        oid=self.order()
        self.s.db.execute('ALTER TABLE orders DROP COLUMN active');self.s.db.commit()
        self.s.close();self.s=Store(self.path)
        self.assertEqual(self.s.order(oid)['active'],1)
        self.assertEqual(self.s.items(oid)[0]['qty'],3)

if __name__=='__main__':unittest.main()
