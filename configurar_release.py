"""Configura versão e endereço público antes da compilação Windows."""
import argparse
import json
import re
from pathlib import Path

from updater import version_tuple


def main():
    parser=argparse.ArgumentParser(description='Configura o endereço fixo do atualizador.')
    parser.add_argument('repo',help='USUARIO/REPOSITORIO no GitHub')
    parser.add_argument('version',help='Versão, por exemplo 1.2.0')
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.repo):
        parser.error('Informe o repositório como USUARIO/REPOSITORIO.')
    try:version_tuple(args.version)
    except ValueError as exc:parser.error(str(exc))
    path=Path(__file__).parent/'assets'/'update_config.json'
    value={'version':args.version,
           'manifest_url':f'https://github.com/{args.repo}/releases/latest/download/update.json'}
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Atualização configurada para {args.repo}, versão {args.version}.')


if __name__=='__main__':
    main()
