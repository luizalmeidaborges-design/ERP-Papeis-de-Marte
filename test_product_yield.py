import tempfile
import unittest
from pathlib import Path
from core import Store


class ProductYieldTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'marte.db'
        self.store=Store(self.path)
        mid=self.store.save_material(name='Adesivo',pack_qty=1,unit='folha',pack_cents=1000,variants=['Branco'])
        self.mid=mid;self.vid=self.store.variants(mid)[0]['id']
        self.store.adjust_stock(mid,'entry',10,'Inicial',variant_id=self.vid)
        self.pid=self.product(5)

    def tearDown(self):
        self.store.close();self.temp.cleanup()

    def product(self,n,id=None):
        return self.store.save_product(id=id,name='Chaveiro',code='CHAV',markup=2,
            table_cents=None,recipe=[('ADE',1)],base_yield=n)

    def balance(self):
        return next(r['balance'] for r in self.store.stock() if r['variant_id']==self.vid)

    def order(self,n,id=None,payment='Pendente'):
        return self.store.save_order(id=id,customer='Cliente',due_date='2026-10-10',payment=payment,
            production='Novo',notes='',items=[dict(product_id=self.pid,description='Chaveiro',qty=n,
            unit_cents=400,variants={self.mid:self.vid})])

    def test_cost_and_fractional_consumption_and_reversal(self):
        self.assertEqual(self.store.product_cost(self.pid)[0],200)
        self.assertEqual(self.store.suggested(self.store.products()[0])[0],400)
        for n in (1,5,10,20):
            with self.subTest(quantity=n):
                oid=self.order(n)
                self.assertAlmostEqual(self.balance(),10-n/5)
                self.store.delete_order(oid)
                self.assertAlmostEqual(self.balance(),10)

    def test_payment_edit_does_not_recalculate_old_stock(self):
        oid=self.order(1)
        self.product(10,self.pid)
        self.order(1,oid,payment='Pago')
        self.assertAlmostEqual(self.balance(),9.8)
        self.order(5,oid)
        self.assertAlmostEqual(self.balance(),9.5)
        self.store.delete_order(oid)
        self.assertAlmostEqual(self.balance(),10)

    def test_invalid_yield_does_not_change_product(self):
        for n in (0,-1,1.5,True,1000001):
            with self.subTest(yield_value=n):
                with self.assertRaises(ValueError):self.product(n,self.pid)
        self.assertEqual(self.store.products()[0]['base_yield'],5)

    def test_yield_survives_restart_and_legacy_defaults_to_one(self):
        self.store.close();self.store=Store(self.path)
        self.assertEqual(self.store.products()[0]['base_yield'],5)
        self.store.db.execute('ALTER TABLE products DROP COLUMN base_yield')
        self.store.db.commit()
        self.store.close();self.store=Store(self.path)
        self.assertEqual(self.store.products()[0]['base_yield'],1)
        self.assertEqual(self.store.product_cost(self.pid)[0],1000)
