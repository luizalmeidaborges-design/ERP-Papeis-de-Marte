import tempfile
import unittest
from pathlib import Path
from core import Store

class MeasurementTests(unittest.TestCase):
    def test_migrate_roundtrip_duplicate_clear_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'db.sqlite'
            s=Store(path)
            try:
                s.save_material(code='PAP',name='Papel',unit='un',pack_qty=1,pack_cents=100)
                args=dict(name='Cartão',code='CAR',markup=2,table_cents=200,recipe=[('PAP',1)])
                pid=s.save_product(**args)
                keys=('weight_g','height_cm','width_cm','length_cm')
                for key in keys:s.db.execute(f'ALTER TABLE products DROP COLUMN {key}')
                s.db.commit();s.close();s=Store(path)
                self.assertIsNone(s.products()[0]['weight_g'])
                measures=dict(zip(keys,['250,5','3.5','15','21']))
                s.save_product(id=pid,measurements=measures,**args)
                s.close();s=Store(path)
                row=s.one('SELECT * FROM products WHERE id=?',(pid,))
                self.assertEqual([row[k] for k in keys],[250.5,3.5,15,21])
                copied=s.duplicate_product(pid)
                row=s.one('SELECT * FROM products WHERE id=?',(copied,))
                self.assertEqual([row[k] for k in keys],[250.5,3.5,15,21])
                for invalid in ['-1','0','nan','inf','abc',True]:
                    with self.assertRaises(ValueError):s.save_product(id=pid,measurements={'weight_g':invalid},**args)
                s.save_product(id=pid,**args)  # callers that omit measurements preserve them
                self.assertEqual(s.one('SELECT weight_g FROM products WHERE id=?',(pid,))[0],250.5)
                s.save_product(id=pid,measurements={'weight_g':''},**args)
                self.assertIsNone(s.one('SELECT weight_g FROM products WHERE id=?',(pid,))[0])
                self.assertEqual(s.product_cost(pid)[0],100)
                self.assertEqual(s.suggested(s.one('SELECT * FROM products WHERE id=?',(pid,)))[0],200)
            finally:s.close()
