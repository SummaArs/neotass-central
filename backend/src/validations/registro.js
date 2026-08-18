"use strict";
/**
 * Registro de validações da Central — compositor.
 *
 * ARMADILHA DO CORE (0.4.7): `defineValidation(model, fn)` faz
 * `store.validations.set(model, fn)` — a segunda chamada para a mesma model
 * **substitui** a primeira, sem aviso. (`defineTrigger`, por comparação,
 * acumula em lista.) Duas regras escritas em arquivos diferentes para a mesma
 * model ⇒ uma delas simplesmente não roda, e nada indica isso.
 *
 * Aqui as validações são acumuladas e registradas como uma função só.
 * Use SEMPRE `adicionar()` — nunca `defineValidation` direto.
 */

const { defineValidation } = require("@oondemand/oon-core-back");

const porModel = new Map();

function adicionar(modelName, fn) {
  if (typeof fn !== "function") throw new Error(`validação de ${modelName} deve ser função`);
  if (!porModel.has(modelName)) {
    porModel.set(modelName, []);
    defineValidation(modelName, async (dados, ctx) => {
      for (const validacao of porModel.get(modelName)) await validacao(dados, ctx);
    });
  }
  porModel.get(modelName).push(fn);
}

const registradas = (modelName) => (porModel.get(modelName) || []).length;

module.exports = { adicionar, registradas };
