import { useState, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileSpreadsheet, CheckCircle, AlertTriangle, Loader2, X } from "lucide-react";
import { toast } from "sonner";

export default function PontoImportarTab({ onImportSuccess }) {
  const [arquivo, setArquivo] = useState(null);
  const [importando, setImportando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const inputRef = useRef(null);

  const handleArquivoSelect = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().match(/\.(xls|xlsx)$/)) {
      toast.error("Envie um arquivo Excel (.xls ou .xlsx)");
      return;
    }
    setArquivo(f);
    setResultado(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().match(/\.(xls|xlsx)$/)) {
      toast.error("Envie um arquivo Excel (.xls ou .xlsx)");
      return;
    }
    setArquivo(f);
    setResultado(null);
  };

  const handleImportar = async () => {
    if (!arquivo) {
      toast.error("Selecione um arquivo primeiro");
      return;
    }
    setImportando(true);
    setResultado(null);
    try {
      const fd = new FormData();
      fd.append("file", arquivo);
      const { data } = await axios.post(`${API}/rh/ponto/importar-planilha`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResultado(data);
      toast.success(data.message);
      if (data.aviso_nao_cadastrados) {
        toast.warning(data.aviso_nao_cadastrados, { duration: 12000 });
      }
      if (onImportSuccess) onImportSuccess(data);
    } catch (err) {
      const msg = err.response?.data?.detail || "Erro ao importar planilha";
      toast.error(msg, { duration: 10000 });
      setResultado({ erro: msg });
    } finally {
      setImportando(false);
    }
  };

  const limparArquivo = () => {
    setArquivo(null);
    setResultado(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="space-y-6" data-testid="ponto-importar-tab">
      <Card className="border-2 border-dashed border-emerald-300 bg-emerald-50/30">
        <CardContent className="p-8">
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="text-center cursor-pointer"
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".xls,.xlsx"
              onChange={handleArquivoSelect}
              className="hidden"
              data-testid="input-arquivo-ponto"
            />
            {!arquivo ? (
              <>
                <div className="w-16 h-16 mx-auto rounded-full bg-emerald-100 flex items-center justify-center mb-4">
                  <Upload className="text-emerald-600" size={32} />
                </div>
                <h3 className="text-lg font-bold text-gray-800 mb-2">
                  Solte o arquivo aqui ou clique para selecionar
                </h3>
                <p className="text-sm text-gray-500">
                  Formatos aceitos: .xls / .xlsx (Registro de presença gerado pelo relógio de ponto)
                </p>
              </>
            ) : (
              <div className="flex items-center justify-center gap-3">
                <FileSpreadsheet className="text-emerald-600" size={32} />
                <div className="text-left">
                  <p className="font-semibold text-gray-800">{arquivo.name}</p>
                  <p className="text-xs text-gray-500">{(arquivo.size / 1024).toFixed(1)} KB</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    limparArquivo();
                  }}
                >
                  <X size={16} />
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {arquivo && !resultado && (
        <div className="flex justify-end">
          <Button
            onClick={handleImportar}
            disabled={importando}
            className="bg-emerald-600 hover:bg-emerald-700"
            data-testid="btn-confirmar-importar-ponto"
          >
            {importando ? (
              <>
                <Loader2 className="animate-spin mr-2" size={16} />
                Importando...
              </>
            ) : (
              <>
                <Upload className="mr-2" size={16} />
                Confirmar Importação
              </>
            )}
          </Button>
        </div>
      )}

      {resultado && !resultado.erro && (
        <Card className="border-emerald-200 bg-emerald-50">
          <CardContent className="p-6">
            <div className="flex items-start gap-3 mb-4">
              <CheckCircle className="text-emerald-600 mt-1" size={24} />
              <div>
                <h3 className="font-bold text-emerald-800 text-lg">Importação concluída</h3>
                <p className="text-sm text-emerald-700">
                  Período: <strong>{resultado.periodo?.inicio} a {resultado.periodo?.fim}</strong>
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="bg-white rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-emerald-600">{resultado.total_funcionarios}</p>
                <p className="text-xs text-gray-500">Funcionários</p>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-blue-600">{resultado.total_registros}</p>
                <p className="text-xs text-gray-500">Registros importados</p>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-amber-600">
                  {resultado.funcionarios_nao_cadastrados?.length || 0}
                </p>
                <p className="text-xs text-gray-500">Não cadastrados</p>
              </div>
            </div>

            {resultado.funcionarios_nao_cadastrados?.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="text-amber-600 mt-0.5 flex-shrink-0" size={18} />
                  <div className="text-sm">
                    <p className="font-semibold text-amber-800 mb-1">
                      Funcionários não cadastrados na plataforma:
                    </p>
                    <ul className="list-disc list-inside text-amber-700 space-y-0.5">
                      {resultado.funcionarios_nao_cadastrados.map((f, i) => (
                        <li key={i}>
                          <strong>{f.nome}</strong>
                          {f.departamento_planilha && ` — ${f.departamento_planilha}`}
                          {f.id_usuario_planilha && ` (ID ${f.id_usuario_planilha})`}
                        </li>
                      ))}
                    </ul>
                    <p className="text-xs text-amber-600 mt-2">
                      Os registros de ponto foram salvos. Cadastre estes funcionários em "Funcionários" para que apareçam vinculados.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="text-xs text-gray-500 mt-3">
              <details>
                <summary className="cursor-pointer font-medium">Ver lista completa de funcionários processados</summary>
                <ul className="mt-2 space-y-1">
                  {resultado.funcionarios_processados?.map((f, i) => (
                    <li key={i} className="flex justify-between">
                      <span>
                        {f.cadastrado ? "✅" : "⚠️"} {f.nome} ({f.departamento})
                      </span>
                      <span>{f.dias_com_registro} dias</span>
                    </li>
                  ))}
                </ul>
              </details>
            </div>
          </CardContent>
        </Card>
      )}

      {resultado?.erro && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="text-red-600 mt-1" size={20} />
            <div>
              <h3 className="font-bold text-red-800">Erro na importação</h3>
              <p className="text-sm text-red-700">{resultado.erro}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-4 text-sm text-gray-600">
          <h4 className="font-semibold text-gray-800 mb-2">📋 Como usar</h4>
          <ol className="list-decimal list-inside space-y-1">
            <li>Exporte o relatório de presença mensal do seu relógio de ponto (formato .xls/.xlsx).</li>
            <li>A planilha deve conter o cabeçalho "Data de presença:DD/MM/AAAA~DD/MM/AAAA" e blocos por funcionário.</li>
            <li>Suba o arquivo aqui — registros do mesmo mês serão sobrescritos.</li>
            <li>Acesse a aba <strong>Quadro Mensal</strong> para ver as horas, saldo e banco de horas de cada funcionário.</li>
          </ol>
          <p className="mt-2 text-xs">
            <strong>Jornada padrão considerada:</strong> Seg-Sex 8h/dia • Sábado 4h (08:00–12:00) • Domingo descanso.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
