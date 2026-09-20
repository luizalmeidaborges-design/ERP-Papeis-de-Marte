"""Cópias SQLite consistentes, mantidas fora do banco em uso."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class BackupResult:
    local_path: Path
    selected_path: Path | None
    selected_error: str | None = None


class AutomaticBackup:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.local_dir = self.data_dir / 'backups'
        self.settings = self.data_dir / 'backup_settings.json'
        self.folder: Path | None = None
        try:
            saved = json.loads(self.settings.read_text(encoding='utf-8'))
            if isinstance(saved.get('folder'), str) and saved['folder']:
                self.folder = Path(saved['folder'])
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def select_folder(self, folder: str | Path):
        chosen = Path(folder).expanduser().resolve()
        if not chosen.is_dir():
            raise ValueError('A pasta de backup precisa existir no computador.')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix='backup_settings_',suffix='.tmp',dir=self.data_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as output:
                json.dump({'folder': str(chosen)}, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp, self.settings)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        self.folder = chosen

    def create(self, source: str | Path, *, today: date | None = None) -> BackupResult:
        """Gera o backup local primeiro; falha na pasta escolhida não o apaga."""
        source = Path(source)
        if not source.is_file():
            raise FileNotFoundError(f'Banco de dados não encontrado: {source}')
        self.local_dir.mkdir(parents=True, exist_ok=True)
        name = f'marte_{(today or date.today()).isoformat()}.db'
        local = self.local_dir / name
        fd, temp = tempfile.mkstemp(prefix='.marte_',suffix='.tmp',dir=self.local_dir)
        os.close(fd)
        try:
            with closing(sqlite3.connect(source,timeout=15)) as original:
                with closing(sqlite3.connect(temp,timeout=15)) as target:
                    original.backup(target)
            with closing(sqlite3.connect(temp)) as check:
                if check.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('A cópia do banco não passou na verificação de integridade.')
            os.replace(temp,local)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        if self.folder is None:
            return BackupResult(local,None)
        try:
            if not self.folder.is_dir():
                raise FileNotFoundError('A pasta escolhida não está disponível.')
            selected=self.folder / name
            if selected.resolve() != local.resolve():
                fd, temp = tempfile.mkstemp(prefix='.marte_',suffix='.tmp',dir=self.folder)
                os.close(fd)
                try:
                    shutil.copy2(local,temp)
                    os.replace(temp,selected)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
            return BackupResult(local,selected)
        except OSError as exc:
            return BackupResult(local,None,str(exc))
