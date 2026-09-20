"""Gera update.json depois de compilar o EXE no Windows."""
import argparse
import hashlib
import json
from pathlib import Path

from updater import https_url, read_config


def main():
    parser = argparse.ArgumentParser(description='Gera o manifesto da versão compilada.')
    parser.add_argument('--exe', type=Path, default=Path('dist/ERP_Papeis_de_Marte.exe'))
    urls=parser.add_mutually_exclusive_group(required=True)
    urls.add_argument('--url', help='URL HTTPS do EXE na nova release')
    urls.add_argument('--repo', help='Repositório público GitHub, no formato USUARIO/REPOSITORIO')
    parser.add_argument('--output', type=Path, default=Path('dist/update.json'))
    args = parser.parse_args()
    config = read_config(Path(__file__).parent / 'assets' / 'update_config.json')
    if args.repo:
        import re
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.repo):
            parser.error('Informe --repo no formato USUARIO/REPOSITORIO.')
        expected=f'https://github.com/{args.repo}/releases/latest/download/update.json'
        if config.get('manifest_url') != expected:
            parser.error('Configure assets/update_config.json para este repositório antes de compilar.')
        args.url=f'https://github.com/{args.repo}/releases/download/v{config["version"]}/ERP_Papeis_de_Marte.exe'
    exe = args.exe.read_bytes()
    manifest = {'schema': 1, 'version': config['version'], 'url': https_url(args.url),
                'sha256': hashlib.sha256(exe).hexdigest(), 'size_bytes': len(exe)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Manifesto criado: {args.output} (versão {config["version"]})')


if __name__ == '__main__':
    main()
