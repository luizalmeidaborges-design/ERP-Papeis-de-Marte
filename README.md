# ERP Papéis de Marte

Aplicativo **offline** para Windows, escrito em Python com Tkinter e SQLite.
O arquivo `.exe` é gerado no próprio Windows. Não é necessário manter Excel
nem Python no computador que receber o executável pronto.

## Para usar agora no VS Code

1. Abra esta pasta no VS Code e abra o terminal (**Terminal > Novo Terminal**).
2. Instale as dependências e inicie a interface (se `py` não existir,
   substitua `py -3` por `python` na primeira linha):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Para gerar o EXE

Execute `compilar_windows.bat` nesta pasta (pelo Explorador de Arquivos ou pelo
terminal do VS Code). O resultado será `dist\ERP_Papeis_de_Marte.exe`.
O script aceita Python 3.10+ instalado como `py -3` **ou** `python`.
O computador de compilação precisa de Python 3 e conexão à internet na primeira
instalação das dependências. O EXE gerado funciona sem internet.

## Atualizações automáticas

**No GitHub:** após colocar este projeto em um repositório público, abra
**Actions → Compilar e publicar ERP → Run workflow**, informe `1.1.0` para a
primeira publicação e execute. O próprio GitHub compila no Windows, calcula a
conferência do EXE e cria a Release. Faça o download do EXE da primeira Release
e envie uma vez à cliente. Para atualizações seguintes, repita a ação com
`1.2.0`, `1.3.0` etc., sempre aumentando a versão. A cliente não precisa de
uma conta no GitHub nem instalar o GitHub CLI. O botão de publicação aparece
depois que `.github/workflows/publicar.yml` estiver no ramo padrão.

Também é possível publicar ao alterar `release-version.txt` no ramo `main`:
primeiro envie as mudanças do programa e depois atualize esse arquivo para a
próxima versão (por exemplo, `1.3.0`). O GitHub inicia a compilação automaticamente.
Mantenha apenas uma versão nova por publicação; a Release recebe o EXE e
`update.json`. O comando manual continua disponível na aba Actions.

Para criar o repositório `luizalmeidaborges-design/ERP-Papeis-de-Marte`
diretamente do seu Windows, instale [Git for Windows](https://git-scm.com/download/win)
e [GitHub CLI](https://cli.github.com/), execute `gh auth login` no terminal uma
vez e abra `criar_repositorio_windows.bat` na pasta extraída do ZIP. O script
confere que a planilha privada está excluída, cria o repositório **público** e
envia o projeto. Em seguida, use **Actions → Compilar e publicar ERP** no GitHub.

Quando receber arquivos atualizados do projeto, copie-os para **a mesma pasta**
onde executou `criar_repositorio_windows.bat`, substituindo os anteriores e
preservando a pasta `.git`. Execute `enviar_alteracoes_windows.bat`; depois abra
Actions e publique com uma versão maior. Enviar o código e executar a publicação
são duas etapas diferentes. Não copie bancos `.db` nem a planilha privada para
o repositório.

O repositório público inclui o código e o logo, mas exclui a planilha privada
`assets/Precificação.xlsx`, bancos SQLite e arquivos temporários. O EXE publicado
inicia com os dados já existentes no computador da cliente. O banco é copiado
automaticamente durante o uso e quando o programa é fechado.

**Primeira entrega:** o EXE já enviado à cliente não conhece o atualizador.
Envie uma única vez um novo EXE compilado com esta versão, depois de configurar
o endereço de publicação. A partir daí, quando ela abrir o aplicativo com
internet, ele consulta a versão mais recente e baixa o novo EXE em segundo plano.
Uma mensagem no menu lateral avisa quando a versão estiver pronta. Na abertura
seguinte, o EXE anterior inicia a versão baixada automaticamente, inclusive
sem internet. Mantenha o EXE inicial no mesmo lugar para a cliente usá-lo
sempre; ele encaminhará para a versão atual. O banco `marte.db` continua em
`%LOCALAPPDATA%\ERP_Papeis_de_Marte`.

**Preparar publicação (exemplo com GitHub Releases público):**

1. Crie um repositório público com um README inicial para publicar os executáveis. Anote `USUARIO/REPO`.
2. Em `assets/update_config.json`, escreva a versão atual e coloque em
   `manifest_url` este endereço, substituindo `USUARIO/REPO`:
   `https://github.com/USUARIO/REPO/releases/latest/download/update.json`.
   O arquivo distribuído neste ZIP vem com URL vazia; enquanto ela estiver vazia,
   a consulta automática fica desligada.
3. Execute `compilar_windows.bat` no Windows e, no terminal nesta pasta, execute
   `py -3 gerar_manifesto.py --repo USUARIO/REPO` (pode usar `python` no lugar de
   `py -3`). O comando cria `dist\update.json` usando o tamanho e SHA-256 do EXE
   recém-compilado.
4. No repositório, crie uma Release com tag `v1.1.0` (ou `v` + a versão do JSON).
   Anexe, com estes nomes exatos, `dist\ERP_Papeis_de_Marte.exe` e
   `dist\update.json`. Publique a Release.
5. Depois de conferir que o endereço `.../releases/latest/download/update.json`
   abre, mande o novo EXE à cliente para esta única troca manual.

**Próximas versões:** aumente `version` em `assets/update_config.json` (por
exemplo `1.2.0`), preserve o mesmo `manifest_url`, compile de novo e execute
`py -3 gerar_manifesto.py --repo USUARIO/REPO`. Crie a Release `v1.2.0`, anexe
o novo EXE e seu `update.json` e publique. Não altere os arquivos depois de
gerar o manifesto: se recompilar, gere um manifesto novo. Não publique como
*pré-lançamento*, pois o endereço `latest` usa a release normal mais recente.

**Publicação com um comando:** depois de instalar o [GitHub CLI](https://cli.github.com/)
e executar `gh auth login` uma vez no seu computador, abra o terminal nesta
pasta e execute `publicar_windows.bat USUARIO/REPO 1.2.0`. O script configura
o endereço e a versão, chama a compilação (que pede uma tecla ao terminar),
gera o manifesto e publica uma Release normal com os dois arquivos.
Na primeira vez, use `1.1.0` e envie o EXE resultante uma vez à cliente.
Nas próximas vezes, escolha um número de versão maior. O repositório precisa
existir e estar público; a máquina que publica precisa de internet.

O computador da cliente continua funcionando offline quando não consegue
consultar ou baixar a atualização. Somente a consulta precisa de internet.
Releases e arquivos precisam estar acessíveis sem login, pois o EXE não inclui
credenciais. O download é feito por HTTPS e conferido pelo tamanho e SHA-256
declarados no manifesto; controle o acesso de publicação desse repositório.

## Uso

- **Insumos:** nome, tamanho, gramatura, observações, preço e quantidade da embalagem.
  O custo unitário é calculado como preço ÷ quantidade. Para comprimento ou massa,
  use a unidade adequada e mantenha a quantidade da receita na mesma unidade.
- **Tamanho e gramatura:** aparecem em colunas separadas nos insumos e nos
  produtos. Um novo código é gerado automaticamente com três caracteres do nome,
  tamanho e gramatura. Exemplo: Offset + A4 + 150 = `OFFA4150`. Os códigos dos
  registros anteriores são preservados na atualização.
- **Variações de insumos:** no cadastro, liste cores como `Branco, Dourado, Preto`.
  O preço e o custo unitário continuam sendo do insumo, iguais para todas as
  cores. Ao selecionar no pedido um produto que usa esse insumo, escolha a cor
  de cada material antes de adicionar o item. Se o mesmo produto tiver cores
  diferentes, adicione-o em linhas separadas. A escolha aparece no pedido e no
  PDF.
- **Produtos:** acrescente quantos insumos quiser à composição de uma unidade.
  O preço sugerido é custo × multiplicador (padrão 1,8, igual à planilha). O preço
  de tabela pode ser definido separadamente. A média vendida é o total efetivamente
  cobrado pelo produto dividido pela quantidade vendida nos pedidos vinculados.
- **Pedidos:** cliente, entrega, vários itens, valor por item, status de pagamento,
  status de produção, observações e geração de comprovante em PDF. Produtos do
  cadastro aparecem como sugestões; também é possível digitar itens avulsos.
  Clique no botão de calendário ao lado de **Entrega** para escolher a data.
  Quando o pagamento for **Parcial**, informe quanto já foi recebido; o saldo
  aparece no pedido e na coluna **Restante**. **Pago** encerra o saldo; **Pendente**
  mostra o total em aberto. Pedidos anteriores preservam seus status.
  Selecione um pedido e use **Excluir pedido** para removê-lo após confirmação.
  O estoque consumido é devolvido às variações correspondentes, com estorno
  registrado no histórico. O número do pedido não é reutilizado.
  O botão **Salvar pedido** permanece visível no rodapé da edição; use a barra
  de rolagem para alcançar os demais campos em telas menores.
- **Calendário:** veja as entregas do mês, mude de mês e clique em um dia para
  listar seus pedidos. Um clique duplo na lista abre o pedido para edição.
- **Filtros de pedidos:** filtros independentes por número, cliente, itens, data
  de criação, data de entrega, pagamento, produção, faixa de valor e valor
  restante. Datas são
  pesquisadas como aparecem na tabela (`DD/MM/AAAA`).
- **Relatórios:** escolha mês/ano de cadastro ou Total para ver pedidos, receita,
  ticket médio, situação e itens vendidos. Exporte o resumo para PDF.
- **Estoque:** registre entrada de insumos, retirada forçada e ajuste para um
  saldo final contado. Cada operação exige motivo e fica no histórico. Pedidos
  novos com produtos cadastrados retiram automaticamente os insumos da receita
  na data do cadastro, usando quantidade do pedido × quantidade da composição.
  Pedidos com itens avulsos não têm baixa automática. Ao mudar os itens de um
  pedido, a retirada anterior é estornada e refeita; mudar apenas pagamento,
  produção, preço ou entrega não altera o estoque. Produtos com composição
  incompleta precisam ser corrigidos para terem retirada automática.
  O saldo e o histórico aparecem por variação. **Transferir** move unidades
  entre cores ou do saldo antigo “Sem variação (legado)” para uma cor, sem mudar
  a quantidade total do insumo.
- **Início:** totais e pedidos em aberto por data de entrega.
- **Salvar cópia dos dados:** crie regularmente um arquivo `.db` de backup.

## Backup automático (a partir da versão 1.2.1)

O programa mantém uma cópia diária do banco em
`%LOCALAPPDATA%\ERP_Papeis_de_Marte\backups\marte_AAAA-MM-DD.db`.
Cria a primeira cópia ao abrir, atualiza a cópia após mudanças (verificação a
cada 30 segundos) e faz outra cópia ao clicar no **X**. No fechamento, aparece
**Backup sendo realizado** e o programa aguarda a cópia local e a cópia para a
pasta escolhida terminarem. Cópias dos dias anteriores continuam disponíveis;
no mesmo dia, a cópia é atualizada com os pedidos e cadastros mais recentes.

Clique no pequeno ícone **📁** ao lado da data no topo para escolher uma pasta
de backup. Se escolher uma pasta sincronizada pelo OneDrive ou Google Drive, o
aplicativo copia os arquivos para ela e o serviço sincroniza com a nuvem quando
houver conexão. Confira o ícone do serviço para saber se o envio terminou: o
aviso de backup do ERP confirma a cópia na pasta, não o envio à nuvem. Se essa
pasta ficar indisponível, o backup local continua sendo salvo e aparece um
aviso; ao voltar, o aplicativo tenta copiar novamente. O banco de trabalho
`marte.db` permanece fora da pasta sincronizada.

Para recuperar um backup, feche o ERP, guarde uma cópia do `marte.db` atual e
copie o arquivo de backup escolhido para
`%LOCALAPPDATA%\ERP_Papeis_de_Marte\marte.db`, substituindo o arquivo anterior.
Ao abrir, o aplicativo carregará os dados daquela cópia.

O banco fica em `%LOCALAPPDATA%\ERP_Papeis_de_Marte\marte.db` no Windows.
Ao instalar uma nova versão do EXE, o aplicativo atualiza os campos necessários
no banco existente e mantém cadastros, pedidos e códigos já salvos.
O EXE enviado anteriormente importava o Excel em `assets` **somente no primeiro uso**.
A partir desta versão, o EXE publicado não inclui a planilha de pedidos e preços
da cliente. Bancos existentes mantêm todos os dados; uma instalação nova começa
com cadastros vazios. Ao executar o código localmente com a planilha presente,
ela ainda é importada apenas no primeiro uso. A planilha está excluída do Git.
Os oito pedidos históricos importados não têm data de entrega na
planilha; ela aparece como “Não informada” até a edição do pedido. Um pedido
histórico também está sem preço e aparece como “A definir”. Os produtos
`PRE001` (insumo `FITCET` ausente) e `KIT001` (sem composição) precisam de revisão;
seu custo e preço sugerido não são exibidos como números incompletos. A edição
de pedidos antigos exige definir uma data de entrega e um preço para cada item.

O total da tela inicial soma somente pedidos com todos os preços definidos.
O relatório segue esse mesmo critério para o total, o ticket médio e a lista de
itens vendidos.
“Média vendida” só aparece para produtos escolhidos do cadastro nos pedidos;
itens avulsos não são associados automaticamente ao produto por semelhança do nome.

Na aba **Relatórios**, escolha um mês e ano para filtrar pela **data de cadastro
do pedido**, ou **Total** para todo o histórico. Os pedidos importados da planilha
não tinham data de cadastro; por isso entram no Total, mas não nos meses.

O estoque começa com saldo **zero** porque a planilha não informa quantas
embalagens foram compradas ou ainda estão disponíveis. Antes de produzir,
registre o estoque inicial em **Entrada** ou **Ajustar saldo**, na mesma unidade
usada na receita. Pedidos anteriores a esta atualização não são abatidos de
forma retroativa. O saldo pode ficar negativo para mostrar faltas ou lançamentos
pendentes. Alterações posteriores na composição de um produto não mudam as
retiradas já registradas; uma edição nos itens do pedido estorna o consumo
anterior e aplica a composição atual.

Ao cadastrar cores em um insumo que já tinha estoque, o saldo anterior continua
visível em **Sem variação (legado)**; ele não é distribuído automaticamente entre
as cores. Use **Transferir** para atribuí-lo. Remover uma cor do cadastro a
inativa para novos pedidos, mas mantém seu saldo e histórico para consulta ou
ajuste. Pedidos já registrados preservam a cor escolhida.

O comprovante em PDF é um resumo do pedido e não é nota fiscal. Os dados ficam
apenas no computador; para transferi-los, copie ou restaure `marte.db` com o
aplicativo fechado.
