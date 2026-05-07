import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { 
  Calendar, Users, Plus, Edit, Trash2, AlertTriangle, 
  Sun, ChevronLeft, ChevronRight, Search
} from "lucide-react";
import { toast } from "sonner";

export default function FeriasPage() {
  const [funcionarios, setFuncionarios] = useState([]);
  const [ferias, setFerias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAno, setSelectedAno] = useState(new Date().getFullYear());
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFerias, setEditingFerias] = useState(null);
  const [alertas, setAlertas] = useState([]);
  
  const [formData, setFormData] = useState({
    funcionario_id: "",
    data_inicio: "",
    data_fim: "",
    dias_vendidos: 0,
    observacoes: ""
  });

  useEffect(() => {
    fetchFuncionarios();
    fetchFerias();
    fetchAlertas();
  }, [selectedAno]);

  const fetchFuncionarios = async () => {
    try {
      const response = await axios.get(`${API}/rh/funcionarios`);
      setFuncionarios(response.data);
    } catch (error) {
      console.error("Erro ao carregar funcionários:", error);
    }
  };

  const fetchFerias = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/rh/ferias?ano=${selectedAno}`);
      setFerias(response.data);
    } catch (error) {
      toast.error("Erro ao carregar férias");
    } finally {
      setLoading(false);
    }
  };

  const fetchAlertas = async () => {
    try {
      const response = await axios.get(`${API}/rh/ferias/alertas`);
      setAlertas(response.data);
    } catch (error) {
      console.error("Erro ao carregar alertas:", error);
    }
  };

  const handleDispensarAlerta = async (funcionarioId, nome) => {
    if (!window.confirm(`Dispensar o alerta de ${nome}? Você pode reativá-lo depois pelo botão "Mostrar dispensados".`)) return;
    try {
      await axios.post(`${API}/rh/ferias/alertas/dispensar/${funcionarioId}`);
      toast.success("Alerta dispensado");
      fetchAlertas();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao dispensar alerta");
    }
  };

  const handleDispensarTodos = async () => {
    if (alertas.length === 0) return;
    if (!window.confirm(`Dispensar todos os ${alertas.length} alertas de período aquisitivo?`)) return;
    try {
      await axios.post(`${API}/rh/ferias/alertas/dispensar-todos`);
      toast.success(`${alertas.length} alerta(s) dispensado(s)`);
      fetchAlertas();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao dispensar alertas");
    }
  };

  const handleReativarDispensados = async () => {
    try {
      await axios.delete(`${API}/rh/ferias/alertas/dispensar-todos`);
      toast.success("Alertas dispensados foram reativados");
      fetchAlertas();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao reativar alertas");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingFerias) {
        await axios.put(`${API}/rh/ferias/${editingFerias.id}`, formData);
        toast.success("Férias atualizadas!");
      } else {
        await axios.post(`${API}/rh/ferias`, formData);
        toast.success("Férias agendadas!");
      }
      fetchFerias();
      fetchAlertas();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Deseja excluir estas férias?")) return;
    try {
      await axios.delete(`${API}/rh/ferias/${id}`);
      toast.success("Férias excluídas!");
      fetchFerias();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const handleZerarTodos = async () => {
    const confirmText = "ZERAR FERIAS";
    const input = window.prompt(
      `⚠️ ATENÇÃO: esta ação exclui TODOS os ${ferias.length} registros de férias e é IRREVERSÍVEL.\n\n` +
      `Para confirmar, digite exatamente: ${confirmText}`
    );
    if (input === null) return;
    if (input.trim().toUpperCase() !== confirmText) {
      toast.error("Texto de confirmação não confere. Operação cancelada.");
      return;
    }
    try {
      const r = await axios.delete(`${API}/rh/ferias?confirmar=true`);
      toast.success(r.data.message || "Todos os registros foram excluídos");
      fetchFerias();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao excluir todos os registros");
    }
  };

  const openModal = (ferias = null) => {
    if (ferias) {
      setEditingFerias(ferias);
      setFormData({
        funcionario_id: ferias.funcionario_id,
        data_inicio: ferias.data_inicio,
        data_fim: ferias.data_fim,
        dias_vendidos: ferias.dias_vendidos || 0,
        observacoes: ferias.observacoes || ""
      });
    } else {
      setEditingFerias(null);
      setFormData({
        funcionario_id: "",
        data_inicio: "",
        data_fim: "",
        dias_vendidos: 0,
        observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingFerias(null);
  };

  const getFuncionarioNome = (id) => {
    const func = funcionarios.find(f => f.id === id);
    return func?.nome || "-";
  };

  const calcularDiasFerias = () => {
    if (!formData.data_inicio || !formData.data_fim) return 0;
    const inicio = new Date(formData.data_inicio);
    const fim = new Date(formData.data_fim);
    const diff = Math.ceil((fim - inicio) / (1000 * 60 * 60 * 24)) + 1;
    return diff;
  };

  // Gera calendário do ano
  const gerarCalendario = () => {
    const meses = [];
    for (let mes = 0; mes < 12; mes++) {
      const primeiroDia = new Date(selectedAno, mes, 1);
      const ultimoDia = new Date(selectedAno, mes + 1, 0);
      const dias = [];
      
      // Dias vazios no início
      for (let i = 0; i < primeiroDia.getDay(); i++) {
        dias.push(null);
      }
      
      // Dias do mês
      for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
        const data = new Date(selectedAno, mes, dia);
        const dataStr = data.toISOString().split('T')[0];
        
        // Verifica se há férias neste dia
        const feriasNoDia = ferias.filter(f => {
          const inicio = new Date(f.data_inicio);
          const fim = new Date(f.data_fim);
          return data >= inicio && data <= fim;
        });
        
        dias.push({
          dia,
          data: dataStr,
          ferias: feriasNoDia
        });
      }
      
      meses.push({
        nome: new Date(selectedAno, mes, 1).toLocaleDateString('pt-BR', { month: 'long' }),
        dias
      });
    }
    return meses;
  };

  const calendario = gerarCalendario();

  const mesesNomes = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
  ];

  if (loading && funcionarios.length === 0) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;
  }

  return (
    <div data-testid="ferias-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Férias e Escalas</h1>
          <p className="text-gray-500 mt-1">Calendário de férias dos funcionários</p>
        </div>
        <div className="flex items-center gap-2">
          {ferias.length > 0 && (
            <Button
              variant="outline"
              onClick={handleZerarTodos}
              className="border-red-300 text-red-600 hover:bg-red-50"
              data-testid="btn-zerar-ferias"
              title="Excluir TODOS os registros de férias"
            >
              <Trash2 size={16} className="mr-2" />
              Zerar tudo
            </Button>
          )}
          <Button onClick={() => openModal()} className="bg-[#10B981] hover:bg-[#059669]">
            <Plus size={18} className="mr-2" />Agendar Férias
          </Button>
        </div>
      </div>

      {/* Seletor de Ano */}
      <div className="flex items-center justify-center gap-4 mb-6">
        <Button variant="outline" size="sm" onClick={() => setSelectedAno(selectedAno - 1)}>
          <ChevronLeft size={18} />
        </Button>
        <h2 className="text-2xl font-bold">{selectedAno}</h2>
        <Button variant="outline" size="sm" onClick={() => setSelectedAno(selectedAno + 1)}>
          <ChevronRight size={18} />
        </Button>
      </div>

      {/* Alertas de Férias */}
      {alertas.length > 0 && (
        <Card className="mb-6 border-orange-200 bg-orange-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <h3 className="font-semibold flex items-center gap-2 text-orange-600">
                <AlertTriangle size={18} />
                Alertas de Período Aquisitivo
                <span className="px-2 py-0.5 bg-orange-200 text-orange-900 rounded-full text-xs font-bold">
                  {alertas.length}
                </span>
              </h3>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="text-orange-700 border-orange-300 hover:bg-orange-100"
                  onClick={handleReativarDispensados}
                  title="Reativar todos os alertas que foram dispensados"
                  data-testid="btn-reativar-dispensados"
                >
                  Mostrar dispensados
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-red-600 border-red-300 hover:bg-red-50"
                  onClick={handleDispensarTodos}
                  title="Dispensar todos os alertas"
                  data-testid="btn-dispensar-todos"
                >
                  <Trash2 size={14} className="mr-1" />
                  Dispensar todos
                </Button>
              </div>
            </div>
            <div className="space-y-2">
              {alertas.map((alerta, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-white rounded-lg border border-orange-200">
                  <div>
                    <p className="font-medium">{alerta.funcionario_nome}</p>
                    <p className="text-sm text-gray-500">{alerta.mensagem}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setFormData({ ...formData, funcionario_id: alerta.funcionario_id });
                        setIsModalOpen(true);
                      }}
                      data-testid={`btn-agendar-alerta-${alerta.funcionario_id}`}
                    >
                      Agendar
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-gray-500 hover:text-red-600 hover:bg-red-50"
                      onClick={() => handleDispensarAlerta(alerta.funcionario_id, alerta.funcionario_nome)}
                      title="Dispensar este alerta"
                      data-testid={`btn-dispensar-alerta-${alerta.funcionario_id}`}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Legenda */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              <span>Férias Programadas</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span>Em Férias Hoje</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-200 rounded"></div>
              <span>Dia Normal</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Calendário Anual */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-6">
        {calendario.map((mes, mesIdx) => (
          <Card key={mesIdx}>
            <CardContent className="p-3">
              <h4 className="font-semibold text-center mb-2 capitalize">{mes.nome}</h4>
              <div className="grid grid-cols-7 gap-1 text-xs">
                {['D', 'S', 'T', 'Q', 'Q', 'S', 'S'].map((d, i) => (
                  <div key={i} className="text-center font-medium text-gray-500 py-1">{d}</div>
                ))}
                {mes.dias.map((diaObj, diaIdx) => (
                  <div
                    key={diaIdx}
                    className={`text-center py-1 rounded cursor-pointer text-xs
                      ${!diaObj ? '' : 
                        diaObj.ferias.length > 0 
                          ? 'bg-blue-500 text-white hover:bg-blue-600' 
                          : 'hover:bg-gray-100'
                      }`}
                    title={diaObj?.ferias.map(f => getFuncionarioNome(f.funcionario_id)).join(', ') || ''}
                  >
                    {diaObj?.dia || ''}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Lista de Férias Programadas */}
      <Card>
        <CardContent className="p-4">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Sun size={18} className="text-[#10B981]" />
            Férias Programadas em {selectedAno}
          </h3>
          
          {ferias.length === 0 ? (
            <p className="text-center text-gray-400 py-8">Nenhuma férias programada para este ano</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left p-3 text-sm font-medium text-gray-600">Funcionário</th>
                    <th className="text-center p-3 text-sm font-medium text-gray-600">Início</th>
                    <th className="text-center p-3 text-sm font-medium text-gray-600">Fim</th>
                    <th className="text-center p-3 text-sm font-medium text-gray-600">Dias</th>
                    <th className="text-center p-3 text-sm font-medium text-gray-600">Vendidos</th>
                    <th className="text-center p-3 text-sm font-medium text-gray-600">Status</th>
                    <th className="text-center p-3 text-sm font-medium text-gray-600">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {ferias.map((f) => {
                    const hoje = new Date();
                    const inicio = new Date(f.data_inicio);
                    const fim = new Date(f.data_fim);
                    const dias = Math.ceil((fim - inicio) / (1000 * 60 * 60 * 24)) + 1;
                    const status = hoje >= inicio && hoje <= fim ? 'em_ferias' : hoje > fim ? 'concluido' : 'agendado';
                    
                    return (
                      <tr key={f.id} className="border-t hover:bg-gray-50">
                        <td className="p-3 text-sm font-medium">{getFuncionarioNome(f.funcionario_id)}</td>
                        <td className="p-3 text-sm text-center">{new Date(f.data_inicio).toLocaleDateString('pt-BR')}</td>
                        <td className="p-3 text-sm text-center">{new Date(f.data_fim).toLocaleDateString('pt-BR')}</td>
                        <td className="p-3 text-sm text-center font-medium">{dias}</td>
                        <td className="p-3 text-sm text-center">{f.dias_vendidos || 0}</td>
                        <td className="p-3 text-sm text-center">
                          <span className={`px-2 py-1 rounded text-xs ${
                            status === 'em_ferias' ? 'bg-green-100 text-green-700' :
                            status === 'concluido' ? 'bg-gray-100 text-gray-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {status === 'em_ferias' ? 'Em Férias' : status === 'concluido' ? 'Concluído' : 'Agendado'}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex justify-center gap-1">
                            <Button size="sm" variant="outline" onClick={() => openModal(f)}><Edit size={14} /></Button>
                            <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(f.id)}><Trash2 size={14} /></Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Agendar Férias */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingFerias ? "Editar Férias" : "Agendar Férias"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Funcionário *</Label>
              <Select value={formData.funcionario_id} onValueChange={(v) => setFormData({...formData, funcionario_id: v})}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  {funcionarios.filter(f => f.status === 'ativo').map(f => (
                    <SelectItem key={f.id} value={f.id}>{f.nome}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Data Início *</Label>
                <Input type="date" value={formData.data_inicio} onChange={(e) => setFormData({...formData, data_inicio: e.target.value})} required />
              </div>
              <div>
                <Label>Data Fim *</Label>
                <Input type="date" value={formData.data_fim} onChange={(e) => setFormData({...formData, data_fim: e.target.value})} required />
              </div>
            </div>

            <div className="p-3 bg-blue-50 rounded-lg text-center">
              <p className="text-sm text-gray-600">Total de dias:</p>
              <p className="text-2xl font-bold text-blue-600">{calcularDiasFerias()} dias</p>
            </div>
            
            <div>
              <Label>Dias Vendidos (abono pecuniário)</Label>
              <Input 
                type="number" 
                min="0" 
                max="10" 
                value={formData.dias_vendidos} 
                onChange={(e) => setFormData({...formData, dias_vendidos: parseInt(e.target.value) || 0})} 
              />
              <p className="text-xs text-gray-500 mt-1">Máximo de 1/3 das férias (10 dias)</p>
            </div>
            
            <div>
              <Label>Observações</Label>
              <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} />
            </div>

            <DialogFooter className="gap-2">
              <Button type="button" variant="outline" onClick={closeModal}>Cancelar</Button>
              <Button type="submit" className="bg-[#10B981] hover:bg-[#059669]">{editingFerias ? "Atualizar" : "Agendar"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
