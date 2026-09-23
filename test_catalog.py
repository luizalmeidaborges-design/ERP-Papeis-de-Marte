import sqlite3
import tempfile
import unittest
from pathlib import Path
from core import Store


class CatalogTests(unittest.TestCase):
    def test_price_date_and_manual_code_preserve_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'marte.db'
            store=Store(path)
            try:
                mid=store.save_material(name='Offset',size='A4',grammage='150',pack_qty=100,
                    unit='un',pack_cents=2500,price_date='2026-09-23')
                pid=store.save_product(name='Bala personalizada',code='KIT-100',markup=1.8,
                    table_cents=3000,recipe=[('OFFA4150',5)])
                order=store.save_order(customer='Teste',due_date='2026-10-01',payment='Pendente',
                    production='Novo',notes='',items=[{'product_id':pid,'description':'Kit',
                    'qty':1,'unit_cents':3000}])
                store.save_product(id=pid,name='Bala personalizada',code='KIT-200',markup=1.8,
                    table_cents=3000,recipe=[('OFFA4150',5)])
                self.assertEqual(store.items(order)[0]['product_id'],pid)
                self.assertEqual(store.product_cost(pid)[0],125)
                with self.assertRaises(ValueError):
                    store.save_product(name='Sem código',code='',markup=1.8,
                        table_cents=3000,recipe=[('OFFA4150',1)])
                with self.assertRaises(sqlite3.IntegrityError):
                    store.save_product(name='Duplicado',code='kit-200',markup=1.8,
                        table_cents=3000,recipe=[('OFFA4150',1)])
                with self.assertRaises(ValueError):
                    store.save_material(id=mid,name='Offset',size='A4',grammage='150',
                        pack_qty=100,unit='un',pack_cents=2500,price_date='2026-02-30')
            finally:store.close()
            store=Store(path)
            try:
                self.assertEqual(store.materials()[0]['price_date'],'2026-09-23')
                self.assertEqual(store.products()[0]['code'],'KIT-200')
                self.assertEqual(len(store.orders()),1)
            finally:store.close()

    def test_old_database_gains_optional_date_without_changing_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'marte.db'
            store=Store(path)
            try:
                store.save_material(name='Papel',pack_qty=1,unit='un',pack_cents=50)
                store.db.execute('ALTER TABLE materials DROP COLUMN price_date')
                store.db.commit()
            finally:store.close()
            store=Store(path)
            try:
                row=store.materials()[0]
                self.assertEqual(row['name'],'Papel')
                self.assertEqual(row['price_date'],'')
                self.assertEqual(row['pack_cents'],50)
            finally:store.close()
