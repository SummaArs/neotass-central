# Neotass · Operação

Central OonDemand que substitui o **Make** entre o **Monday** e o **Omie**.

A operação continua digitando no Monday. O Omie continua sendo o motor fiscal, restrito ao Financeiro.
No meio, esta Central é a camada que **decide, garante e registra** — e a única porta para o Omie.

---

## Rodar em 4 comandos

```bash
cp backend/.env.example backend/.env && cp frontend/.env.example frontend/.env
node ~/Python/ooncore_kb/tools/ativar-local.js .
npm run dev:backend
npm run dev:frontend    # http://localhost:5175/?code=dev-local
```

Precisa de MongoDB em **replica set** (invariante atômico roda em transação).

## O menu tem 9 itens

| | Item | Para quê |
|---|---|---|
| 📊 | A operação hoje | 12 indicadores: quanto entra, quanto sobra, o que está parado |
| 📖 | Como operar | tutorial de uma tela |
| 🛒 | Compras | quadro + lista + criar, com mapa de cotações dentro do cartão |
| 🧾 | Faturamento | solicitação de O.S. com alçada por faixa de valor |
| 🤝 | Fornecedores | fila do que chegou pelo formulário público |
| 🎪 | Projetos | o DRE de cada evento |
| 💸 | Contas a pagar | o que foi ao Omie e o que deu erro |
| 🗂 | Cadastros | cliente, departamento e alçada, numa página só |
| 🔌 | Conexão com o Omie | credenciais e fila de integração (nativo do Core) |

## O que a Central recusa fazer

Estas regras vivem no manifesto, não em código, e são recusa de servidor — não aviso de tela:

- comprometer em contas a pagar **mais que o custo aprovado** do projeto — nem de uma vez, nem fatiado;
- solicitar faturamento **acima da receita aprovada** pelo cliente (o PO);
- pular etapa do fluxo (quem apura não fatura sozinho);
- excluir projeto com conta, cliente com projeto ou fornecedor já cotado;
- antedatar um lançamento — `createdAt` é do servidor.

## Provas

Rodadas nesta Central, sem IA e sem token:

| prova | resultado |
|---|---|
| portão (validadores do Core 0.4.15 + referências cruzadas) | 4/4 |
| arnês adversarial do manifesto | **48/48** |
| `oon-lint` (manifesto × backend) | 0 problemas |
| `oon-prove` (23 invariantes por HTTP contra backend real) | **20/20** |
| fronteira do invariante de orçamento, ao centavo | **5/5** |
| operação legítima ponta a ponta | **10/10** |

Sem o remendo de invariante, um projeto com teto de R$ 1.240.000 aceitou R$ 1.946.900.

## Três remendos do Core (`backend/src/validations`)

Achados medidos aqui, com o conserto do lado da Central. Apagar quando o Core corrigir:

1. **`invariantesAtomicos.js`** — `assertAtomicInvariants` não casta o id do pai no `$match` do aggregate,
   então a soma dos irmãos volta 0 e o teto é furado em parcelas. Aqui a regra é relida do próprio
   `central.process.json`, com o id castado e o `match` aplicado.
2. **`camposReservados.js`** — o Core persiste `_id`, `createdAt` e `updatedAt` vindos do corpo da
   requisição (`oon-prove` D5/D9/D8). Fecha os três. Atenção: na atualização o Core entrega o documento
   inteiro à validação, então o critério é **divergência do gravado**, não presença.
3. **`registro.js`** — `defineValidation` é `Map.set`: a segunda validação da mesma model apaga a
   primeira, sem aviso. Este compositor acumula.

## Como foi construída

O domínio não foi escrito à mão. `docs/central.spec` (≈320 linhas) é compilada nos quatro manifestos
(≈1.500 linhas) por um compilador determinístico, e o resultado passa por um portão com os validadores
do próprio Core antes de entrar aqui.

## Falta para produção

1. resolver a alçada pela faixa cadastrada (`RegraAlcada`);
2. provider `monday` (webhook de entrada) e os mappings do Omie;
3. exigir o mínimo de cotações para aprovar;
4. RBAC por papel.
