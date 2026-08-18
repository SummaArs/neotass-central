"use strict";
/**
 * REMENDO DO CORE 0.4.15 — invariante atômico que soma os irmãos já gravados.
 *
 * DEFEITO (reprovado nesta Central em 18/08/2026):
 * `processRuntime.assertAtomicInvariants` monta o `$match` do aggregate com o id
 * do pai TAL COMO veio no corpo da requisição — string, via REST. Query de model
 * o Mongoose casta para ObjectId; pipeline de aggregate NÃO. A soma dos irmãos
 * volta 0 e o Core passa a testar apenas "este registro, sozinho, cabe no teto?".
 * Medido: projeto com teto de R$ 1.240.000 aceitou R$ 1.946.900 (uma conta de
 * 600 mil + três parcelas de 200 mil), devolvendo 201 em todas.
 *
 * Este arquivo reimplementa a MESMA regra declarada em `central.process.json`,
 * com o id castado e com o `match` da regra aplicado. Não inventa regra nova:
 * a fonte continua sendo o manifesto. Apagar quando o Core corrigir.
 */

const path = require("node:path");
const mongoose = require("mongoose");
const { GenericError, registry } = require("@oondemand/oon-core-back");
const { adicionar } = require("./registro");

const processo = require(path.join(__dirname, "../../central.process.json"));

/** aceita "64f...", ObjectId, ou o objeto populado { _id } */
function paraId(valor) {
  if (!valor) return null;
  const cru = typeof valor === "object" && valor._id ? valor._id : valor;
  if (cru instanceof mongoose.Types.ObjectId) return cru;
  return mongoose.Types.ObjectId.isValid(String(cru)) ? new mongoose.Types.ObjectId(String(cru)) : null;
}

/** match do manifesto (eq/neq/in/nin) -> filtro do Mongo */
function paraFiltroMongo(match = {}) {
  const q = {};
  for (const [campo, cond] of Object.entries(match || {})) {
    if (cond && typeof cond === "object" && !Array.isArray(cond)) {
      if ("eq" in cond) q[campo] = cond.eq;
      else if ("neq" in cond) q[campo] = { $ne: cond.neq };
      else if ("in" in cond) q[campo] = { $in: cond.in };
      else if ("nin" in cond) q[campo] = { $nin: cond.nin };
    } else q[campo] = cond;
  }
  return q;
}

/** o candidato só entra na soma se ele mesmo satisfizer o match */
function candidatoCasa(estado, match = {}) {
  for (const [campo, cond] of Object.entries(match || {})) {
    const v = estado[campo];
    if (cond && typeof cond === "object" && !Array.isArray(cond)) {
      if ("eq" in cond && v !== cond.eq) return false;
      if ("neq" in cond && v === cond.neq) return false;
      if ("in" in cond && !cond.in.includes(v)) return false;
      if ("nin" in cond && cond.nin.includes(v)) return false;
    } else if (v !== cond) return false;
  }
  return true;
}

const modelo = (nome) => registry.getModel(nome).mongooseModel;

for (const [nomeModel, regras] of Object.entries(processo.models || {})) {
  const invariantes = (regras.atomicInvariants || []).filter((r) => r.kind === "relatedSumLteParentField");
  if (!invariantes.length) continue;

  adicionar(nomeModel, async (dados, ctx = {}) => {
    // numa atualização parcial, o estado que vale é o gravado + o que chegou
    const estado = { ...(ctx.current || {}), ...dados };

    for (const regra of invariantes) {
      const paiId = paraId(estado[regra.parentLocalField]);
      if (!paiId) continue;

      const filtro = { [regra.parentLocalField]: paiId, ...paraFiltroMongo(regra.match) };
      const atualId = paraId(ctx.current && ctx.current._id);
      if (atualId) filtro._id = { $ne: atualId };

      let consulta = modelo(nomeModel).aggregate([
        { $match: filtro },
        { $group: { _id: null, total: { $sum: { $ifNull: [`$${regra.sourceField}`, 0] } } } },
      ]);
      if (ctx.session && typeof consulta.session === "function") consulta = consulta.session(ctx.session);
      const [linha] = await consulta;

      const irmaos = Number((linha && linha.total) || 0);
      const candidato = candidatoCasa(estado, regra.match) ? Number(estado[regra.sourceField] || 0) : 0;
      const total = irmaos + candidato;

      let paiQuery = modelo(regra.parentModel).findById(paiId).lean();
      if (ctx.session) paiQuery = paiQuery.session(ctx.session);
      const pai = await paiQuery;
      if (!pai) continue;   // pai ausente já é tratado pelo Core

      const limite = Number(pai[regra.parentField] || 0) + Number(regra.tolerance || 0);
      if (total > limite) {
        throw new GenericError(regra.message, {
          statusCode: 409,
          details: { field: regra.sourceField, rule: regra.name, message: regra.message, total, limit: limite },
        });
      }
    }
  });
}
