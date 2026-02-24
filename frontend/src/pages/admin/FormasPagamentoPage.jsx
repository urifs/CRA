import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Plus, Search, Edit, Trash2, CreditCard, CheckCircle2, XCircle, Percent, Clock
} from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const tiposForma = [
  { value: "dinheiro", label: "Dinheiro" },
  { value: "pix", label: "PIX" },
  { value: "cartao_debito", label: "Cartão Débito" },
  { value: "cartao_credito", label: "Cartão Crédito" },
  { value: "boleto", label: "Boleto" },
  { value: "cheque", label: "Cheque" },
  { value: "transferencia", label: "Transferência" },
  { value: "deposito", label: "Depósito" },
  { value: "outros", label: "Outros" }
];

export default function FormasPagamentoPage() {
  const [formas, setFormas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingForma, setEditingForma] = useState(null);
  const [formData, setFormData] = useState({
    codigo: "", nome: "", tipo: "outros", taxa: "0", prazo_recebimento: "0", 
    conta_bancaria: "", ativo: true, observacoes: ""
  });

  useEffect(() => { fetchFormas(); }, []);

  const fetchFormas = async () => {
    try {
      const response = await axios.get(`${API}/admin/formas-pagamento`);
      setFormas(response.data);
    } catch (error) { toast.error("Erro ao carregar formas de pagamento"); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const dataToSend = {
        ...formData,
        taxa: parseFloat(formData.taxa) || 0,
        prazo_recebimento: parseInt(formData.prazo_recebimento) || 0
      };
      if (editingForma) {
        await axios.put(`${API}/admin/formas-pagamento/${editingForma.id}`, dataToSend);
        toast.success("Forma de pagamento atualizada!");
      } else {
        await axios.post(`${API}/admin/formas-pagamento`, dataToSend);
        toast.success("Forma de pagamento cadastrada!");
      }
      fetchFormas(); closeModal();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao salvar"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Excluir esta forma de pagamento?")) return;
    try {
      await axios.delete(`${API}/admin/formas-pagamento/${id}`);
      toast.success("Forma de pagamento excluída!"); fetchFormas();
    } catch (error) { toast.error(error.response?.data?.detail || "Erro ao excluir"); }
  };

  const openModal = (forma = null) => {
    if (forma) {
      setEditingForma(forma);
      setFormData({
        codigo: forma.codigo || "",
        nome: forma.nome || "",
        tipo: forma.tipo || "outros",
        taxa: forma.taxa?.toString() || "0",
        prazo_recebimento: forma.prazo_recebimento?.toString() || "0",
        conta_bancaria: forma.conta_bancaria || "",
        ativo: forma.ativo !== false,
        observacoes: forma.observacoes || ""
      });
    } else {
      setEditingForma(null);
      setFormData({
        codigo: "", nome: "", tipo: "outros", taxa: "0", prazo_recebimento: "0",
        conta_bancaria: "", ativo: true, observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingForma(null); };

  const filteredFormas = formas.filter(f =>
    f.nome?.toLowerCase().includes(search.toLowerCase()) ||
    f.codigo?.toLowerCase().includes(search.toLowerCase()) ||
    f.tipo?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="flex items-center justify-center min-h-[400px]"><div className="spinner w-12 h-12"></div></div>;

  return (
    <div data-testid="formas-pagamento-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Formas de Pagamento</h1>
          <p className="text-slate-500 mt-1">Configure as formas de pagamento disponíveis</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#FFC232] hover:bg-[#FFC232]" data-testid="new-forma-btn">
          <Plus size={18} className="mr-2" />Nova Forma
        </Button>
      </div>

      {/* Busca */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
          <Input 
            placeholder="Buscar por código, nome ou tipo..." 
            value={search} 
            onChange={(e) => setSearch(e.target.value)} 
            className="pl-10" 
          />
        </div>
      </div>

      {/* Resumo */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <CreditCard className="text-[#FFC232]" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Total de Formas</p>
              <p className="text-lg font-bold text-[#FFC232]">{formas.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-slate-500">Ativas</p>
              <p className="text-lg font-bold text-green-600">{formas.filter(f => f.ativo !== false).length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista */}
      {filteredFormas.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            <CreditCard className="mx-auto mb-4" size={48} />
            <p>Nenhuma forma de pagamento encontrada</p>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-3 font-medium text-slate-600">Código</th>
                <th className="text-left p-3 font-medium text-slate-600">Nome</th>
                <th className="text-left p-3 font-medium text-slate-600">Tipo</th>
                <th className="text-right p-3 font-medium text-slate-600">Taxa %</th>
                <th className="text-right p-3 font-medium text-slate-600">Prazo (dias)</th>
                <th className="text-left p-3 font-medium text-slate-600">Conta</th>
                <th className="text-left p-3 font-medium text-slate-600">Status</th>
                <th className="text-center p-3 font-medium text-slate-600">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredFormas.map((f) => (
                <tr key={f.id} className="border-t hover:bg-slate-50" data-testid={`forma-${f.id}`}>
                  <td className="p-3 font-mono">{f.codigo || "-"}</td>
                  <td className="p-3 font-medium">{f.nome}</td>
                  <td className="p-3">
                    <span className="px-2 py-1 rounded text-xs bg-slate-100 text-slate-700">
                      {tiposForma.find(t => t.value === f.tipo)?.label || f.tipo}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    {f.taxa > 0 ? (
                      <span className="text-[#E31A1A] flex items-center justify-end gap-1">
                        <Percent size={12} />{f.taxa}%
                      </span>
                    ) : "-"}
                  </td>
                  <td className="p-3 text-right">
                    {f.prazo_recebimento > 0 ? (
                      <span className="flex items-center justify-end gap-1">
                        <Clock size={12} />{f.prazo_recebimento}d
                      </span>
                    ) : "-"}
                  </td>
                  <td className="p-3 text-slate-500">{f.conta_bancaria || "-"}</td>
                  <td className="p-3">
                    {f.ativo !== false ? (
                      <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-700">
                        <CheckCircle2 className="inline mr-1" size={12} />Ativa
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs bg-slate-100 text-slate-600">
                        <XCircle className="inline mr-1" size={12} />Inativa
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-center">
                    <div className="flex justify-center gap-1">
                      <Button size="sm" variant="outline" onClick={() => openModal(f)}><Edit size={14} /></Button>
                      <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDelete(f.id)}><Trash2 size={14} /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingForma ? "Editar Forma de Pagamento" : "Nova Forma de Pagamento"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Código</label>
                <Input value={formData.codigo} onChange={(e) => setFormData({...formData, codigo: e.target.value})} placeholder="Ex: FP001" />
              </div>
              <div>
                <label className="form-label">Tipo</label>
                <Select value={formData.tipo} onValueChange={(value) => setFormData({...formData, tipo: value})}>
                  <SelectTrigger className="w-full h-11">
                    <SelectValue placeholder="Selecione o tipo" />
                  </SelectTrigger>
                  <SelectContent className="z-[9999]">
                    {tiposForma.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <label className="form-label">Nome *</label>
              <Input value={formData.nome} onChange={(e) => setFormData({...formData, nome: e.target.value})} required placeholder="Nome da forma de pagamento" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Taxa (%)</label>
                <Input type="number" step="0.01" value={formData.taxa} onChange={(e) => setFormData({...formData, taxa: e.target.value})} placeholder="0.00" />
              </div>
              <div>
                <label className="form-label">Prazo Recebimento (dias)</label>
                <Input type="number" value={formData.prazo_recebimento} onChange={(e) => setFormData({...formData, prazo_recebimento: e.target.value})} placeholder="0" />
              </div>
            </div>
            <div>
              <label className="form-label">Conta Bancária</label>
              <Input value={formData.conta_bancaria} onChange={(e) => setFormData({...formData, conta_bancaria: e.target.value})} placeholder="Conta associada (opcional)" />
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="ativo" checked={formData.ativo} onChange={(e) => setFormData({...formData, ativo: e.target.checked})} className="w-4 h-4" />
              <label htmlFor="ativo" className="text-sm">Forma de pagamento ativa</label>
            </div>
            <div>
              <label className="form-label">Observações</label>
              <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} placeholder="Observações (opcional)" />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={closeModal} className="flex-1">Cancelar</Button>
              <Button type="submit" className="flex-1 bg-[#FFC232] hover:bg-[#FFC232]">{editingForma ? "Atualizar" : "Cadastrar"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
