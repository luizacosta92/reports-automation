import { useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileSpreadsheet,
  Gauge,
  RotateCcw,
  ShieldCheck,
  UploadCloud,
  XCircle,
} from "lucide-react";

// Em producao (AWS) o build define VITE_API_URL; localmente usa a API em 127.0.0.1:8000.
const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "—";
  return new Intl.NumberFormat("pt-BR", {
    maximumFractionDigits: 4,
  }).format(value);
}

function getErrorMessage(response, body) {
  if (body && typeof body.detail === "string") return body.detail;
  if (response.status === 415) {
    return "Formato não suportado. Selecione um arquivo Excel .xlsx.";
  }
  if (response.status === 422) {
    return "Não foi possível ler a planilha. Confira as colunas e os valores obrigatórios.";
  }
  return "Não foi possível processar o arquivo. Verifique se a API está em execução e tente novamente.";
}

export default function App() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  function chooseFile(nextFile) {
    setError("");
    setResult(null);

    if (!nextFile) {
      setFile(null);
      return;
    }

    if (!nextFile.name.toLowerCase().endsWith(".xlsx")) {
      setFile(null);
      setError("Selecione um arquivo com extensão .xlsx.");
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setFile(nextFile);
  }

  async function processFile(event) {
    event.preventDefault();
    if (!file || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/api/v1/calibrations/process`,
        {
          method: "POST",
          body: formData,
        }
      );

      let body = {};
      try {
        body = await response.json();
      } catch {
        body = {};
      }

      if (!response.ok) {
        throw new Error(getErrorMessage(response, body));
      }

      if (!Array.isArray(body.resultados)) {
        throw new Error(
          "A API respondeu, mas o formato dos resultados não é o esperado."
        );
      }

      setResult(body);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? `Não foi possível conectar à API. Confirme se o back-end está rodando em ${API_URL || window.location.origin}.`
          : err.message || "Ocorreu um erro inesperado durante o processamento."
      );
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setError("");
    setResult(null);
    setDragging(false);
    if (inputRef.current) inputRef.current.value = "";
  }

  const approved = result?.parecer_final === "APROVADO";
  const rows = result?.resultados ?? [];
  const withinCount = rows.filter(
    (row) => row.status === "DENTRO_DA_TOLERANCIA"
  ).length;
  const outsideCount = rows.filter(
    (row) => row.status === "FORA_DA_TOLERANCIA"
  ).length;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <Gauge size={23} strokeWidth={2.2} />
          </div>
          <div>
            <div className="brand-name">
              CALIBRA<span>.</span>
            </div>
            <div className="brand-subtitle">ANÁLISE DE CALIBRAÇÃO</div>
          </div>
        </div>
        <div className="topbar-right">
          <span className="secure-dot" />
          <span>Ambiente de análise</span>
        </div>
      </header>

      <main className="main-content">
        <div className="breadcrumb">
          <span>Início</span>
          <ChevronRight size={14} />
          <strong>Processar calibração</strong>
        </div>

        <section className="page-intro">
          <div className="intro-copy">
            <div className="eyebrow">
              <Activity size={15} /> PROCESSAMENTO METROLÓGICO
            </div>
            <h1>Análise de calibração</h1>
            <p>
              Envie a planilha de medições para calcular os resultados e
              verificar a conformidade de cada ponto de ensaio.
            </p>
          </div>
          <div className="intro-illustration" aria-hidden="true">
            <div className="illustration-ring ring-one" />
            <div className="illustration-ring ring-two" />
            <div className="illustration-center">
              <Gauge size={38} />
            </div>
            <span className="orbit-dot dot-one" />
            <span className="orbit-dot dot-two" />
          </div>
        </section>

        <section className="workflow" aria-label="Etapas do processamento">
          <div className="workflow-step active">
            <span>1</span>
            <div>
              <strong>Enviar planilha</strong>
              <small>Arquivo Excel</small>
            </div>
          </div>
          <div className="workflow-line" />
          <div className={`workflow-step ${result ? "complete" : ""}`}>
            <span>
              {result ? <CheckCircle2 size={17} /> : "2"}
            </span>
            <div>
              <strong>Processar dados</strong>
              <small>Cálculos metrológicos</small>
            </div>
          </div>
          <div className="workflow-line" />
          <div className={`workflow-step ${result ? "complete" : ""}`}>
            <span>
              {result ? <CheckCircle2 size={17} /> : "3"}
            </span>
            <div>
              <strong>Ver resultados</strong>
              <small>Parecer final</small>
            </div>
          </div>
        </section>

        <section className="upload-card">
          <div className="section-heading">
            <div className="heading-icon">
              <FileSpreadsheet size={20} />
            </div>
            <div>
              <h2>Importar dados</h2>
              <p>
                Selecione a planilha operacional que contém as leituras e os
                valores de referência.
              </p>
            </div>
          </div>

          <form onSubmit={processFile}>
            <input
              ref={inputRef}
              className="visually-hidden"
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={(event) => chooseFile(event.target.files?.[0])}
            />

            <div
              className={`dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""
                }`}
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  inputRef.current?.click();
                }
              }}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                chooseFile(event.dataTransfer.files?.[0]);
              }}
            >
              <div className="upload-icon">
                {file ? (
                  <FileSpreadsheet size={27} />
                ) : (
                  <UploadCloud size={28} />
                )}
              </div>

              {file ? (
                <>
                  <strong className="selected-file">{file.name}</strong>
                  <span>
                    {(file.size / 1024).toLocaleString("pt-BR", {
                      maximumFractionDigits: 1,
                    })}{" "}
                    KB · Arquivo selecionado
                  </span>
                  <span className="change-file">
                    Clique para escolher outro arquivo
                  </span>
                </>
              ) : (
                <>
                  <strong>Arraste sua planilha até aqui</strong>
                  <span>
                    ou <em>clique para procurar no computador</em>
                  </span>
                  <span className="file-hint">Formato aceito: .xlsx</span>
                </>
              )}
            </div>

            {error && (
              <div className="error-message" role="alert">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div className="form-actions">
              <button
                className="button button-primary"
                type="submit"
                disabled={!file || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner" />
                    Processando...
                  </>
                ) : (
                  <>
                    <ClipboardCheck size={17} />
                    Processar planilha
                  </>
                )}
              </button>
              <button
                className="button button-ghost"
                type="button"
                onClick={reset}
                disabled={loading}
              >
                <RotateCcw size={16} />
                Limpar
              </button>
            </div>
          </form>
        </section>

        {result && (
          <section className="results-section">
            <div className="results-heading">
              <div>
                <div className="eyebrow">
                  <ShieldCheck size={15} /> RESULTADO DO PROCESSAMENTO
                </div>
                <h2>Resumo da análise</h2>
              </div>
              <div
                className={`verdict-pill ${approved ? "verdict-approved" : "verdict-rejected"
                  }`}
              >
                {approved ? (
                  <CheckCircle2 size={17} />
                ) : (
                  <XCircle size={17} />
                )}
                {result.parecer_final || "PARECER NÃO INFORMADO"}
              </div>
            </div>

            <div className="summary-grid">
              <article className="summary-card">
                <span className="summary-label">Pontos analisados</span>
                <strong>{rows.length}</strong>
                <small>Total de resultados retornados</small>
              </article>
              <article className="summary-card summary-good">
                <span className="summary-label">Dentro da tolerância</span>
                <strong>{withinCount}</strong>
                <small>Pontos conformes</small>
              </article>
              <article className="summary-card summary-bad">
                <span className="summary-label">Fora da tolerância</span>
                <strong>{outsideCount}</strong>
                <small>Pontos não conformes</small>
              </article>
            </div>

            {result.metadata && (
              <div className="metadata-card">
                <h3>Informações da calibração</h3>
                <div className="metadata-grid">
                  {Object.entries(result.metadata).map(([key, value]) => (
                    <div className="metadata-item" key={key}>
                      <span>{key.replaceAll("_", " ")}</span>
                      <strong>
                        {value === null || value === undefined
                          ? "—"
                          : typeof value === "object"
                            ? JSON.stringify(value)
                            : String(value)}
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="table-card">
              <div className="table-heading">
                <div>
                  <h3>Resultados por ponto de ensaio</h3>
                  <p>Valores calculados e situação de conformidade.</p>
                </div>
                <span className="table-count">{rows.length} pontos</span>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Ponto</th>
                      <th>Referência</th>
                      <th>Média</th>
                      <th>Erro sistemático</th>
                      <th>LEA</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>

                    {rows.map((row, index) => {
                      const isWithin =
                        row.status === "DENTRO_DA_TOLERANCIA";

                      return (
                        <tr key={`${row.parametro ?? "ponto"}-${index}`}>
                          <td>{row.parametro ?? index + 1}</td>
                          <td>{formatNumber(row.nominal)}</td>
                          <td>{formatNumber(row.media)}</td>
                          <td>{formatNumber(row.erro_sistematico)}</td>
                          <td>{formatNumber(row.lea)}</td>
                          <td>
                            <span
                              className={`status-badge ${isWithin ? "status-good" : "status-bad"
                                }`}
                            >
                              {isWithin ? (
                                <CheckCircle2 size={14} />
                              ) : (
                                <XCircle size={14} />
                              )}
                              {row.status || "STATUS NÃO INFORMADO"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        <footer className="page-footer">
        </footer>
      </main>
    </div>
  );
}
