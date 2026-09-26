import tempfile
import unittest
from pathlib import Path
from core import Store


class FinishTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'db.sqlite'
        self.store=Store(self.path)
        self.store.ensure_finish_catalog()
        self.finishes={r['key']:dict(r) for r in self.store.finishes()}
        rows=[]
        for key,paid in [('brilhante',1000),('fosco',2000),('holografico',3000)]:
            f=self.finishes[key]
            rows.append(dict(key=key,material_id=f['material_id'],extra_cents=f['extra_cents'],pack_qty=10,pack_cents=paid))
            self.store.adjust_stock(f['material_id'],'entry',20,'Inicial')
        self.store.configure_finishes(rows)
        self.paper=self.store.save_material(name='Papel',code='PAP',pack_qty=1,unit='un',pack_cents=1264)
        self.pid=self.store.save_product(name='Chaveiro',code='CHV',markup=1.8,table_cents=None,
                 base_yield=5,recipe=[('PAP',1),('BOPBRI30',1)])

    def tearDown(self):
        self.store.close();self.temp.cleanup()

    def balance(self,key):
        return next(r['balance'] for r in self.store.stock() if r['id']==self.finishes[key]['material_id'])

    def save(self,key,qty=1,id=None,payment='Pendente',item=None):
        item=item or dict(product_id=self.pid,description='Chaveiro',qty=qty,variants={},**self.store.finish_quote(self.pid,key))
        return self.store.save_order(id=id,customer='Cliente',due_date='2026-10-01',payment=payment,
                                    production='Novo',notes='',items=[item])

    def test_exact_user_yield_example_and_stored_fields(self):
        row=self.store.products()[0]
        self.assertAlmostEqual(row['cost_total_cents'],1364)
        self.assertAlmostEqual(row['cost_unit_cents'],272.8)
        self.assertEqual(row['suggested_cents'],491)
        quote=self.store.finish_quote(self.pid)
        self.assertEqual(quote['unit_cents'],491)

    def test_substitution_surcharge_and_yield_without_changing_recipe(self):
        recipe=[dict(r) for r in self.store.recipe(self.pid)]
        q=self.store.finish_quote(self.pid,'fosco')
        self.assertAlmostEqual(q['cost_unit_cents'],292.8)
        self.assertEqual(q['unit_cents'],827)
        oid=self.save('fosco',5)
        self.assertEqual(self.balance('fosco'),19)
        self.assertEqual(self.balance('brilhante'),20)
        self.assertEqual([dict(r) for r in self.store.recipe(self.pid)],recipe)
        self.store.delete_order(oid)
        self.assertEqual(self.balance('fosco'),20)

    def test_change_finish_reverses_old_lamination(self):
        oid=self.save('fosco')
        self.assertAlmostEqual(self.balance('fosco'),19.8)
        self.save('holografico',id=oid)
        self.assertEqual(self.balance('fosco'),20)
        self.assertAlmostEqual(self.balance('holografico'),19.8)
        self.assertEqual(self.balance('brilhante'),20)

    def test_snapshot_survives_price_changes_and_payment_edit(self):
        oid=self.save('fosco');item=self.store.items(oid)[0]
        self.store.db.execute('UPDATE materials SET pack_cents=4000 WHERE id=?',(self.finishes['fosco']['material_id'],))
        self.store.db.commit()
        self.save('fosco',id=oid,payment='Pago',item=item)
        restored=self.store.items(oid)[0]
        self.assertEqual(restored['unit_cents'],827)
        self.assertAlmostEqual(restored['cost_unit_cents'],292.8)
        self.assertAlmostEqual(self.balance('fosco'),19.8)
        self.store.close();self.store=Store(self.path)
        self.assertEqual(self.store.items(oid)[0]['finish_name'],'Fosco Anti-risco')

    def test_price_cache_updates_from_purchases(self):
        self.store.save_purchase(items=[dict(material_id=self.paper,qty=1,total_cents=2264)])
        row=self.store.products()[0]
        self.assertAlmostEqual(row['cost_total_cents'],2364)
        self.assertAlmostEqual(row['cost_unit_cents'],472.8)
        self.assertEqual(row['suggested_cents'],851)

    def test_catalog_is_idempotent_and_missing_prices_block_quotes(self):
        self.store.ensure_finish_catalog()
        self.assertEqual(len(self.store.finishes()),3)
        self.store.db.execute('UPDATE materials SET pack_cents=0 WHERE id=?',(self.finishes['holografico']['material_id'],))
        with self.assertRaises(ValueError):self.store.finish_quote(self.pid,'holografico')
        self.store.db.rollback()

    def test_legacy_quotes_remain_readable_and_bopp_can_now_be_in_product(self):
        pid=self.store.save_product(name='Sem laminar',code='SEM',markup=2,table_cents=3000,recipe=[('PAP',1)])
        self.assertEqual(self.store.finish_quote(pid)['unit_cents'],3000)
        with self.assertRaises(ValueError):self.store.finish_quote(pid,'fosco')
        pid=self.store.save_product(name='Fosco',code='FOS',markup=2,table_cents=None,recipe=[('BOPFOS30',1)])
        self.assertEqual(self.store.product_cost(pid)[0],200)
