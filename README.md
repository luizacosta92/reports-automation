# Reports Automation

Aplicação web para automatizar o processamento de planilhas de calibração e a emissão de pareceres de conformidade para a Schulz S.A.

O projeto utiliza uma API em Python com FastAPI e uma interface web para enviar planilhas Excel, processar pontos de ensaio e apresentar os resultados da análise metrológica.

## Objetivo do Projeto

Desenvolver uma aplicação web capaz de receber planilhas `.xlsx`, processar os pontos de ensaio e apresentar os resultados de calibração de maneira clara e organizada.

O sistema calcula a média das medições, o erro sistemático e compara o erro absoluto com o Limite de Erro Admissível (LEA), classificando os pontos conforme as regras implementadas no domínio.

## Funcionalidades Implementadas

- Upload de planilhas Excel (`.xlsx`).
- Leitura dos dados da planilha em memória.
- Identificação de parâmetros, valores nominais, tolerâncias e medições.
- Extração de metadados de cliente e técnico, quando disponíveis.
- Cálculo da média das leituras por ponto de ensaio.
- Cálculo do erro sistemático.
- Comparação do erro absoluto com o LEA.
- Classificação dos pontos dentro ou fora da tolerância.
- Geração de parecer final aprovado ou reprovado.
- Interface web para envio do arquivo e apresentação dos resultados.
- Endpoint de saúde para verificar se a API está funcionando.
- Testes automatizados para o domínio metrológico e a leitura de planilhas.

## Tecnologias Utilizadas

**Backend**
- Python 3.11 ou superior
- FastAPI
- OpenPyXL
- Pytest

**Frontend**
- React
- JavaScript
- Vite

## Arquitetura

O projeto utiliza uma arquitetura de monólito modular com API REST, separando as responsabilidades por camada.

```text
Frontend React
      |
      v
FastAPI / API REST
      |
      v
Caso de uso ProcessCalibration
      |
      v
Servico de dominio metrologico
      |
      v
Port MeasurementReader
      |
      v
XlsxMeasurementReader
```

### Organização das responsabilidades

- `app/api`: endpoints HTTP e validação da entrada.
- `app/application`: casos de uso e orquestração do processamento.
- `app/domain/models`: modelos e enumerações do domínio.
- `app/domain/ports`: contratos de acesso aos dados.
- `app/domain/services`: regras de negócio e cálculos metrológicos.
- `app/infrastructure`: implementação da leitura de arquivos XLSX.
- `frontend-calibra`: interface web.
- `tests`: testes automatizados.

Essa separação permite evoluir o sistema sem concentrar regras de negócio nas rotas HTTP ou na interface.

## Estrutura do Projeto

```text
reports-automation/
├── app/
│   ├── api/
│   ├── application/
│   ├── domain/
│   │   ├── models/
│   │   ├── ports/
│   │   └── services/
│   ├── infrastructure/
│   │   └── xlsx_reader.py
│   └── main.py
├── frontend-calibra/
├── tests/
│   ├── dados.xlsx
│   └── test_metrology.py
├── pyproject.toml
└── README.md
```

## Requisitos

- Python 3.11 ou superior.
- Node.js e npm.
- Navegador atualizado.
- Planilha Excel no formato `.xlsx`.

## Instalação e Execução

### 1. Backend

Abra o terminal na raiz do projeto.

Crie e configure o ambiente virtual, caso ainda não exista:

```powershell
python -m venv .venv
```

Instale as dependências:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Inicie a API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

A API estará disponível em:

- Saúde: http://127.0.0.1:8000/health
- Documentação interativa: http://127.0.0.1:8000/docs

O endpoint de saúde retorna:

```json
{
  "status": "ok"
}
```

### 2. Frontend

Abra outro terminal e acesse a pasta do frontend:

```powershell
cd frontend-calibra
npm ci
npm run dev
```

Por padrão, o frontend usa `http://127.0.0.1:8000`. Para apontar para uma API
publicada ou para outra instância local, defina `VITE_API_URL` antes de iniciar
o Vite ou de gerar o build:

```powershell
$env:VITE_API_URL = "https://sua-api.example.com"
npm run dev
```

No deploy com frontend e API na mesma origem, use uma URL vazia para que as
requisições sejam relativas:

```powershell
$env:VITE_API_URL = ""
npm run build
```

Abra no navegador o endereço informado pelo Vite, normalmente:

http://localhost:5173

Mantenha os dois terminais abertos enquanto utiliza a aplicação.

## API

### Processar calibração

**Endpoint:** `POST /api/v1/calibrations/process`

O endpoint recebe uma planilha pelo campo `file`, usando `multipart/form-data`.

Exemplo de chamada:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/calibrations/process -F "file=@tests/dados.xlsx"
```

A resposta de sucesso contém metadados, resultados por ponto e parecer final. Exemplo ilustrativo:

```json
{
  "metadata": {
    "cliente": "Schulz S.A.",
    "tecnico": "Maria"
  },
  "resultados": [
    {
      "parametro": "P1",
      "nominal": 10.0,
      "leituras": [10.1, 10.3],
      "media": 10.2,
      "erro_sistematico": 0.2,
      "lea": 0.2,
      "status": "DENTRO_DA_TOLERANCIA"
    }
  ],
  "parecer_final": "APROVADO"
}
```

Os valores acima são apenas um exemplo do formato de resposta.

### Classificações possíveis

**Status do ponto**
- `DENTRO_DA_TOLERANCIA`
- `FORA_DA_TOLERANCIA`

**Parecer final**
- `APROVADO`
- `REPROVADO`

O parecer final é aprovado quando todos os pontos atendem à regra de tolerância implementada no domínio.

## Formato da Planilha

O leitor reconhece os nomes de colunas previstos para o processamento, incluindo:

| Campo | Cabeçalhos aceitos |
|---|---|
| Parâmetro | `Parametro`, `Parâmetro`, `Caracteristica`, `DIMENSION` |
| Nominal | `Nominal`, `Valor Nominal` |
| Tolerância superior | `Tol +`, `+TOL` |
| Tolerância inferior | `Tol -`, `-TOL` |
| LEA | `LEA`, `Limite de Erro Admissivel` |
| Medições | `Medida`, `Medicao`, `Leitura`, `Valor Obtido`, `MEAS` |

O leitor procura a linha que contém o cabeçalho dos parâmetros, permitindo que existam linhas de metadados antes da tabela.

Quando a planilha possui uma aba chamada `Importação` ou `Importacao`, ela é selecionada automaticamente pelo leitor.

Para arquivos que utilizam tolerâncias superior e inferior sem uma coluna explícita de LEA, a implementação atual considera o maior valor absoluto entre as tolerâncias disponíveis.

A planilha utilizada nos testes automatizados está em `tests/dados.xlsx`.

## Cálculos Metrológicos

Para cada ponto de ensaio, o sistema calcula:

**Média das leituras**

A média aritmética das medições registradas para o ponto.

**Erro sistemático**

`Erro sistemático = Média − Valor nominal`

**Critério de tolerância**

O valor absoluto do erro sistemático é comparado com o LEA definido para o ponto.

O status resultante e o parecer final são determinados pelas regras implementadas no serviço de domínio metrológico.

## Testes Automatizados

O projeto possui testes automatizados para a API HTTP, a lógica metrológica e a
leitura de planilhas.

Para executar:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Os testes cobrem:

- Cálculo da média, erro sistemático, LEA e aprovação.
- Reprovação quando existe um ponto fora da tolerância.
- Leitura de XLSX com metadados e colunas de tolerância.
- Rejeição de conteúdo que não corresponde a um arquivo XLSX válido.
- Resposta do endpoint `/health`.
- Upload de planilhas aprovadas e reprovadas pela API.
- Rejeição de extensão inválida e ausência do campo `file`.

O caso que lê a planilha operacional `tests/dados.xlsx` depende desse arquivo
de teste estar presente no repositório. A validação da AV04 deve incluir a
revisão desse fixture antes do merge.

A execução dos testes unitários não substitui um teste E2E completo entre navegador, frontend, API e arquivo Excel.

## Tratamento de Erros e CORS

A API realiza validações para arquivos e estruturas de planilha não suportados. O tratamento de erros deve informar ao cliente quando o arquivo não pode ser processado.

O projeto também utiliza configuração de CORS para permitir a comunicação entre o frontend local e a API, conforme as origens configuradas no backend.

Em ambiente de produção, as origens permitidas devem ser ajustadas para os endereços efetivamente utilizados pela aplicação.

## Escopo Atual e Evoluções Futuras

A versão atual concentra-se no processamento de planilhas XLSX e na apresentação dos resultados de calibração.

Não fazem parte do escopo implementado nesta versão:

- Persistência em banco de dados.
- Histórico e auditoria de processamentos.
- Autenticação e controle de acesso.
- Geração de certificados em PDF.
- Desvio padrão e incerteza expandida.
- Implantação em nuvem com Docker.

Essas funcionalidades podem ser avaliadas conforme as necessidades futuras do produto e as decisões da equipe.

## Considerações Finais

O Reports Automation foi desenvolvido para simplificar o processamento de dados de calibração, centralizar os cálculos metrológicos e facilitar a visualização dos resultados.

A separação entre frontend, API, regras de domínio e infraestrutura favorece a manutenção, os testes e a evolução do sistema.

**Repositório:** adicionar o link do repositório remoto utilizado na entrega.

**Evidências visuais:** adicionar capturas de tela da interface e dos resultados obtidos com a planilha oficial, quando disponíveis.
