"""Atualização opcional do EXE, sem modificar o banco SQLite local."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

MAX_MANIFEST = 65536
MAX_EXE = 300 * 1024 * 1024
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def version_tuple(value):
    if not isinstance(value, str) or not VERSION_PATTERN.fullmatch(value):
        raise ValueError('Versão inválida; use números como 1.2.0.')
    return tuple(map(int, value.split('.')))


def https_url(value):
    if not isinstance(value, str) or urlsplit(value).scheme != 'https' or not urlsplit(value).hostname:
        raise ValueError('O endereço de atualização precisa usar HTTPS.')
    return value


def read_config(asset_path):
    config = json.loads(Path(asset_path).read_text(encoding='utf-8'))
    version_tuple(config['version'])
    if config.get('manifest_url'):
        https_url(config['manifest_url'])
    return config


def _read_json(url, opener):
    with opener(https_url(url), timeout=12) as response:
        https_url(response.geturl())
        data = response.read(MAX_MANIFEST + 1)
        if len(data) > MAX_MANIFEST:
            raise ValueError('Manifesto de atualização muito grande.')
    return json.loads(data)


def _cached_file(data_dir, version):
    version_tuple(version)
    return Path(data_dir) / 'updates' / ('ERP_Papeis_de_Marte-' + version + '.exe')


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def cached_update(config, data_dir):
    """Só devolve um EXE baixado e verificado, de versão posterior à atual."""
    marker = Path(data_dir) / 'updates' / 'ready.json'
    try:
        record = json.loads(marker.read_text(encoding='utf-8'))
        if version_tuple(record['version']) <= version_tuple(config['version']):
            return None
        path = _cached_file(data_dir, record['version'])
        if (re.fullmatch(r'[a-f0-9]{64}', record['sha256']) and path.is_file()
                and _sha256(path) == record['sha256']):
            return path
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        pass
    return None


def launch_cached(config, data_dir):
    """Inicia a versão nova quando a cliente abrir o EXE antigo novamente."""
    if not getattr(sys, 'frozen', False):
        return False
    path = cached_update(config, data_dir)
    if path is None:
        return False
    env = dict(os.environ)
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    try:
        subprocess.Popen([str(path)], env=env, close_fds=True)
    except OSError:
        return False
    return True


def check_and_stage(config, data_dir, opener=urllib.request.urlopen):
    """Baixa uma versão mais nova em segundo plano; nunca substitui o EXE em uso."""
    if not getattr(sys, 'frozen', False) or not config.get('manifest_url'):
        return None
    manifest = _read_json(config['manifest_url'], opener)
    if manifest.get('schema') != 1:
        raise ValueError('Formato do manifesto incompatível.')
    version = manifest['version']
    if version_tuple(version) <= version_tuple(config['version']):
        return None
    current = cached_update(config, data_dir)
    if current and version_tuple(current.stem.rsplit('-', 1)[-1]) >= version_tuple(version):
        return None
    url = https_url(manifest['url'])
    expected_hash = manifest['sha256']
    length = manifest['size_bytes']
    if not isinstance(expected_hash, str) or not re.fullmatch(r'[a-f0-9]{64}', expected_hash):
        raise ValueError('Assinatura SHA-256 inválida.')
    if isinstance(length, bool) or not isinstance(length, int) or not 0 < length <= MAX_EXE:
        raise ValueError('Tamanho de atualização inválido.')
    target = _cached_file(data_dir, version)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, partial = tempfile.mkstemp(prefix='download-', suffix='.part', dir=target.parent)
    try:
        digest = hashlib.sha256()
        count = 0
        with os.fdopen(fd, 'wb') as output, opener(url, timeout=30) as response:
            https_url(response.geturl())
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > length:
                    raise ValueError('O arquivo excedeu o tamanho anunciado.')
                output.write(chunk)
                digest.update(chunk)
            output.flush()
            os.fsync(output.fileno())
        if count != length or digest.hexdigest() != expected_hash:
            raise ValueError('Falha na verificação do tamanho ou SHA-256 do EXE.')
        os.replace(partial, target)
        marker = target.parent / 'ready.json'
        marker_tmp = target.parent / 'ready.json.tmp'
        marker_tmp.write_text(json.dumps({'version': version, 'sha256': expected_hash}), encoding='utf-8')
        os.replace(marker_tmp, marker)
        return version
    finally:
        if os.path.exists(partial):
            os.unlink(partial)
