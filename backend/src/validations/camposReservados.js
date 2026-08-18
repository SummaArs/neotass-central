"use strict";
/**
 * REMENDO DO CORE 0.4.15 — campos que só o servidor pode escrever.
 *
 * DEFEITO (oon-prove D5/D9/D8, aberto desde a 0.3.74 e medido de novo aqui):
 * `crudService.js` faz `new Model(req.body)` sem filtrar. O Mongoose descarta
 * chave fora do schema, mas `_id`, `createdAt` e `updatedAt` SÃO do schema. Logo:
 *   - o cliente escolhe o `_id` e passa a poder ocupar identidade alheia;
 *   - o cliente escolhe o `createdAt` e ANTEDATA um lançamento — numa Central com
 *     contas a pagar e faturamento, isso é adulterar a trilha de auditoria;
 *   - PUT com `_id` divergente estoura 500 vindo do Mongo, em vez de 4xx.
 *
 * Aqui esses campos passam a ser recusados na entrada, em todas as models.
 * Apagar quando o Core filtrar o corpo da requisição.
 */

const path = require("node:path");
const { GenericError } = require("@oondemand/oon-core-back");
const { adicionar } = require("./registro");

const dominio = require(path.join(__dirname, "../../central.domain.json"));

/**
 * CUIDADO (medido em 18/08/2026): na ATUALIZAÇÃO o Core entrega à validação o
 * documento inteiro já mesclado — logo `createdAt`, `updatedAt` e `_id` chegam
 * mesmo quando o cliente mandou só um campo. Recusar por presença barra toda
 * edição legítima (comprovado: PUT {situacao} devolvia 422). O critério certo é
 * DIVERGÊNCIA do que está gravado, não presença.
 */
const igual = (a, b) => {
  if (a === undefined || a === null || b === undefined || b === null) return false;
  const da = new Date(a).getTime(), db = new Date(b).getTime();
  if (!Number.isNaN(da) && !Number.isNaN(db)) return da === db;
  return String(a) === String(b);
};
const recusar = (campo, mensagem) => {
  throw new GenericError(mensagem, { statusCode: 422, details: { field: campo, rule: "camposReservados" } });
};

for (const model of dominio.models || []) {
  adicionar(model.name, async (dados, ctx = {}) => {
    const criando = !(ctx.current && ctx.current._id);

    if (criando) {
      // na criação nada disso pode vir do cliente
      for (const campo of ["_id", "createdAt", "updatedAt"]) {
        if (dados[campo] !== undefined) {
          recusar(campo, `O campo ${campo} é definido pelo servidor e não pode ser enviado na criação.`);
        }
      }
      return;
    }

    // na atualização: identidade e data de criação são imutáveis.
    // `updatedAt` fica de fora — é o servidor que a move a cada gravação.
    if (dados._id !== undefined && !igual(dados._id, ctx.current._id)) {
      recusar("_id", "O identificador do registro não pode ser alterado.");
    }
    if (dados.createdAt !== undefined && !igual(dados.createdAt, ctx.current.createdAt)) {
      recusar("createdAt", "A data de criação do registro não pode ser alterada.");
    }
  });
}
