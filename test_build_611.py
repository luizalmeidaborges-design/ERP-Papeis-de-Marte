import unittest
from measurement_units import display_measurement, stored_measurement

class MeasurementUITests(unittest.TestCase):
    def test_conversions_and_invalid_input(self):
        for key,old,text in [('weight_g',250,'0,25'),('length_cm',13,'0,13'),('height_cm',2,'0,02'),('width_cm',21,'0,21')]:
            self.assertEqual(display_measurement(key,old),text)
            self.assertEqual(float(stored_measurement(key,text)),old)
        self.assertIsNone(stored_measurement('weight_g',''))
        for bad in ['nan','inf','0','-1','abc']:
            with self.assertRaises(ValueError):stored_measurement('height_cm',bad)

    def test_product_form_displays_converts_and_preserves_units(self):
        import test_build_510
        h=test_build_510.ProductFormTests();h.setUp()
        try:
            pid=h.store.save_product(code='CAR',name='Cartão',markup=2,table_cents=200,recipe=[('PAP',1)],
                measurements={'weight_g':250,'height_cm':2,'width_cm':10,'length_cm':13})
            h.form(h.store.products()[0])
            self.assertEqual(h.fields['PESO (kg)'].get(),'0,25')
            self.assertEqual(h.fields['COMPRIMENTO (m)'].get(),'0,13')
            h.fields['ALTURA (m)'].set('0,025')
            h.actions['Salvar produto'][0]()
            row=h.store.products()[0]
            self.assertEqual(row['weight_g'],250)
            self.assertEqual(row['height_cm'],2.5)
            self.assertEqual(row['length_cm'],13)
        finally:h.doCleanups();h.tearDown()

class RecipeWindowTests(unittest.TestCase):
    def test_apply_is_visible_in_small_resizable_window(self):
        import tkinter as tk
        import app
        try:root=tk.Tk()
        except tk.TclError:self.skipTest('Sem display gráfico para verificar a janela real.')
        try:
            root.withdraw();parent=tk.Toplevel(root)
            ui=app.ERP.__new__(app.ERP);ui.root=root
            applied=[]
            ui.product_notes_dialog(parent,'Receita',applied.append)
            win=next(w for w in parent.winfo_children() if isinstance(w,tk.Toplevel))
            win.geometry('640x480+0+0');root.update()
            def descendants(w):
                for child in w.winfo_children():
                    yield child
                    yield from descendants(child)
            action=next(w for w in descendants(win) if isinstance(w,tk.Button) and w.cget('text')=='Aplicar ao produto')
            self.assertTrue(action.winfo_ismapped())
            self.assertLess(action.winfo_rooty()+action.winfo_height(),win.winfo_rooty()+win.winfo_height())
            self.assertEqual(str(win.transient()),'')
            self.assertTrue(all(win.resizable()))
            action.invoke();self.assertEqual(applied,['Receita'])
        finally:root.destroy()
