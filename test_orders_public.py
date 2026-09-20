"""Testa exclusão de pedidos sem precisar de dados privados da cliente."""
import tempfile
import unittest
from pathlib import Path

from core import Store


class PublicOrderTests(unittest.TestCase):
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
