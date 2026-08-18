const { defineTrigger, omie } = require("@oondemand/oon-core-back");

/**
 * Após criar/alterar uma Pessoa, enfileira o sync com a Omie usando o mapping
 * declarado. No-op seguro se a Omie não estiver configurada (sem app_key).
 */
defineTrigger("Pessoa", {
  after: async (doc) => {
    await omie.sync({
      mapping: "pessoa-cliente",
      payload: { idPessoa: String(doc._id), nome: doc.nome, email: doc.email, documento: doc.documento },
    });
  },
});
