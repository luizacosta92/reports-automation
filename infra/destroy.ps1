<#
  Remove TUDO que o deploy criou (zera qualquer risco de custo).
  Use ao terminar a avaliacao:   .\infra\destroy.ps1
#>
param(
  [string]$StackName = "reports-automation",
  [string]$Region = "us-east-1"
)
$ErrorActionPreference = "Stop"

$Bucket = aws cloudformation describe-stacks --stack-name $StackName --region $Region `
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" --output text
if ($Bucket -and $Bucket -ne "None") {
  Write-Host "Esvaziando o bucket $Bucket (o CloudFormation nao apaga bucket com arquivos)..."
  aws s3 rm "s3://$Bucket" --recursive --region $Region
}
Write-Host "Apagando a stack $StackName..."
sam delete --stack-name $StackName --region $Region --no-prompts
Write-Host "Concluido. Confira no console se nao sobrou nada (CloudFormation, S3, CloudFront)."
