"""Testa exclusão de pedidos sem precisar de dados privados da cliente."""
import tempfile
import unittest
import sqlite3
from pathlib import Path

from core import Store


class PublicOrderTests(unittest.TestCase):
    def test_partial_payment_balance_survives_restart_and_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'marte.db'
            item={'product_id':None,'description':'Encomenda','qty':2,'unit_cents':1500}
            store=Store(path)
            try:
                order_id=store.save_order(customer='Cliente',due_date='2026-10-10',
                   payment='Parcial',paid_cents=1000,production='Novo',notes='',items=[item])
                self.assertEqual(store.orders()[0]['remaining_cents'],2000)
                self.assertEqual(store.orders()[0]['paid_cents'],1000)
                with self.assertRaisesRegex(ValueError,'maior que zero e menor'):
                    store.save_order(id=order_id,customer='Cliente',due_date='2026-10-10',
                       payment='Parcial',paid_cents=3000,production='Novo',notes='',items=[item])
                self.assertEqual(store.order(order_id)['paid_cents'],1000)
            finally:store.close()
            store=Store(path)
            try:
                self.assertEqual(store.orders()[0]['remaining_cents'],2000)
                store.save_order(id=order_id,customer='Cliente',due_date='2026-10-10',
                    payment='Pago',production='Novo',notes='',items=[item])
                self.assertEqual(store.orders()[0]['remaining_cents'],0)
                self.assertEqual(store.order(order_id)['paid_cents'],3000)
            finally:store.close()

    def test_legacy_orders_migrate_without_losing_payment_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'marte.db'
            with sqlite3.connect(path) as db:
                db.execute('''CREATE TABLE orders (id INTEGER PRIMARY KEY,number TEXT NOT NULL UNIQUE,
                    customer TEXT NOT NULL,created_date TEXT,due_date TEXT,
                    payment TEXT NOT NULL,production TEXT NOT NULL,notes TEXT NOT NULL)''')
                db.execute("INSERT INTO orders VALUES (1,'PM0001','Cliente antigo','2026-09-01',"
                           "'2026-10-10','Pago','Entregue','Importado')")
            db.close()
            store=Store(path)
            try:
                store.db.execute("INSERT INTO order_items(order_id,description,qty,unit_cents) VALUES (1,'Item',1,4500)")
                store.db.commit()
                self.assertEqual(store.order(1)['payment'],'Pago')
                self.assertEqual(store.order(1)['paid_cents'],0)
                self.assertEqual(store.orders()[0]['remaining_cents'],0)
            finally:store.close()

    def test_delete_restores_variant_stock_and_preserves_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp)/'marte.db')
            try:
                store.save_material(name='Cartolina',size='A4',grammage='150',
                    pack_qty=10,unit='un',pack_cents=1000,variants=['Vermelho','Azul'])
                material=store.one("SELECT id FROM materials WHERE code='CARA4150'")
                red=store.variants(material['id'])[0]['id']
                product_id=store.save_product(name='Caderno',size='A4',grammage='',
                    markup=1.8,table_cents=2000,recipe=[('CARA4150',2)])
                store.adjust_stock(material['id'],'entry',5,'Estoque inicial',variant_id=red)
                item={'product_id':product_id,'description':'Caderno','qty':2,
                      'unit_cents':2000,'variants':{material['id']:red}}
                order_id=store.save_order(customer='Cliente fictício',due_date='2026-10-10',
                    payment='Pendente',production='Novo',notes='',items=[item])
                self.assertEqual(store.order(order_id)['number'],'PM0001')
                def balance():
                    return next(r['balance'] for r in store.stock() if r['variant_id']==red)
                self.assertEqual(balance(),1)
                store.delete_order(order_id)
                self.assertEqual(balance(),5)
                self.assertIsNone(store.order(order_id))
                self.assertEqual(len(store.orders()),0)
                self.assertEqual(store.stock_history(material['id'],variant_id=red)[0]['kind'],'order_reversal')
                self.assertEqual(store.next_number(),'PM0002')
            finally:
                store.close()


if __name__=='__main__':
    unittest.main()
