import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { 
  Building2, 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Loader2,
  CreditCard,
  Wallet,
  PiggyBank,
  TrendingUp,
  QrCode,
  Copy,
  CheckCircle,
  XCircle
} from "lucide-react";
import { formatCPFouCNPJ, formatCurrency as formatCurrencyMask, parseCurrency } from "@/utils/masks";

const BANCOS_BRASIL = [
  { codigo: "001", nome: "Banco do Brasil" },
  { codigo: "033", nome: "Santander" },
  { codigo: "104", nome: "Caixa Econômica Federal" },
  { codigo: "237", nome: "Bradesco" },
  { codigo: "341", nome: "Itaú Unibanco" },
  { codigo: "356", nome: "Banco Real" },
  { codigo: "389", nome: "Banco Mercantil do Brasil" },
  { codigo: "399", nome: "HSBC" },
  { codigo: "422", nome: "Banco Safra" },
  { codigo: "453", nome: "Banco Rural" },
  { codigo: "633", nome: "Banco Rendimento" },
  { codigo: "652", nome: "Itaú Unibanco Holding" },
  { codigo: "745", nome: "Citibank" },
  { codigo: "756", nome: "Sicoob" },
  { codigo: "077", nome: "Banco Inter" },
  { codigo: "260", nome: "Nubank" },
  { codigo: "290", nome: "PagSeguro" },
  { codigo: "323", nome: "Mercado Pago" },
  { codigo: "380", nome: "PicPay" },
  { codigo: "212", nome: "Banco Original" },
  { codigo: "336", nome: "C6 Bank" },
  { codigo: "000", nome: "Outro" },
];

const TIPOS_CONTA = [
  { value: "corrente", label: "Conta Corrente" },
  { value: "poupanca", label: "Conta Poupança" },
  { value: "investimento", label: "Conta Investimento" },
  { value: "caixa", label: "Caixa" },
];

const TIPOS_CHAVE_PIX = [
  { value: "cpf", label: "CPF" },
  { value: "cnpj", label: "CNPJ" },
  { value: "email", label: "E-mail" },
  { value: "telefone", label: "Telefone" },
  { value: "aleatoria", label: "Chave Aleatória" },
];

const CORES = [
  "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", 
  "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1"
];

export default function ContasBancariasPage() {
  const { token } = useAuth();
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingConta, setEditingConta] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  
  const [formData, setFormData] = useState({
    nome: "",
    banco: "",
    codigo_banco: "",
    agencia: "",
    agencia_digito: "",
    conta: "",
    conta_digito: "",
    tipo_conta: "corrente",
    titular: "",
    cpf_cnpj_titular: "",
    chave_pix: "",
    tipo_chave_pix: "",
    saldo_inicial: "0",
    saldo_atual: "0",
    ativo: true,
    cor: "#3B82F6",
    observacoes: ""
  });

  useEffect(() => { fetchContas(); }, []);

  const fetchContas = async () => {
    try {
      const response = await axios.get(`${API}/admin/contas-bancarias`);
      setContas(response.data);
    } catch (error) {
      toast.error("Erro ao carregar contas bancárias");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.nome || !formData.banco || !formData.agencia || !formData.conta) {
      toast.error("Preencha os campos obrigatórios");
      return;
    }

    try {
      const payload = {
        ...formData,
        saldo_inicial: parseCurrency(formData.saldo_inicial) || 0,
        saldo_atual: parseCurrency(formData.saldo_atual) || 0
      };

      if (editingConta) {
        await axios.put(`${API}/admin/contas-bancarias/${editingConta.id}`, payload);
        toast.success("Conta bancária atualizada!");
      } else {
        await axios.post(`${API}/admin/contas-bancarias`, payload);
        toast.success("Conta bancária cadastrada!");
      }
      
      closeModal();
      fetchContas();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar");
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await axios.delete(`${API}/admin/contas-bancarias/${deleteId}`);
      toast.success("Conta bancária excluída!");
      setDeleteId(null);
      fetchContas();
    } catch (error) {
      toast.error("Erro ao excluir");
    }
  };

  const openModal = (conta = null) => {
    if (conta) {
      setEditingConta(conta);
      setFormData({
        nome: conta.nome || "",
        banco: conta.banco || "",
        codigo_banco: conta.codigo_banco || "",
        agencia: conta.agencia || "",
        agencia_digito: conta.agencia_digito || "",
        conta: conta.conta || "",
        conta_digito: conta.conta_digito || "",
        tipo_conta: conta.tipo_conta || "corrente",
        titular: conta.titular || "",
        cpf_cnpj_titular: conta.cpf_cnpj_titular || "",
        chave_pix: conta.chave_pix || "",
        tipo_chave_pix: conta.tipo_chave_pix || "",
        saldo_inicial: String(conta.saldo_inicial || 0),
        saldo_atual: String(conta.saldo_atual || 0),
        ativo: conta.ativo !== false,
        cor: conta.cor || "#3B82F6",
        observacoes: conta.observacoes || ""
      });
    } else {
      setEditingConta(null);
      setFormData({
        nome: "", banco: "", codigo_banco: "", agencia: "", agencia_digito: "",
        conta: "", conta_digito: "", tipo_conta: "corrente", titular: "",
        cpf_cnpj_titular: "", chave_pix: "", tipo_chave_pix: "", saldo_inicial: "0",
        saldo_atual: "0", ativo: true, cor: "#3B82F6", observacoes: ""
      });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingConta(null);
  };

  const handleBancoChange = (codigoBanco) => {
    const banco = BANCOS_BRASIL.find(b => b.codigo === codigoBanco);
    setFormData({
      ...formData,
      codigo_banco: codigoBanco,
      banco: banco?.nome || ""
    });
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado!");
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);
  };

  const filteredContas = contas.filter(c => 
    c.nome?.toLowerCase().includes(search.toLowerCase()) ||
    c.banco?.toLowerCase().includes(search.toLowerCase()) ||
    c.agencia?.includes(search) ||
    c.conta?.includes(search)
  );

  const totalSaldo = contas.filter(c => c.ativo).reduce((acc, c) => acc + (c.saldo_atual || 0), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-[#D4A000]" />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Building2 className="text-[#D4A000]" />
            Contas Bancárias
          </h1>
          <p className="text-gray-500 mt-1">Gerencie as contas bancárias da empresa</p>
        </div>
        <Button onClick={() => openModal()} className="bg-[#D4A000] hover:bg-[#b8860b]" data-testid="new-conta-bancaria-btn">
          <Plus size={20} className="mr-2" />
          Nova Conta Bancária
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Total de Contas</p>
                <p className="text-2xl font-bold">{contas.length}</p>
              </div>
              <CreditCard size={32} className="opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Contas Ativas</p>
                <p className="text-2xl font-bold">{contas.filter(c => c.ativo).length}</p>
              </div>
              <CheckCircle size={32} className="opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-amber-100 text-sm">Saldo Total</p>
                <p className="text-2xl font-bold">{formatCurrency(totalSaldo)}</p>
              </div>
              <Wallet size={32} className="opacity-80" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Com PIX</p>
                <p className="text-2xl font-bold">{contas.filter(c => c.chave_pix).length}</p>
              </div>
              <QrCode size={32} className="opacity-80" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <Input
          placeholder="Buscar por nome, banco, agência ou conta..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          data-testid="search-contas-bancarias"
        />
      </div>

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredContas.map((conta) => (
          <Card 
            key={conta.id} 
            className={`overflow-hidden transition-all hover:shadow-lg ${!conta.ativo ? 'opacity-60' : ''}`}
            style={{ borderTop: `4px solid ${conta.cor || '#3B82F6'}` }}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${conta.cor}20`, color: conta.cor }}
                  >
                    {conta.tipo_conta === 'poupanca' ? <PiggyBank size={20} /> : 
                     conta.tipo_conta === 'investimento' ? <TrendingUp size={20} /> : 
                     conta.tipo_conta === 'caixa' ? <Wallet size={20} /> : 
                     <CreditCard size={20} />}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{conta.nome}</h3>
                    <p className="text-sm text-gray-500">{conta.banco}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => openModal(conta)} className="h-8 w-8 p-0">
                    <Edit size={14} />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setDeleteId(conta.id)} className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50">
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Agência:</span>
                  <span className="font-mono">{conta.agencia}{conta.agencia_digito ? `-${conta.agencia_digito}` : ''}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Conta:</span>
                  <span className="font-mono">{conta.conta}{conta.conta_digito ? `-${conta.conta_digito}` : ''}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Tipo:</span>
                  <span className="capitalize">{conta.tipo_conta?.replace('_', ' ')}</span>
                </div>
                {conta.chave_pix && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 flex items-center gap-1">
                      <QrCode size={12} /> PIX:
                    </span>
                    <button 
                      onClick={() => copyToClipboard(conta.chave_pix)}
                      className="font-mono text-xs truncate max-w-[150px] hover:text-blue-600 flex items-center gap-1"
                      title={conta.chave_pix}
                    >
                      {conta.chave_pix.length > 20 ? conta.chave_pix.slice(0, 20) + '...' : conta.chave_pix}
                      <Copy size={10} />
                    </button>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t flex justify-between items-center">
                <span className="text-gray-500 text-sm">Saldo Atual:</span>
                <span className={`text-lg font-bold ${(conta.saldo_atual || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(conta.saldo_atual)}
                </span>
              </div>

              {!conta.ativo && (
                <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
                  <XCircle size={12} />
                  Conta Inativa
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredContas.length === 0 && (
        <div className="text-center py-12">
          <Building2 size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Nenhuma conta bancária encontrada</p>
          <Button onClick={() => openModal()} className="mt-4 bg-[#D4A000] hover:bg-[#b8860b]">
            <Plus size={16} className="mr-2" />
            Cadastrar Primeira Conta
          </Button>
        </div>
      )}

      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building2 className="text-[#D4A000]" />
              {editingConta ? "Editar Conta Bancária" : "Nova Conta Bancária"}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Nome e Cor */}
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2">
                <Label>Nome da Conta *</Label>
                <Input 
                  value={formData.nome} 
                  onChange={(e) => setFormData({...formData, nome: e.target.value})}
                  placeholder="Ex: Conta Principal, Poupança"
                  required
                />
              </div>
              <div>
                <Label>Cor</Label>
                <div className="flex flex-wrap gap-1 mt-2">
                  {CORES.map(cor => (
                    <button
                      key={cor}
                      type="button"
                      onClick={() => setFormData({...formData, cor})}
                      className={`w-6 h-6 rounded-full border-2 ${formData.cor === cor ? 'border-gray-900 scale-110' : 'border-transparent'}`}
                      style={{ backgroundColor: cor }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Banco */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Banco *</Label>
                <Select value={formData.codigo_banco} onValueChange={handleBancoChange}>
                  <SelectTrigger><SelectValue placeholder="Selecione o banco" /></SelectTrigger>
                  <SelectContent>
                    {BANCOS_BRASIL.map(b => (
                      <SelectItem key={b.codigo} value={b.codigo}>
                        {b.codigo !== "000" ? `${b.codigo} - ` : ''}{b.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Tipo de Conta *</Label>
                <Select value={formData.tipo_conta} onValueChange={(v) => setFormData({...formData, tipo_conta: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {TIPOS_CONTA.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Agência e Conta */}
            <div className="grid grid-cols-4 gap-4">
              <div className="col-span-1">
                <Label>Agência *</Label>
                <Input 
                  value={formData.agencia} 
                  onChange={(e) => setFormData({...formData, agencia: e.target.value})}
                  placeholder="0000"
                  required
                />
              </div>
              <div className="col-span-1">
                <Label>Dígito</Label>
                <Input 
                  value={formData.agencia_digito} 
                  onChange={(e) => setFormData({...formData, agencia_digito: e.target.value})}
                  placeholder="0"
                  maxLength={2}
                />
              </div>
              <div className="col-span-1">
                <Label>Conta *</Label>
                <Input 
                  value={formData.conta} 
                  onChange={(e) => setFormData({...formData, conta: e.target.value})}
                  placeholder="00000"
                  required
                />
              </div>
              <div className="col-span-1">
                <Label>Dígito</Label>
                <Input 
                  value={formData.conta_digito} 
                  onChange={(e) => setFormData({...formData, conta_digito: e.target.value})}
                  placeholder="0"
                  maxLength={2}
                />
              </div>
            </div>

            {/* Titular */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Titular</Label>
                <Input 
                  value={formData.titular} 
                  onChange={(e) => setFormData({...formData, titular: e.target.value})}
                  placeholder="Nome do titular"
                />
              </div>
              <div>
                <Label>CPF/CNPJ do Titular</Label>
                <Input 
                  value={formData.cpf_cnpj_titular} 
                  onChange={(e) => setFormData({...formData, cpf_cnpj_titular: formatCPFouCNPJ(e.target.value)})}
                  placeholder="000.000.000-00"
                />
              </div>
            </div>

            {/* PIX */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Tipo da Chave PIX</Label>
                <Select value={formData.tipo_chave_pix || "none"} onValueChange={(v) => setFormData({...formData, tipo_chave_pix: v === "none" ? "" : v})}>
                  <SelectTrigger><SelectValue placeholder="Selecione..." /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Nenhum</SelectItem>
                    {TIPOS_CHAVE_PIX.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Chave PIX</Label>
                <Input 
                  value={formData.chave_pix} 
                  onChange={(e) => setFormData({...formData, chave_pix: e.target.value})}
                  placeholder="Digite a chave PIX"
                />
              </div>
            </div>

            {/* Saldo e Status */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Saldo Inicial</Label>
                <Input 
                  type="number"
                  step="0.01"
                  value={formData.saldo_inicial} 
                  onChange={(e) => setFormData({...formData, saldo_inicial: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              <div>
                <Label>Saldo Atual</Label>
                <Input 
                  type="number"
                  step="0.01"
                  value={formData.saldo_atual} 
                  onChange={(e) => setFormData({...formData, saldo_atual: e.target.value})}
                  placeholder="0.00"
                  data-testid="saldo-atual-input"
                />
                <p className="text-xs text-gray-500 mt-1">Atualizado automaticamente nas quitações</p>
              </div>
              <div>
                <Label>Status</Label>
                <Select value={formData.ativo ? "ativo" : "inativo"} onValueChange={(v) => setFormData({...formData, ativo: v === "ativo"})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ativo">Ativa</SelectItem>
                    <SelectItem value="inativo">Inativa</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Observações */}
            <div>
              <Label>Observações</Label>
              <Input 
                value={formData.observacoes} 
                onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                placeholder="Observações adicionais"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeModal}>Cancelar</Button>
              <Button type="submit" className="bg-[#D4A000] hover:bg-[#b8860b]">
                {editingConta ? "Atualizar" : "Cadastrar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar Exclusão</DialogTitle>
          </DialogHeader>
          <p className="text-gray-600">Tem certeza que deseja excluir esta conta bancária? Esta ação não pode ser desfeita.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancelar</Button>
            <Button variant="destructive" onClick={handleDelete}>Excluir</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
