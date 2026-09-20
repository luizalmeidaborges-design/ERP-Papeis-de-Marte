"""Verifica as cópias SQLite usadas no fechamento e durante o trabalho."""
from contextlib import closing
from datetime import date
from pathlib import Path
import os
import sqlite3
import tempfile
import unittest

from automatic_backup import AutomaticBackup
from core import Store


def customers(path):
    with closing(sqlite3.connect(path)) as db:
        return [row[0] for row in db.execute('SELECT customer FROM orders ORDER BY id')]


class AutomaticBackupTests(unittest.TestCase):
    def test_updates_daily_copy_and_retains_previous_day(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            store = Store(directory / 'data' / 'marte.db')
            try:
                backup = AutomaticBackup(directory / 'data')
                selected = directory / 'OneDrive' / 'Papéis de Marte'
                selected.mkdir(parents=True)
                backup.select_folder(selected)
                self.assertTrue(
                    os.path.samefile(
                        AutomaticBackup(directory / 'data').folder,
                        selected,
                    )
                )
                item = {'product_id': None, 'description': 'Caderno',
                        'qty': 1, 'unit_cents': 2000}
                store.save_order(customer='Primeira', due_date='2026-10-01',
                                 payment='Pendente', production='Novo', notes='', items=[item])
                yesterday = backup.create(store.path, today=date(2026, 9, 19))
                self.assertEqual(customers(yesterday.local_path), ['Primeira'])
                self.assertEqual(customers(yesterday.selected_path), ['Primeira'])
                store.save_order(customer='Segunda', due_date='2026-10-02',
                                 payment='Pago', production='Novo', notes='', items=[item])
                today = backup.create(store.path, today=date(2026, 9, 20))
                self.assertEqual(customers(today.local_path), ['Primeira', 'Segunda'])
                self.assertEqual(customers(today.selected_path), ['Primeira', 'Segunda'])
                self.assertEqual(customers(yesterday.local_path), ['Primeira'])
                self.assertEqual(customers(yesterday.selected_path), ['Primeira'])
                store.save_order(customer='Terceira', due_date='2026-10-03',
                                 payment='Pago', production='Novo', notes='', items=[item])
                refreshed = backup.create(store.path, today=date(2026, 9, 20))
                self.assertEqual(refreshed.local_path, today.local_path)
                self.assertEqual(customers(refreshed.local_path), ['Primeira', 'Segunda', 'Terceira'])
                self.assertEqual(customers(refreshed.selected_path), ['Primeira', 'Segunda', 'Terceira'])
            finally:
                store.close()

    def test_unavailable_selected_folder_keeps_valid_local_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            store = Store(directory / 'data' / 'marte.db')
            try:
                selected = directory / 'OneDrive'
                selected.mkdir()
                backup = AutomaticBackup(directory / 'data')
                backup.select_folder(selected)
                selected.rmdir()
                result = backup.create(store.path)
                self.assertIsNone(result.selected_path)
                self.assertIn('não está disponível', result.selected_error)
                with closing(sqlite3.connect(result.local_path)) as db:
                    self.assertEqual(db.execute('PRAGMA quick_check').fetchone()[0], 'ok')
            finally:
                store.close()


if __name__ == '__main__':
    unittest.main()
