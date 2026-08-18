/**
 * Central Neotass — só os caminhos do domínio.
 *
 * Identidade (name, slug, appKind), módulos e ativação vivem em
 * `central.app.json`. O conformance do create-central-oon reprova se forem
 * declarados aqui também (CENTRAL_CONFIG_BOUNDARY) — e está certo: dois lugares
 * dizendo a mesma coisa é um lugar para elas discordarem.
 */
module.exports = {
  domain: {
    models: "src/models",
    validations: "src/validations",
    triggers: "src/triggers",
    hooks: "src/hooks",
    mappings: "src/mappings",
    documents: "src/documents",
    pipelines: "src/pipelines",
    integrations: "src/integrations",
    routes: "src/routes",
  },
};
