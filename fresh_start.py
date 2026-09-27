"""Reinício único solicitado para a build 5.1.0, antes de abrir o Store."""
from datetime import datetime
from contextlib import closing
from pathlib import Path
import sqlite3

RESET_KEY = 'fresh_start_5_1_0'


def prepare_database(path):
    """Backup obrigatório antes da limpeza; dados e marcador na mesma transação.

    Não importa planilhas. Se o backup ou a limpeza falhar, propaga o erro e o
    aplicativo não abre. Reabrir esta versão preserva todos os novos cadastros.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        # Hold a reserved write lock throughout backup and reset. Readers can
        # continue, but no other connection can add data after the snapshot.
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('BEGIN IMMEDIATE')
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if 'app_migrations' in tables and db.execute(
                'SELECT 1 FROM app_migrations WHERE name=?', (RESET_KEY,)).fetchone():
            return None
        backup = None
        if any(not name.startswith('sqlite_') for name in tables):
            folder = path.parent / 'backups'
            folder.mkdir(parents=True, exist_ok=True)
            backup = folder / ('antes_reset_5_1_0_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.db')
            try:
                with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(backup)) as copy:
                    source.backup(copy)
                    if copy.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise RuntimeError('A cópia de segurança não passou na verificação.')
            except Exception:
                backup.unlink(missing_ok=True)
                raise
        try:
            db.execute('CREATE TABLE IF NOT EXISTS app_migrations (name TEXT PRIMARY KEY)')
            for name in tables:
                if name != 'app_migrations' and (not name.startswith('sqlite_') or name == 'sqlite_sequence'):
                    db.execute('DELETE FROM "' + name.replace('"', '""') + '"')
            db.execute('INSERT INTO app_migrations(name) VALUES(?)', (RESET_KEY,))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return backup
