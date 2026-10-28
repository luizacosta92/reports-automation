<#
  Publica a aplicacao Reports Automation na AWS.
  Rode a partir da RAIZ do repositorio:

    .\infra\deploy.ps1                          (AWS Academy Learner Lab: site no S3 + API Gateway, sem CloudFront)
    .\infra\deploy.ps1 -UseCloudFront           (conta AWS comum: site no S3 privado + CloudFront com HTTPS)
    .\infra\deploy.ps1 -Email seu@email.com     (conta comum: cria tambem o alerta de orcamento)

  Primeiro uso: leia infra\README.md (instalar AWS CLI e SAM CLI, credenciais).
#>
param(
  [string]$Email = "",              # opcional: so necessario para criar o alerta do AWS Budgets
  [switch]$UseCloudFront,           # padrao: desligado (o Learner Lab nao permite criar o OAC do CloudFront)
  [string]$StackName = "reports-automation",
  [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"
$Raiz = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz

function Passo($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Checar($codigo, $mensagem) { if ($codigo -ne 0) { throw $mensagem } }

Passo "Conferindo ferramentas e credenciais"
foreach ($cmd in "aws", "sam", "python", "npm") {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "'$cmd' nao encontrado. Veja infra\README.md (pre-requisitos)." }
}
aws sts get-caller-identity --region $Region | Out-Null
Checar $LASTEXITCODE "Credenciais AWS invalidas ou expiradas. No Learner Lab, copie as credenciais novas (AWS Details > AWS CLI > Show)."

# Uma stack que falhou na criacao fica em ROLLBACK_COMPLETE e nao pode ser atualizada: precisa ser apagada antes.
$Status = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].StackStatus" --output text 2>$null
if ($Status -eq "ROLLBACK_COMPLETE" -or $Status -eq "CREATE_FAILED") {
  Passo "Removendo a stack anterior que falhou ($Status)"
  aws cloudformation delete-stack --stack-name $StackName --region $Region
  aws cloudformation wait stack-delete-complete --stack-name $StackName --region $Region
  Checar $LASTEXITCODE "Nao foi possivel apagar a stack anterior. Apague-a no console do CloudFormation."
}

Passo "Copiando o codigo da API para o pacote da Lambda"
python infra\prepare.py
Checar $LASTEXITCODE "Falha ao preparar o codigo."

Passo "sam build (empacota a Lambda para Linux)"
sam build --template-file infra\template.yaml --build-dir infra\.aws-sam\build
Checar $LASTEXITCODE "sam build falhou."

Passo "sam deploy (cria/atualiza a infraestrutura)"
$Parametros = @("UseCloudFront=$($UseCloudFront.IsPresent.ToString().ToLower())", "CreateBudget=false")
if ($Email) { $Parametros = @("UseCloudFront=$($UseCloudFront.IsPresent.ToString().ToLower())", "CreateBudget=true", "AlertEmail=$Email") }
sam deploy --template-file infra\.aws-sam\build\template.yaml `
  --stack-name $StackName --region $Region `
  --capabilities CAPABILITY_IAM --resolve-s3 `
  --parameter-overrides $Parametros `
  --no-confirm-changeset --no-fail-on-empty-changeset
Checar $LASTEXITCODE "sam deploy falhou."

function Saida($chave) {
  aws cloudformation describe-stacks --stack-name $StackName --region $Region `
    --query "Stacks[0].Outputs[?OutputKey=='$chave'].OutputValue" --output text
}
$Bucket = Saida "FrontendBucketName"
$DistId = Saida "DistributionId"
$Url    = Saida "SiteUrl"
$ApiUrl = Saida "ApiDirectUrl"
$ViteApi = Saida "ApiUrlForFrontend"
if ($ViteApi -eq "None") { $ViteApi = "" }

Passo "Gerando o build do front-end"
Push-Location frontend-calibra
npm ci
Checar $LASTEXITCODE "npm ci falhou."
$env:VITE_API_URL = $ViteApi   # vazio com CloudFront (chama /api no mesmo dominio); URL da API Gateway sem CloudFront
npm run build
Checar $LASTEXITCODE "npm run build falhou."
Pop-Location

Passo "Enviando o front-end para o S3"
aws s3 sync frontend-calibra\dist "s3://$Bucket" --delete --region $Region
Checar $LASTEXITCODE "Falha no upload para o S3."
if ($DistId -and $DistId -ne "none" -and $DistId -ne "None") {
  aws cloudfront create-invalidation --distribution-id $DistId --paths "/*" | Out-Null
}

Passo "Teste rapido: /health da API"
$Teste = if ($UseCloudFront) { "$Url/health" } else { "$ApiUrl/health" }
try {
  $r = Invoke-RestMethod $Teste
  Write-Host "API respondeu: $($r | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
  Write-Host "Nao respondeu ainda. Tente abrir no navegador: $Teste" -ForegroundColor Yellow
}

Write-Host "`nPronto!" -ForegroundColor Green
Write-Host "Site: $Url"
Write-Host "API:  $ApiUrl"
if (-not $UseCloudFront) { Write-Host "(Sem CloudFront o site e HTTP; a API e HTTPS.)" }
if ($Email) { Write-Host "Confirme o e-mail de inscricao do AWS Budgets que chegou em $Email." }
