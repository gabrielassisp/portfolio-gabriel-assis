'use strict';
const cases = {
  brazil: {
    kicker: 'PROJETO PÚBLICO · BIGQUERY + DBT',
    title: 'Pipeline de indicadores econômicos do Brasil',
    intro: 'Pipeline batch com três fontes públicas (IBGE, Banco Central e World Bank), carga no BigQuery e transformações com dbt, executado de verdade e com as evidências versionadas no repositório.',
    metrics: [['75', 'observações reais por execução'], ['16', 'testes dbt aprovados'], ['61', 'testes Python']],
    sections: [
      ['O problema', 'Indicadores econômicos vêm de APIs com formatos, frequências e regras de revisão diferentes. O objetivo era reuni-los numa base confiável, sem dados sintéticos escondidos e sem custo descontrolado.'],
      ['O que eu fiz', ['Extração estrita das três APIs, com validação de cobertura, unicidade e valores finitos antes da carga.', 'Carga em lote no BigQuery, em tabela bronze particionada e com clustering.', 'Modelos dbt em camadas (staging, intermediate, marts) e testes de qualidade.', 'Execução diária no GitHub Actions com autenticação OIDC (sem chave de service account) e limite de bytes por consulta.']],
      ['Evidências', 'Execução real em 29/10/2026 e execução automática por push em 02/11/2026, ambas com 75 registros e 16 testes dbt aprovados. Os JSON das execuções estão na pasta evidence do repositório.'],
      ['O que aprendi', 'Separar o modo de teste (fixture) do modo real evita que dados falsos cheguem à base sem ninguém perceber, e travas de custo precisam existir desde o primeiro dia.']
    ],
    path: 'APIs públicas → validação → NDJSON → BigQuery (bronze) → dbt (silver/gold) → consulta com limite de bytes',
    links: [{ label: 'Ver código no GitHub', url: 'https://github.com/gabrielassisp/Brazil-Pipeline-Project' }]
  },
  transparencia: {
    kicker: 'PROJETO PÚBLICO · EM CONSTRUÇÃO',
    title: 'Pipeline de dados do Portal da Transparência',
    intro: 'Pipeline com dados públicos do governo federal. A arquitetura segue a plataforma de dados que construí no trabalho com Airflow, dbt e PostgreSQL, reescrita do zero com uma API pública e levada para o GCP.',
    metrics: [['12', 'testes automatizados'], ['3 camadas', 'bronze, silver e gold'], ['700 req/min', 'limite respeitado pela ingestão']],
    sections: [
      ['O problema', 'A API do Portal da Transparência pagina os resultados e limita as requisições: 700 por minuto entre 00h e 06h, 400 no resto do dia e 180 nos endpoints restritos. Uma ingestão ingênua estoura o limite, perde páginas ou duplica dados quando é reprocessada.'],
      ['Como funciona', 'Um cliente em Python percorre as páginas, espaça as chamadas e repete as que falham por 429 ou 5xx. Cada execução grava o JSON bruto em Parquet numa partição ano/mês no GCS. No BigQuery, o dbt tipa os dados (silver) e monta o modelo estrela (gold). O Airflow orquestra tudo e o Terraform cria a infraestrutura.'],
      ['Decisões de engenharia', ['Ingestão idempotente: reprocessar um mês sobrescreve só aquela partição.', 'A mesma DAG faz a carga mensal e o histórico (catchup).', 'A bronze guarda o JSON bruto, então mudanças na API não quebram a ingestão.', 'Modelos incrementais com merge, particionados por mês e clusterizados por município.', 'Trava de custo de 5 GB por consulta no perfil do dbt.']],
      ['Status', 'Prontos: cliente da API, ingestão, testes, DAG, Terraform e os primeiros modelos dbt (Bolsa Família por município). Próximas etapas: carga histórica de 2 a 3 anos, despesas com SCD tipo 2, comparação de custo com e sem particionamento e o dashboard final.']
    ],
    path: 'API / arquivos mensais → Python → GCS (bronze) → BigQuery + dbt (silver, gold) → dashboard',
    note: 'Dados públicos da CGU, acessados com chave gratuita. O código está aberto no GitHub.',
    links: [{ label: 'Ver código no GitHub', url: 'https://github.com/gabrielassisp/portfolio-gabriel-assis/tree/main/projetos/transparencia-data-pipeline' }]
  },
  lakehouse: {
    kicker: 'LABORATÓRIO CLOUD · VALIDADO EM NOVEMBRO DE 2026',
    title: 'Correções, exclusões e replay em um lakehouse',
    intro: 'Laboratório de processamento de vendas que mantém os indicadores corretos quando eventos são corrigidos ou chegam fora de ordem. Usa oito eventos fictícios.',
    metrics: [['38', 'testes automatizados'], ['8 eventos', 'dados fictícios'], ['R$ 250,00', 'receita final conferida']],
    sections: [
      ['O problema', 'Uma venda pode ser corrigida ou excluída depois da primeira carga. Reinserir tudo duplica a receita, e aplicar um evento antigo desfaz a correção. A pipeline precisa saber qual estado vale.'],
      ['Arquitetura', 'Os eventos foram carregados no BigQuery Sandbox, exportados em JSON e copiados manualmente para um Volume no Databricks Free Edition. PySpark e Delta Lake processam as camadas bronze, silver e gold.'],
      ['Decisões de engenharia', ['A silver tem uma linha por venda e só aceita versões mais novas.', 'Exclusões viram tombstones, então um evento antigo não ressuscita a venda.', 'Valores monetários são guardados em centavos inteiros.', 'Eventos inválidos vão para quarentena e bloqueiam a atualização da silver.', 'A gold é uma view das vendas ativas.']],
      ['O que foi verificado', 'A receita foi de R$ 350,00 para R$ 250,00 depois de uma correção, uma exclusão e uma inclusão, e continuou em R$ 250,00 com eventos atrasados e com o replay. Um lote inválido não alterou a silver. O job no Databricks terminou com sucesso em 2min56s.'],
      ['Testes', 'O GitHub Actions roda os 38 testes, o build do pacote e a demonstração com replay em Python 3.11 e 3.13. A execução em PySpark foi validada à parte, no workspace.'],
      ['Limitações', 'A cópia do GCP para o Databricks é manual, e a bronze é relida inteira a cada execução, sem checkpoint incremental. Os dados são sintéticos e não há teste de escala. Os próximos passos são automatizar a transferência e guardar métricas de execução.']
    ],
    path: 'BigQuery Sandbox → exportação JSON → Volume → Bronze → Silver → Gold',
    note: 'O GCP rodou sem faturamento ativo. O repositório ainda é privado; a cópia revisada para download tem o mesmo código.',
    links: [{ label: 'Baixar cópia revisada do lakehouse', url: 'downloads/lakehouse-revisado.zip' }, { label: 'Repositório no GitHub (privado)', url: 'https://github.com/gabrielassisp/lakehouse-vendas-gcp-databricks' }]
  },
  sql: {
    kicker: 'EXPERIÊNCIA PROFISSIONAL · SQL E REGRAS DE NEGÓCIO',
    title: 'Classificação de vendas e reconexões',
    intro: 'A consulta de vendas já existia. Eu reescrevi a parte que classifica os eventos para aplicar as regras de negócio com mais precisão.',
    sections: [
      ['O problema', 'Para saber se um cliente marcado como reconexão era mesmo uma reconexão, alguém precisava abrir o histórico e conferir à mão. A classificação tinha que considerar o tempo entre os eventos e os registros do serviço.'],
      ['O que eu fiz', 'Passei a classificar cada evento a partir do histórico do cliente e do serviço, com regras temporais definidas pelo negócio.'],
      ['Recursos usados', ['CTEs para separar as etapas da consulta.', 'Joins e subconsultas sobre os históricos.', 'LAG e ROW_NUMBER para comparar e selecionar eventos.', 'CASE, COALESCE e regras de tempo para a classificação.']],
      ['Validação', 'Testei a consulta com os usuários do indicador e conferi os resultados contra o histórico dos clientes. Não medi ganho percentual de precisão.'],
      ['O que aprendi', 'Granularidade, exceções e critérios de tempo precisam estar combinados com quem usa o indicador antes de escrever a consulta.']
    ],
    path: 'Histórico de clientes / serviços → regras SQL → classificação para indicadores',
    note: 'O código e os dados são da empresa e não estão publicados.'
  }
};
const dialog = document.querySelector('#case-dialog');
const content = document.querySelector('#case-content');
let previousFocus = null;
function element(tag, text, className) { const item = document.createElement(tag); if (text) item.textContent = text; if (className) item.className = className; return item; }
function openCase(key) {
  const data = cases[key]; if (!data) return;
  previousFocus = document.activeElement;
  content.replaceChildren(element('p', data.kicker, 'case-kicker'));
  const title = element('h2', data.title, 'case-title'); title.id = 'case-title'; content.append(title, element('p', data.intro, 'case-intro'));
  if (data.metrics) { const metrics = element('div', '', 'case-metrics'); data.metrics.forEach(([value, label]) => { const metric = element('div'); metric.append(element('strong', value), element('span', label)); metrics.append(metric); }); content.append(metrics); }
  content.append(element('p', data.path, 'case-path'));
  if (key === 'lakehouse') {
    const evidence = element('a', 'Consultar arquitetura e evidências técnicas', 'button outline');
    evidence.href = 'evidencias/index.html#lakehouse'; content.append(evidence);
  }
  data.sections.forEach(([heading, text]) => { const section = element('section', '', 'case-section'); section.append(element('h3', heading)); if (Array.isArray(text)) { const list = element('ul'); text.forEach(line => list.append(element('li', line))); section.append(list); } else section.append(element('p', text)); content.append(section); });
  content.append(element('p', data.note, 'case-note'));
  if (data.links) { const links = element('div', '', 'case-links'); data.links.forEach(item => { const link = element('a', item.label, 'button outline'); link.href = item.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; links.append(link); }); content.append(links); }
  dialog.showModal(); document.body.classList.add('modal-open'); dialog.scrollTop = 0;
}
document.querySelectorAll('[data-case]').forEach(button => button.addEventListener('click', () => openCase(button.dataset.case)));
document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
dialog.addEventListener('close', () => { document.body.classList.remove('modal-open'); previousFocus?.focus(); });
document.querySelector('#copy-email').addEventListener('click', async () => {
  const status = document.querySelector('#copy-status');
  try { await navigator.clipboard.writeText('gabriel.pereiramoc1@gmail.com'); status.textContent = 'E-mail copiado.'; }
  catch { status.textContent = 'Use o link de e-mail acima para abrir seu aplicativo de mensagens.'; }
});

const form = document.querySelector('#contact-form');
function contactMessage() {
 const values = new FormData(form);
 return {subject: String(values.get('subject')).trim(), body: 'Nome: '+values.get('name')+'\nE-mail: '+values.get('email')+'\n\n'+values.get('message')};
}
form.addEventListener('submit', event => {
 event.preventDefault();
 if (!form.reportValidity()) return;
 const message = contactMessage();
 window.location.href = 'mailto:gabriel.pereiramoc1@gmail.com?subject='+encodeURIComponent(message.subject)+'&body='+encodeURIComponent(message.body);
 document.querySelector('#form-status').textContent = 'Continue no seu aplicativo de e-mail para concluir o envio. Se ele não abrir, copie a mensagem e envie para o endereço ao lado.';
});
document.querySelector('#copy-message').addEventListener('click', async () => {
 if (!form.reportValidity()) return;
 const message = contactMessage();
 try { await navigator.clipboard.writeText('Assunto: '+message.subject+'\n\n'+message.body); document.querySelector('#form-status').textContent = 'Mensagem copiada. Cole no seu e-mail para enviar.'; }
 catch { document.querySelector('#form-status').textContent = 'Não foi possível copiar automaticamente. Selecione o texto e envie pelo e-mail ao lado.'; }
});

const sectionLinks = [...document.querySelectorAll('.nav-links a')];
const sectionObserver = new IntersectionObserver(entries => {
 for (const entry of entries) {
  if (!entry.isIntersecting) continue;
  for (const link of sectionLinks) {
   if (link.hash === '#'+entry.target.id) link.setAttribute('aria-current','location');
   else link.removeAttribute('aria-current');
  }
 }
}, {rootMargin:'-18% 0px -55% 0px',threshold:0});
document.querySelectorAll('main > section[id]').forEach(section=>sectionObserver.observe(section));
