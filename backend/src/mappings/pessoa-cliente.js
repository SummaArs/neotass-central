const { defineOmieMapping } = require("@oondemand/oon-core-back");

/**
 * Mapping de domínio Pessoa -> Cliente Omie. `toOmie` traduz o payload do
 * domínio na chamada da API Omie. O engine (chaves, fila, retries) é do Core.
 */
defineOmieMapping("pessoa-cliente", {
  toOmie: (pessoa) => ({
    endpoint: "geral/clientes/",
    call: "IncluirCliente",
    param: [
      {
        codigo_cliente_integracao: String(pessoa.idPessoa || pessoa._id || ""),
        razao_social: pessoa.nome,
        email: pessoa.email,
        cnpj_cpf: pessoa.documento,
      },
    ],
  }),
});
