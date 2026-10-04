## Build 5.4.0 — Inativar / Excluir

Nas abas Pedidos, Produtos e Insumos, selecione uma linha e clique em
**Inativar / Excluir**. A janela explica as consequências e oferece Cancelar,
Inativar (ou Reativar para registros inativos) e Excluir. Excluir exige uma
segunda confirmação, com Não como padrão.

- Inativar preserva os dados e vínculos. Pedidos inativos são arquivados:
  continuam nos relatórios financeiros, sem estorno do estoque, mas não aparecem
  no calendário nem nas entregas pendentes do início. Use Estado na aba Pedidos
  para localizar ativos ou inativos; Todos mostra ambos.
- Excluir pedido remove seus valores dos relatórios e estorna a retirada
  automática dos insumos, mantendo o histórico das movimentações.
- Produtos presentes em pedidos ou na composição de outros produtos não podem
  ser excluídos. Insumos com composição ou histórico também ficam protegidos.
  Nesses casos, use Inativar.
- Migração preserva a base existente e marca pedidos antigos como ativos.

Validação: 74 testes executados, 64 aprovados e 10 ignorados por dependerem da
planilha privada de importação ausente. Interface Windows não testada visualmente.
Código preparado para compilação manual; release-version.txt não foi alterado.
No workflow manual, informe a versão **5.4.0**.

## Build 5.3.0 — edição de quantidades e produtos compostos

Base: última build 5.2.0. Preserva dados e pedidos existentes; não executa limpeza.

- **Editar quantidade:** selecione uma linha de Produção ou Embalagem e clique
  em Editar quantidade, ou dê duplo clique. Aceita valores fracionários positivos.
  Custo e preço sugerido são recalculados. Cancelar mantém a quantidade anterior;
  a composição só é gravada ao salvar o produto.
- **Ordenação:** a tabela e a lista de produtos usam Código em ordem alfabética,
  sem diferenciar maiúsculas/minúsculas e sem separar ativos antes de inativos.
- **Produto dentro de produto:** os seletores de Produção e Embalagem oferecem
  insumos e produtos cadastrados, identificados pelos prefixos Insumo e Produto.
  Informe quantas unidades do produto incluído são necessárias para compor o pai.
  Produtos podem conter outros produtos em vários níveis. O custo é a soma dos
  insumos finais; o preço de venda e o multiplicador do filho não são somados ao
  custo do pai. O multiplicador geral é aplicado ao custo final para sugerir preço.
- **Estoque:** ao salvar o pedido, a composição inteira é expandida em insumos.
  Quantidades se multiplicam em cada nível e insumos repetidos são somados. As
  variações dos insumos internos também são solicitadas, uma escolha por insumo
  em cada item de pedido, aplicada a todas as ocorrências desse insumo.
- Ao editar quantidades/itens de um pedido, o consumo anterior é estornado e a
  composição atual é aplicada. Alterar apenas pagamento não recalcula o estoque.
  Excluir o pedido devolve o que foi efetivamente retirado, mesmo após mudança
  na composição. Cadastros e pedidos históricos não são recalculados na migração.
- Inclusão circular, direta ou indireta, é bloqueada. Composição incompleta
  bloqueia o consumo de estoque. Alterar códigos mantém os vínculos por ID;
  duplicar um produto copia suas linhas e os vínculos com produtos componentes.

Exemplo: um kit contém 3 cadernos; cada caderno usa 2 folhas. Um pedido de
2 kits retira 12 folhas, além dos outros insumos e embalagens de toda a composição.

Validação: 69 testes executados, 59 aprovados e 10 ignorados por dependerem da
planilha privada ausente. Cobrem três níveis, insumos repetidos, rendimento legado,
cores, edição de quantidades, renomeação, duplicação, ciclos, migração e estorno.
Os callbacks da interface foram testados sem display; validação visual Windows
e compilação ainda devem ser realizadas.

Para compilar: `compilar_windows.bat` ou Actions → Compilar e publicar ERP →
Run workflow → branch `main` → versão **5.3.0**. Este commit não publica Release
nem altera `release-version.txt`.

---

## Build 5.2.0 — códigos, categorias, composição e clientes

Base: build 5.1.1. Preserva o banco existente, sem limpeza automática.

- Códigos sugeridos automaticamente em produtos e insumos, com edição manual.
  Alterar o código de um insumo atualiza todas as composições na mesma transação.
  Produtos conservam seu ID e seus vínculos com pedidos. Códigos repetidos são bloqueados.
- Categorias cadastráveis/excluíveis em produtos e insumos. Ao excluir uma categoria,
  os itens passam para **Sem categoria**. Filtros nas duas listagens.
- **Duplicar produto** cria uma cópia independente com outro código e abre a edição.
- Produção e Embalagem oferecem todos os insumos ativos, independentemente da categoria.
  A seção escolhida fica gravada na composição, mesmo se a categoria do insumo mudar.
- Pedidos pesquisam clientes cadastrados e permitem cadastro completo pelo botão **Novo**.
  Um nome novo digitado diretamente é cadastrado ao salvar um pedido válido.
  Nomes iguais são reutilizados, ignorando maiúsculas e espaços repetidos; homônimos
  exigem seleção explícita, com telefone e ID na lista. Pedidos históricos conservam seu texto.

Verificação: testes automatizados de banco e callbacks dos formulários, além de migração
com um banco gerado pela versão 5.1.1, incluindo pedidos, variações e estoque.
A validação visual e a compilação do EXE no Windows ainda precisam ser realizadas.

Para compilar: `compilar_windows.bat`. Para publicar pelo GitHub Actions, execute
**Compilar e publicar ERP** com a versão **5.2.0**, depois de integrar esta alteração.
Esta alteração não dispara a publicação automática.

---

## Build 5.1.1 — configurações, cálculo e formulários

Esta versão **preserva o banco existente**. A chamada de limpeza automática da
5.1.0 foi retirada da inicialização, inclusive para quem atualizar de versões
anteriores diretamente. Nenhum cadastro é apagado ao abrir esta build.

- Engrenagem **⚙** no cabeçalho: configura o multiplicador geral de custo, salvo
  no banco e incluído no backup. Padrão 1,8; aceita vírgula ou ponto, de 1 a 1000.
- O campo de multiplicador sai do cadastro de produto. A composição soma
  Produção + Embalagem e preenche o preço sugerido usando o multiplicador geral.
  O preço continua editável. Configurar outro multiplicador não altera preços
  já salvos nem pedidos existentes; abra/recalcule a composição para aplicar.
- Corrigida a vida útil das variáveis dos campos Tkinter: ficam vinculadas ao
  widget, evitando leitura inválida depois que o formulário termina de montar.
- Janelas abrem maximizadas. Movimentação, transferência e compras recebem
  conteúdo rolável e rodapé de ações separado; os demais cadastros conservam
  seus rodapés fixos. Botões de confirmação ficam fora do conteúdo rolável.
- Estoque: filtros combináveis por nome/código, variação, tamanho e situação,
  com botão Limpar. Histórico é limpo quando o filtro não retorna resultados.
- Insumos: botão Excluir com confirmação. Exclui insumos sem vínculo e suas
  variações. Se houver composição, estoque, compra ou pedido vinculado, a
  exclusão é bloqueada; use Ativar / inativar para preservar o histórico.

Verificação: 44 testes executados, 34 aprovados e 10 ignorados por dependerem
da planilha privada. Inclui persistência/validação das configurações, callbacks
de preço e filtro, referência de variável Tcl após coleta de lixo e exclusão.
Compilação e validação visual no Windows ainda pendentes.

Compile com `compilar_windows.bat` ou execute manualmente **Compilar e publicar
ERP** em `main`, informando **5.1.1**. Este commit não dispara publicação.

---
Histórico abaixo: as instruções da build 5.1.1 prevalecem.

## Build 5.1.0 — cadastro simplificado e recomeço

**ATENÇÃO: na primeira abertura desta build, o banco local será zerado.**
Clientes, insumos, variações, produtos, composições, pedidos, compras e movimentos
serão removidos. Antes disso, é obrigatória uma cópia SQLite íntegra em
`%LOCALAPPDATA%\ERP_Papeis_de_Marte\backups\antes_reset_5_1_0_*.db`.
Se a cópia falhar, o programa não abre nem apaga os registros.
A limpeza e seu marcador são gravados juntos: reabrir a aplicação preserva os
novos dados. Instalações novas começam vazias, sem importar planilhas antigas.
Os arquivos de backup existentes e a pasta de backup configurada são preservados.
A limpeza só ocorre ao executar a nova versão no computador do usuário.
Para recuperar uma cópia anterior à limpeza, use a build anterior: ela não
contém o marcador desta migração.

O cadastro de produtos mantém Produção e Embalagem, mas remove produto base e
rendimento. Informe os insumos necessários para **1 produto**.
O resumo fixo soma as duas listas e mostra `custo total × multiplicador = preço
calculado`, atualizando ao adicionar/remover insumos ou alterar o multiplicador.
Mesmo com multiplicador inválido o custo continua visível. O mínimo é 1.
O antigo preço opcional é substituído por **Preço sugerido (R$) • Editável**,
preenchido automaticamente. Você pode ajustar o valor antes de salvar. Alterar
insumos ou multiplicador preenche novamente o campo com o cálculo; alterar
nome, tamanho ou gramatura não sobrescreve seu preço. Reabrir preserva o preço
salvo. O pedido usa esse preço, e a tabela de produtos exibe o preço de venda.
Há ajuda `?` em cada campo do formulário, incluindo seleção e quantidade dos
insumos. Passe o mouse, use o foco do teclado ou clique para ler a explicação.
Novos produtos têm rendimento interno 1. O campo legado table_cents armazena
o valor aceito/ajustado. Mudanças futuras no preço dos insumos atualizam o custo;
para rever o preço de venda, abra o produto e ajuste o multiplicador ou sua
composição antes de salvar. Preços de pedidos existentes não são alterados.

Verificação automatizada: 40 testes executados, 30 aprovados e 10 ignorados
por dependerem de uma planilha privada ausente do repositório. Inclui testes
dos callbacks reais do formulário sem display, limpeza única, cópia íntegra,
falha de backup e rollback. Compilação e validação visual no Windows pendentes.

Compile no Windows com `compilar_windows.bat`. Versão interna: **5.1.0**.
Este commit prepara o código; não altera `release-version.txt` e não dispara
publicação automática. Para distribuir posteriormente pelo GitHub Actions,
execute manualmente o workflow com a versão `5.1.0`. Qualquer instalação que
executar esta build fará o reinício descrito acima uma única vez.

---
Histórico das versões anteriores (as regras acima prevalecem na 5.1.0):

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
  produtos. Nos insumos, um novo código é gerado automaticamente com três caracteres do nome,
  tamanho e gramatura. Exemplo: Offset + A4 + 150 = `OFFA4150`. Os códigos dos
  registros anteriores são preservados na atualização. Nos produtos, o código é
  preenchido manualmente e precisa ser único; também pode ser editado.
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

## Melhorias de cadastro

- Insumos: filtros combináveis por nome/código, tamanho, gramatura, variação e
  estado, com botão Limpar. O campo Data do preço (DD/MM/AAAA) é editável e
  aparece na listagem. Cadastros antigos ficam com data não informada até edição.
  Em cadastros novos, a data sugerida é hoje; atualize-a ao revisar o preço.
- Produtos: código manual obrigatório e único. Na composição, digite parte do
  nome ou código do insumo e abra a lista para selecionar o resultado.
- Novo insumo na composição: abre o cadastro sem perder o produto em edição;
  ao salvar, o insumo fica selecionado. Informe a quantidade e clique Adicionar.

Estas alterações de código não acionam a compilação automaticamente. Para
compilar no computador, baixe o código atualizado e execute
`compilar_windows.bat`. Para publicar uma atualização, configure antes uma
versão superior à última Release com `configurar_release.py`.

## Build 2.1.0 — compras e resultado mensal

A aba Compras registra compras já recebidas e pagas de **insumos cadastrados**.
Produtos acabados continuam sendo compostos por esses insumos. Informe fornecedor
(opcional), insumo/variação, quantidade na unidade do cadastro e total pago pela
linha. Ex.: duas embalagens de 100 folhas = 200 un. A data é a data atual.
Confira os itens antes de confirmar: compras confirmadas ficam disponíveis para
consulta e não são editadas ou excluídas nesta versão.

A confirmação salva a compra, dá entrada na variação e atualiza o preço e a data
do insumo em uma transação única. Preço da embalagem = total pago ÷ quantidade
comprada × quantidade por embalagem cadastrada. Se o mesmo insumo aparece em
várias linhas/cores, o preço é calculado sobre os totais da compra, igual para
as cores. Os custos e preços sugeridos dos produtos passam a usar o novo custo;
os preços dos pedidos já gravados continuam os valores originais.

Relatórios mostram vendas, compras pagas, saldo comercial e resultado positivo,
negativo ou equilibrado por mês, inclusive no PDF. Vendas usam o mês de cadastro
do pedido, excluindo presentes e pedidos sem preço; não são recebimentos por
data de pagamento. Compras usam a data do registro. Não há outras despesas,
tributos ou histórico completo de recebimentos: o saldo não é lucro líquido nem
fluxo de caixa. Compras anteriores não registradas não entram no relatório.

Estoque parado significa saldo positivo atual dos insumos/variações, incluindo
inativos, ao custo cadastrado mais recente. Saldos negativos não reduzem esse
valor. Não é avaliação histórica do mês nem classificação por tempo sem venda.

Para compilar: baixe a branch main e execute `compilar_windows.bat`. A configuração
do atualizador já está preparada com a versão 2.1.0 e o endereço deste repositório.
Não é necessário alterar release-version.txt para compilar localmente; alterá-lo
aciona o GitHub Actions. Esta entrega não publica uma Release automaticamente.

## Build 2.1.1 — janela e identidade visual

O ERP abre maximizado, mantendo os controles de fechar e a barra do Windows.
F11 alterna tela cheia e Esc sai dela. Em telas menores, barras de rolagem
mantêm o menu e a área de trabalho acessíveis; o rodapé do produto tem espaço
reservado para salvar. Janelas de cadastro respeitam o tamanho da tela.

O tema usa bordô #7A2E3A, verde botânico #55613F, dourado #C79A5A,
pergaminho #F6F1E8, bege #D8B08C e marrom #3A2417. Títulos usam
Cormorant Garamond/Garamond quando instaladas, com alternativa Georgia;
textos usam Libre Franklin/Montserrat, com alternativa Segoe UI. Nenhuma
fonte precisa ser baixada para usar o ERP offline.

Compile com compilar_windows.bat. A versão do atualizador está em 2.1.1.

## Build 2.2.0 — rendimento do produto base e tabelas

Todas as tabelas têm linhas alternadas, destaque dourado sob o mouse e seleção
bordô com texto branco. Alertas de estoque negativo continuam visíveis.

No produto, informe quantas unidades a composição do produto base produz.
Exemplo: 1 folha + os demais materiais para fabricar 5 chaveiros → rendimento 5.
Cadastre as quantidades de TODOS os insumos para essas 5 peças. O custo da
composição é dividido por 5 para obter o custo unitário e o preço sugerido.
O preço de tabela também é por peça. No pedido, informe o total de peças:
1 consome 0,2 da receita; 5 consomem 1 receita; 10 consomem 2 receitas.
A baixa preserva a cor/variação escolhida. Não arredonda folhas para cima.

Cadastros anteriores recebem rendimento 1; só altere o rendimento depois de
conferir se a composição representa o lote inteiro. Se o preço de tabela antigo
era de um kit, ajuste-o para o preço por peça. Vender um kit de 5 corresponde a
quantidade 5 no pedido; não há cadastro separado de tamanhos de kit nesta versão.

Alterar o rendimento não altera pedidos ou estoque já movimentado. Editar
somente pagamento/entrega preserva a baixa anterior. Ao mudar os itens ou as
quantidades de um pedido, o ERP estorna a baixa anterior e aplica a composição
e o rendimento atuais. Excluir o pedido estorna a quantidade efetivamente baixada.

Compile com compilar_windows.bat. Versão preparada: 2.2.0.


## Build 2.2.1 — clientes e categorias de insumos

Atualização sobre a base restaurada da build 2.2.0, com três alterações:

- **Clientes:** nova aba para cadastrar, buscar e editar nome, telefone, e-mail, data de nascimento e endereço. Somente o nome é obrigatório.
- **Insumos:** categoria Produção ou Embalagem no cadastro, na tabela e no filtro. Insumos de bases anteriores começam como Produção; edite os insumos de embalagem para classificá-los. A migração preserva os registros existentes.
- **Produtos:** a composição apresenta duas listas, Produção e Embalagem, cada uma com seleção, adição e remoção de insumos da sua categoria. As duas listas compõem o mesmo produto e entram no mesmo cálculo de custo e rendimento. O formulário tem rolagem e mantém o botão Salvar visível.

O fluxo de pedidos e as fórmulas de precificação e estoque são os da build 2.2.0. O cadastro de clientes é uma aba independente nesta atualização.

Para compilar, baixe o projeto completo e execute `compilar_windows.bat`. Versão interna: 2.2.1. Este commit não publica uma Release nem altera `release-version.txt`.

Verificação: 23 testes passaram; 10 testes de importação histórica foram ignorados porque exigem a planilha privada, que não está no repositório. Os novos testes cobrem clientes, migração, reclassificação de insumos e preservação do cálculo e do consumo de estoque. A interface ainda precisa de validação visual no Windows.
