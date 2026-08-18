# Central Neotass — Compras, Faturamento e DRE por Projeto
# Fonte: briefing "Integração Monday.com + Make + Omie ERP" (Neotass, ago/2026)
#
# PAPEL DA CENTRAL: ela entra no lugar do Make. O Monday continua sendo onde a
# operação digita; o Omie continua sendo o motor fiscal. A Central é a camada que
# decide, garante e registra — e é a única porta para o Omie.
#
# O que NÃO é modelado aqui, de propósito: fila, outbox, retentativa, lock,
# webhook e trilha de eventos. Tudo isso é do módulo `integrations` do Core.
# Regra da casa: nunca recriar o que o Core já tem.

central neotass-projetos
  nome "Neotass · Operação"
  menu manual
  tenancy single_tenant
  modulos collections documents pipelines integrations omie
  api /api/neotass
  ativacao-campo razaoSocial text obrig "Razão social da base Omie"
  ativacao-campo cnpj text obrig "CNPJ da base Omie"
  ativacao-campo cotacoesMinimas number obrig "Cotações mínimas para aprovar uma compra" pad=3
  ativacao-campo quadroCompras text "ID do quadro de Compras no Monday"
  ativacao-campo quadroFaturamento text "ID do quadro de Faturamento no Monday"
  ativacao-campo emailFinanceiro text "E-mail do Financeiro para pendências"

painel visao /visao-geral "A operação hoje" Início
  ordem 1
  icone 📊
  indicador soma Projeto.receitaAprovada "Receita aprovada pelos clientes"
    nota "Soma dos POs. É o teto do que pode ser faturado."
  indicador soma Projeto.custoComprometido "Custo já comprometido"
    nota "Tudo que já virou conta a pagar. Compra cancelada não conta."
  indicador soma Projeto.margemRealizada "Margem realizada"
    nota "Receita faturada menos custo comprometido. É o lucro que já existe."
  indicador soma Projeto.saldoDeCompra "Ainda pode ser comprado"
    nota "Custo aprovado menos custo comprometido. Quando zera, a Central trava a compra."
  indicador contagem Projeto "Projetos em execução" onde situacao == Em execução
    nota "Eventos e campanhas acontecendo agora."
  indicador contagem ContaPagar "Envios ao Omie com erro" onde situacao == Com erro
    nota "Se este número não for zero, alguém precisa olhar hoje."
  indicador contagem SolicitacaoCompra "Compras esperando aprovação" onde situacao == Em aprovação
    nota "Paradas até alguém da alçada aprovar."
  indicador contagem SolicitacaoFaturamento "Faturamentos esperando aprovação" onde situacao == Em aprovação
    nota "Cada dia aqui é um dia sem nota emitida."
  indicador contagem Fornecedor "Fornecedores novos para analisar" onde situacao == Recebido
    nota "Chegaram pelo formulário público e ainda não foram ao Omie."
  indicador agrupa-contagem SolicitacaoCompra por situacao "Compras por etapa"
    nota "Onde as compras estão travando."
  indicador agrupa-soma SolicitacaoFaturamento.valor por situacao "Faturamento por etapa (R$)"
    nota "Quanto dinheiro está parado em cada etapa."
  indicador agrupa-soma Projeto.margemRealizada por tipo "Margem realizada por tipo de projeto"
    nota "Onde a agência ganha mais: evento, campanha, mídia ou produção."

pagina tutorial /tutorial "Como operar"
  secao Início
  ordem 2
  icone 📖
  bloco "O menu tem cinco lugares" "Entendeu o menu, entendeu o sistema."
    texto "A operação hoje — os números da agência inteira numa tela. Comece o dia aqui."
    texto "Compras, Faturamento, Fornecedores — onde o trabalho acontece. Cada tela é um quadro: as colunas são as etapas, e você arrasta o cartão de uma para a outra."
    texto "Projetos — o dinheiro de cada evento: quanto o cliente aprovou, quanto já gastamos, quanto sobrou."
    texto "Contas a pagar — o que foi para o Omie e o que deu erro."
    texto "Cadastros — cliente, departamento e alçada. Mexe-se uma vez por mês."
  bloco "Uma compra, do início ao fim" "Operação › Compras"
    texto "1. Novo ticket, com o projeto e o que se quer comprar."
    texto "2. Abra o cartão e lance os orçamentos na aba Mapa de cotações. A Central conta quantos chegaram e mostra o menor."
    texto "3. Arraste até Aprovada. Se o valor pede Diretoria, a coluna não aceita sem ela."
    texto "4. Pronto: o fornecedor e o contas a pagar nascem no Omie, com o código do projeto e o departamento."
  bloco "Um faturamento, do início ao fim" "Operação › Faturamento"
    texto "1. Novo ticket com cliente, projeto, valor e a aprovação do cliente anexada."
    texto "2. Arraste até Aprovada, dentro da alçada. A O.S. nasce em rascunho no Omie."
    texto "3. Faturado no Omie, o cartão vira Faturada com o número da nota, e o PDF volta para o Monday."
  bloco "O que a Central recusa fazer" "Isto não é limitação: é a regra escrita onde ninguém esquece dela."
    texto "Comprar acima do custo aprovado do projeto — nem de uma vez, nem fatiado em parcelas."
    texto "Faturar acima do que o cliente aprovou."
    texto "Aprovar fora da alçada da faixa de valor."
    texto "Mandar ao Omie despesa ou receita sem código de projeto e de departamento."
    texto "Antedatar um lançamento: a data de criação é do servidor."

esteira SolicitacaoCompra /compras-esteira "Compras" Operação 3
  icone 🛒
esteira SolicitacaoFaturamento /faturamento-esteira "Faturamento" Operação 4
  icone 🧾
esteira Fornecedor /fornecedores-esteira "Fornecedores" Operação 5
  icone 🤝

entidade Departamento
  rotulo Departamentos
  oculta
  rota /departamentos
  secao Cadastros
  titulo nome
  campo codigo texto obrig unico busca "Código no Omie"
  campo nome texto obrig busca "Departamento"
  campo situacao enum(Ativo|Inativo) obrig idx pad=Ativo "Situação"
  colunas codigo nome situacao
  grupo Identificação: codigo nome situacao
  protege-exclusao Projeto.departamento "Não é possível excluir um departamento com projeto vinculado."

entidade Cliente
  rotulo Clientes
  oculta
  rota /clientes
  secao Cadastros
  titulo nome
  campo nome texto obrig busca "Cliente"
  campo razaoSocial texto "Razão social"
  campo cnpj texto obrig unico busca "CNPJ"
  campo codigoOmie texto "Código no Omie"
  campo responsavel texto idx "Atendimento responsável"
  campo situacao enum(Ativo|Inativo) obrig idx pad=Ativo "Situação"
  colunas nome cnpj responsavel situacao
  grupo Identificação: nome razaoSocial cnpj codigoOmie
  grupo Operação: responsavel situacao
  relacao projetos <- Projeto.cliente "Projetos do cliente"
  grade-relacionada projetos: codigo nome receitaAprovada custoComprometido margemRealizada situacao
  protege-exclusao Projeto.cliente "Não é possível excluir um cliente que já tem projeto."

entidade Projeto
  rotulo Projetos
  rota /projetos
  secao Projetos
  ordem 6
  icone 🎪
  titulo nome
  campo codigo texto obrig unico busca "Código do projeto"
  campo nome texto obrig busca "Projeto"
  campo cliente ref(Cliente) obrig idx "Cliente"
  campo departamento ref(Departamento) obrig idx "Departamento"
  campo codigoDepartamento texto <- Departamento.codigo via departamento "Código do departamento"
  campo tipo enum(Evento|Campanha|Mídia|Produção|Outro) obrig idx pad=Evento "Tipo"
  campo dataInicio data obrig idx "Início"
  campo dataFim data "Encerramento"
  campo receitaAprovada moeda obrig "Receita aprovada pelo cliente (PO)"
  campo custoAprovado moeda obrig "Custo aprovado do projeto"
  campo custoComprometido moeda = soma(ContaPagar.valor por projeto) onde situacao != Cancelada "Custo comprometido"
  campo saldoDeCompra moeda = custoAprovado - custoComprometido "Saldo para comprar"
  campo receitaSolicitada moeda = soma(SolicitacaoFaturamento.valor por projeto) onde situacao != Recusada "Receita solicitada"
  campo receitaFaturada moeda = soma(SolicitacaoFaturamento.valor por projeto) onde situacao == Faturada "Receita faturada"
  campo margemPrevista moeda = receitaAprovada - custoAprovado "Margem prevista"
  campo margemRealizada moeda = receitaFaturada - custoComprometido "Margem realizada"
  campo situacao fluxo [Em orçamento -> Aprovado -> Em execução -> Encerrado; Em orçamento -> Cancelado] obrig idx pad=Em orçamento "Situação"
  colunas codigo nome cliente receitaAprovada custoAprovado custoComprometido margemRealizada situacao
  grupo Identificação: codigo nome cliente departamento
  grupo Classificação: tipo situacao dataInicio dataFim
  grupo Orçamento aprovado: receitaAprovada custoAprovado margemPrevista
  grupo Realizado 1col: custoComprometido saldoDeCompra receitaSolicitada receitaFaturada margemRealizada
  grupo Tags do DRE: codigoDepartamento
  relacao compras <- SolicitacaoCompra.projeto "Compras do projeto"
  relacao contasPagar <- ContaPagar.projeto "Contas a pagar"
  relacao faturamentos <- SolicitacaoFaturamento.projeto "Solicitações de faturamento"
  grade-relacionada compras: numero descricao valorEstimado cotacoesRecebidas menorCotacao situacao
  grade-relacionada contasPagar: numero fornecedor valor vencimento situacao
  grade-relacionada faturamentos: numero descricaoServicos valor papelExigido situacao
  invariante soma(ContaPagar.valor por projeto) <= custoAprovado onde situacao != Cancelada "A soma das contas a pagar não pode ultrapassar o custo aprovado do projeto."
  invariante soma(SolicitacaoFaturamento.valor por projeto) <= receitaAprovada onde situacao != Recusada "Não é possível solicitar faturamento acima da receita aprovada pelo cliente neste projeto."
  protege-exclusao ContaPagar.projeto "Não é possível excluir um projeto que já tem conta a pagar."

entidade RegraAlcada
  rotulo Alçadas de aprovação
  oculta
  singular regraAlcada
  rota /alcadas
  secao Governança
  titulo nome
  campo nome texto obrig unico busca "Faixa"
  campo aplicaA enum(Compra|Faturamento|Ambos) obrig idx pad=Ambos "Aplica-se a"
  campo valorMinimo moeda obrig "Valor mínimo"
  campo valorMaximo moeda obrig "Valor máximo"
  campo papelExigido enum(Coordenação|Gerência|CFO|Diretoria) obrig idx "Quem precisa aprovar"
  campo exigeDoisAprovadores bool obrig idx pad=false "Exige dois aprovadores"
  campo situacao enum(Ativa|Inativa) obrig idx pad=Ativa "Situação"
  colunas nome aplicaA valorMinimo valorMaximo papelExigido exigeDoisAprovadores situacao
  grupo Faixa: nome aplicaA valorMinimo valorMaximo
  grupo Exigência: papelExigido exigeDoisAprovadores situacao

entidade Fornecedor
  rotulo Fornecedores
  oculta
  rota /fornecedores
  secao Compras
  titulo razaoSocial
  campo razaoSocial texto obrig busca "Razão social"
  campo cnpjCpf texto obrig unico busca "CNPJ / CPF"
  campo origem enum(Formulário público|Cadastro interno) obrig idx pad=Formulário público "Origem"
  campo email texto "E-mail"
  campo nomeFantasia texto busca "Nome fantasia"
  campo telefone texto "Telefone"
  campo banco texto "Banco"
  campo agencia texto "Agência"
  campo conta texto "Conta"
  campo tipoConta enum(Corrente|Poupança) "Tipo de conta"
  campo tipoChavePix enum(CNPJ|CPF|E-mail|Telefone|Aleatória) "Tipo de chave PIX"
  campo chavePix texto "Chave PIX"
  campo codigoOmie texto "Código no Omie"
  campo motivoRecusa texto "Motivo da recusa"
  campo situacao fluxo [Recebido -> Em análise -> Aprovado -> Enviado ao ERP; Em análise -> Recusado] obrig idx pad=Recebido "Situação"
  colunas razaoSocial cnpjCpf origem codigoOmie situacao
  grupo Identificação: razaoSocial nomeFantasia cnpjCpf origem
  grupo Contato: email telefone
  grupo Dados bancários: banco agencia conta tipoConta
  grupo PIX: tipoChavePix chavePix
  grupo Análise 1col: situacao motivoRecusa codigoOmie
  protege-exclusao Cotacao.fornecedor "Não é possível excluir um fornecedor que já foi cotado."

entidade SolicitacaoCompra
  rotulo Solicitações de compra
  oculta
  singular solicitacaoCompra
  rota /compras
  secao Compras
  titulo descricao
  campo descricao texto obrig busca "Item ou serviço"
  campo projeto ref(Projeto) obrig idx "Projeto"
  campo valorEstimado moeda obrig "Valor estimado"
  campo papelExigido enum(Coordenação|Gerência|CFO|Diretoria) idx "Alçada exigida"
  campo numero texto obrig unico busca "Número"
  campo codigoProjeto texto <- Projeto.codigo via projeto "Código do projeto"
  campo codigoDepartamento texto <- Projeto.codigoDepartamento via projeto "Código do departamento"
  campo categoria enum(Locação|Alimentação|Produção|Cenografia|Transporte|Mídia|Cachê|Brindes|Outro) obrig idx "Categoria"
  campo comprador texto obrig idx "Comprador"
  campo cotacoesRecebidas numero = contagem(Cotacao.valor por solicitacao) "Cotações recebidas"
  campo menorCotacao moeda = menor(Cotacao.valor por solicitacao) "Menor cotação"
  campo valorAprovado moeda "Valor aprovado"
  campo justificativaEscolha texto "Justificativa da escolha"
  campo aprovadoPor texto "Aprovado por"
  campo aprovadoEm data "Aprovado em"
  campo idMonday texto idx "Item no Monday"
  campo situacao fluxo [Rascunho -> Cotando -> Em aprovação -> Aprovada -> Comprada; Em aprovação -> Reprovada] obrig idx pad=Rascunho "Situação"
  colunas numero projeto descricao valorEstimado cotacoesRecebidas menorCotacao papelExigido situacao
  grupo Solicitação: numero projeto descricao categoria
  grupo Valores: valorEstimado menorCotacao cotacoesRecebidas valorAprovado
  grupo Aprovação: papelExigido aprovadoPor aprovadoEm situacao
  grupo Justificativa 1col: justificativaEscolha
  grupo Tags do DRE: codigoProjeto codigoDepartamento
  relacao cotacoes <- Cotacao.solicitacao "Mapa de cotações"
  grade-relacionada cotacoes editavel: fornecedorNome valor prazoDias condicaoPagamento escolhida
  protege-exclusao Cotacao.solicitacao "Não é possível excluir uma solicitação que já tem cotação."

entidade Cotacao
  rotulo Cotações
  oculta
  rota /cotacoes
  secao Compras
  titulo fornecedorNome
  campo solicitacao ref(SolicitacaoCompra) obrig idx "Solicitação de compra"
  campo fornecedor ref(Fornecedor) obrig idx "Fornecedor"
  campo fornecedorNome texto <- Fornecedor.razaoSocial via fornecedor "Fornecedor"
  campo valor moeda obrig "Valor cotado"
  campo prazoDias numero "Prazo de entrega (dias)"
  campo condicaoPagamento texto "Condição de pagamento"
  campo escolhida bool obrig idx pad=false "Escolhida"
  campo observacao texto "Observação"
  colunas fornecedorNome valor prazoDias condicaoPagamento escolhida
  grupo Cotação: solicitacao fornecedor valor
  grupo Condições: prazoDias condicaoPagamento escolhida
  grupo Observação 1col: observacao

entidade ContaPagar
  rotulo Contas a pagar
  singular contaPagar
  rota /contas-a-pagar
  secao Financeiro
  ordem 7
  icone 💸
  titulo numero
  campo numero texto obrig unico busca "Número"
  campo projeto ref(Projeto) obrig idx "Projeto"
  campo codigoProjeto texto <- Projeto.codigo via projeto "Código do projeto"
  campo codigoDepartamento texto <- Projeto.codigoDepartamento via projeto "Código do departamento"
  campo solicitacao ref(SolicitacaoCompra) idx "Solicitação de compra"
  campo fornecedor ref(Fornecedor) obrig idx "Fornecedor"
  campo descricao texto obrig busca "Descrição"
  campo categoriaFinanceira texto obrig "Categoria no Omie"
  campo valor moeda obrig "Valor"
  campo vencimento data obrig idx "Vencimento"
  campo codigoLancamento texto "Lançamento no Omie"
  campo ultimoErro texto "Último erro do Omie"
  campo situacao enum(A enviar|Enviada|Confirmada|Com erro|Cancelada) obrig idx pad=A enviar "Situação"
  colunas numero projeto fornecedor valor vencimento situacao
  grupo Documento: numero projeto fornecedor solicitacao
  grupo Valor e prazo: valor vencimento categoriaFinanceira
  grupo Descrição 1col: descricao
  grupo Integração 1col: situacao codigoLancamento ultimoErro
  grupo Tags do DRE: codigoProjeto codigoDepartamento

entidade SolicitacaoFaturamento
  rotulo Solicitações de faturamento
  oculta
  singular solicitacaoFaturamento
  rota /faturamento
  secao Faturamento
  titulo numero
  campo numero texto obrig unico busca "Número"
  campo projeto ref(Projeto) obrig idx "Projeto"
  campo valor moeda obrig "Valor"
  campo papelExigido enum(Coordenação|Gerência|CFO|Diretoria) idx "Alçada exigida"
  campo codigoProjeto texto <- Projeto.codigo via projeto "Código do projeto"
  campo codigoDepartamento texto <- Projeto.codigoDepartamento via projeto "Código do departamento"
  campo descricaoServicos texto obrig busca "Descrição dos serviços"
  campo condicaoPagamento enum(À vista|15 dias|30 dias|30/60|30/60/90|Personalizada) obrig "Condição de pagamento"
  campo dataPrevistaFaturamento data idx "Previsão de faturamento"
  campo aprovadoPor texto "Aprovado por"
  campo aprovadoEm data "Aprovado em"
  campo numeroOs texto "O.S. no Omie"
  campo numeroNfse texto "Número da NFS-e"
  campo linkNfse texto "PDF da NFS-e"
  campo ultimoErro texto "Último erro do Omie"
  campo idMonday texto idx "Item no Monday"
  campo situacao fluxo [Rascunho -> Em aprovação -> Aprovada -> Enviada ao ERP -> Faturada; Em aprovação -> Recusada] obrig idx pad=Rascunho "Situação"
  colunas numero projeto descricaoServicos valor papelExigido dataPrevistaFaturamento situacao
  grupo Solicitação: numero projeto valor condicaoPagamento
  grupo Serviços 1col: descricaoServicos
  grupo Aprovação: papelExigido aprovadoPor aprovadoEm dataPrevistaFaturamento
  grupo Retorno do Omie: numeroOs numeroNfse linkNfse ultimoErro
  grupo Tags do DRE: codigoProjeto codigoDepartamento

pagina cadastros /cadastros "Cadastros"
  secao Ajustes
  ordem 8
  icone 🗂
  bloco "O que se cadastra uma vez" "Estes três cadastros mudam pouco e sustentam todo o resto: o cliente, o departamento que carimba o DRE e a faixa de valor que define quem aprova."
    texto "Se um deles estiver faltando, a Central trava o que depende dele — de propósito. É melhor travar do que gravar um número inventado."
  grade Cliente "Clientes da agência"
  grade Departamento "Departamentos (o carimbo do DRE no Omie)"
  grade RegraAlcada "Alçadas — quem aprova cada faixa de valor"

navegacao-extra "Conexão com o Omie" /integracoes
  secao Ajustes
  icone 🔌
