# Deploy na AWS (Free Tier) - Reports Automation

Esta pasta publica o projeto na AWS usando **AWS SAM** (Serverless Application Model): um arquivo
`template.yaml` descreve a infraestrutura e dois comandos (`sam build` e `sam deploy`) a criam.
Responsavel: Integrante 3 (infraestrutura e deploy).

## Usando o AWS Academy Learner Lab (nosso caso)

O grupo publica no **Learner Lab** (orcamento de US$ 50, servicos restritos). Diferencas em relacao a uma conta comum:

1. **Nao ha usuario IAM nem `aws configure` com chave fixa.** Clique em **Start Lab**, espere a bolinha "AWS" ficar verde,
   abra **AWS Details > AWS CLI: Show** e copie as tres linhas (`aws_access_key_id`, `aws_secret_access_key`,
   `aws_session_token`) para o arquivo `C:\Users\SEU_USUARIO\.aws\credentials`, assim:

   ```
   [default]
   aws_access_key_id=...
   aws_secret_access_key=...
   aws_session_token=...
   ```
   Regiao: `us-east-1`. As credenciais **expiram quando a sessao acaba (4 h)**: a cada nova sessao, copie de novo.
   Nunca envie essas linhas para ninguem nem para o GitHub.
2. **Sem CloudFront.** O Learner Lab nega `cloudfront:CreateOriginAccessControl` (testado no primeiro deploy: a stack fez rollback).
   Por isso o padrao do `deploy.ps1` e o **plano B**: site como *website* do S3 (HTTP, leitura publica so de `GetObject`) e API
   chamada direto no API Gateway (HTTPS), com CORS liberado para o endereco do site. O `-UseCloudFront` e para contas comuns.
3. **A Lambda usa a `LabRole`**, que ja existe na conta (o laboratorio nao permite criar funcoes IAM). Isso ja esta no template.
4. **O AWS Budgets fica desligado por padrao** (`CreateBudget=false`), porque o laboratorio costuma nao permitir. O controle de custo
   e o proprio medidor "Used $X of $50" do laboratorio. Rode o deploy **sem** `-Email`: `.\infra\deploy.ps1`.
5. Se algum servico for bloqueado, o `sam deploy` mostra o erro: me envie a mensagem para ajustar.
6. Em vez de destruir a conta ao final, use `.\infra\destroy.ps1` para apagar os recursos criados e preservar o saldo.

> Os passos sobre criar conta AWS, usuario IAM e `aws configure` mais abaixo valem para uma **conta comum**, nao para o Learner Lab.

## O que sobe na nuvem

```
Usuario --HTTPS--> CloudFront --+--> S3 (site React, bucket privado)
                                |
                                +--> /api/* e /health --> API Gateway (HTTP) --> Lambda (FastAPI + Mangum)
```

| Peca | Para que serve | Observacao |
|------|----------------|------------|
| S3 | Guarda o build do front-end | Bucket privado; so o CloudFront le (OAC) |
| CloudFront | Entrega o site com HTTPS e repassa `/api/*` para a API | Site e API ficam na **mesma origem**, entao nao ha problema de CORS |
| API Gateway (HTTP API) | Recebe a chamada e aciona a Lambda | Limite de 5 req/s para segurar abuso/custo |
| Lambda | Roda a API FastAPI do grupo, sem alterar o codigo dela | O **Mangum** traduz o evento do API Gateway para o formato que o FastAPI entende |
| CloudWatch Logs | Logs da Lambda | Retencao de 14 dias para nao acumular |
| AWS Budgets | Alerta por e-mail se aparecer custo | Veja "Controle de custos" |

> **Diferenca em relacao ao documento da AV2:** a AV2 previa 5 funcoes Lambda e DynamoDB. O codigo real do
> grupo (AV3) e uma unica API FastAPI sem banco de dados, entao o deploy publica essa API em **uma** Lambda.
> O pipeline em 5 estagios e a persistencia ficam como evolucao futura. O relatorio deve dizer isso.

## Pre-requisitos (uma vez so)

1. **Conta AWS** (nao use o usuario "root" no dia a dia).
2. **Usuario IAM para o deploy** (console AWS > IAM > Usuarios > Criar):
   - Crie um usuario so para isso, **sem acesso ao console**, e gere uma *access key* (tipo "CLI").
   - O SAM cria funcao Lambda, funcoes IAM, S3, CloudFront, API Gateway e Budgets. Para uma conta de estudo, o jeito
     mais simples e anexar a politica gerenciada `AdministratorAccess` a esse usuario e **desativar/apagar a chave
     quando terminar**. (Isso nao e "menor privilegio": em producao se restringiria as permissoes.)
   - Nunca coloque a chave no GitHub.
3. **AWS CLI v2**: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
4. **AWS SAM CLI**: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
5. **Python 3.11+** e **Node.js + npm** (o grupo ja usa).
6. Configurar o CLI com a chave do passo 2:

```powershell
aws configure
# AWS Access Key ID:     (a do usuario IAM)
# AWS Secret Access Key: (a do usuario IAM)
# Default region name:   us-east-1
# Default output format: json
aws sts get-caller-identity   # deve mostrar a sua conta
```

## Ajuste obrigatorio no front-end (combinar com quem cuida do front)

Hoje o `frontend-calibra/src/App.jsx` chama `http://127.0.0.1:8000` direto. Na nuvem a API fica no mesmo dominio
do site, em `/api`. Troque a URL fixa por uma variavel (o comportamento local nao muda):

```jsx
// topo do App.jsx
const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

// dentro de processFile():
const response = await fetch(`${API_URL}/api/v1/calibrations/process`, { method: "POST", body: formData });
```

O `deploy.ps1` faz o build com `VITE_API_URL` vazio, entao em producao a chamada vira `/api/v1/calibrations/process`.
Sem essa mudanca, o site publicado tentaria falar com o `127.0.0.1` do computador do usuario e daria erro.

## Publicar

Na raiz do repositorio (PowerShell):

```powershell
.\infra\deploy.ps1 -Email seu@email.com
```

O script: confere credenciais, copia a API (`prepare.py`), roda `sam build` e `sam deploy`, builda o front-end,
envia para o S3, limpa o cache do CloudFront e testa `/health`. No final mostra o endereco `https://xxxx.cloudfront.net`.
Chegara um e-mail da AWS para **confirmar a inscricao** no alerta de orcamento: confirme, senao o alerta nao chega.

Atualizar depois de mudar o codigo: rode o mesmo comando de novo.

## Como verificar que funcionou (evidencias para o relatorio e o video)

1. Abrir `https://xxxx.cloudfront.net/health` -> `{"status":"ok"}`.
2. Abrir o site, enviar a planilha de teste e ver o parecer APROVADO/REPROVADO.
3. Console AWS: CloudFormation (stack `CREATE_COMPLETE`), Lambda, S3, CloudFront e Budgets.
4. Console AWS > Billing > Free Tier: print do uso.

## Controle de custos (importante)

- A PoC usa volume minimo (centenas de requisicoes por mes). Cotas gratuitas que eu conheco (**confirme na pagina
  oficial "AWS Free Tier" e em Billing > Free Tier, porque as regras mudam e dependem da data de criacao da conta**):
  Lambda 1 milhao de requisicoes/mes (sempre gratis); CloudFront 1 TB de saida e 10 milhoes de requisicoes/mes
  (sempre gratis); API Gateway HTTP, S3 e CloudWatch Logs costumam ser gratis por 12 meses em contas antigas.
  Contas novas (criadas apos meados de 2025, pelo que sei) usam um plano com creditos em vez dessas cotas:
  **verifique qual e o seu caso** e anote no relatorio.
- O template cria um **AWS Budget** com alertas por e-mail: gasto real acima de US$ 0,10, acima de 80% do limite
  (US$ 1) e previsao acima de 100%. O Budgets avisa, **nao bloqueia** cobranca.
- Cuidados embutidos: limite de 5 req/s no API Gateway, logs com retencao de 14 dias, bucket privado.
- **Ao terminar a avaliacao, rode `.\infra\destroy.ps1`** para apagar tudo, e desative a chave de acesso do usuario IAM.

## Limitacoes conhecidas

- **Sem CloudFront o site e HTTP** (sem criptografia entre navegador e S3); a API continua em HTTPS. A AV2 previa HTTPS
  para tudo: no relatorio, registre que o Learner Lab nao permite CloudFront e que a versao com HTTPS esta no template (`-UseCloudFront`).
- **Sem autenticacao:** qualquer pessoa com o link envia planilhas (a AV2 previa IAM/Cognito; nao implementado).
- **Tamanho do arquivo:** a Lambda aceita no maximo ~6 MB por requisicao; com a codificacao base64 isso limita a
  planilha a aproximadamente 4 MB.
- **Primeira chamada mais lenta** (cold start de poucos segundos) depois de um tempo parada.
- **Nao testei o deploy de verdade:** nao tenho acesso a sua conta AWS. O `template.yaml` passou no `cfn-lint`
  (validador), mas o primeiro `sam deploy` pode revelar ajustes. Se algo falhar, copie a mensagem de erro.
- O dominio e o `*.cloudfront.net` padrao (certificado padrao da AWS); dominio proprio ficou fora do escopo.

## Arquivos

| Arquivo | Funcao |
|---------|--------|
| `template.yaml` | Toda a infraestrutura (SAM/CloudFormation) |
| `api_src/lambda_handler.py` | Adaptador Mangum: liga o FastAPI ao Lambda |
| `api_src/requirements.txt` | Dependencias da Lambda (sem uvicorn) |
| `prepare.py` | Copia `app/` para dentro do pacote da Lambda |
| `deploy.ps1` / `destroy.ps1` | Publica / remove tudo |
