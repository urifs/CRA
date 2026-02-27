import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { UserPlus, Search, Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { formatCPF, formatCNPJ, formatCEP, formatTelefone, formatCurrency, parseCurrency } from "@/utils/masks";

const tiposCadastro = [
  { value: "cliente", label: "Cliente" },
  { value: "fornecedor", label: "Fornecedor" },
  { value: "cli_forn", label: "Cliente/Fornecedor" },
  { value: "transportador", label: "Transportador" }
];

const initialFormData = {
  tipo_cadastro: "fornecedor",
  tipo_pessoa: "PJ",
  status: "ativo",
  nome_razao: "",
  apelido_fantasia: "",
  cpf_cnpj: "",
  rg_ie: "",
  telefone: "",
  celular: "",
  email: "",
  cep: "",
  endereco: "",
  numero: "",
  complemento: "",
  bairro: "",
  cidade: "",
  uf: "",
  grupo: "",
  rota: "",
  vendedor: "",
  limite_credito: "",
  observacoes: ""
};

export default function CadastroFormModal({ 
  open, 
  onOpenChange, 
  defaultTipo = "fornecedor",
  onSuccess 
}) {
  const [formData, setFormData] = useState({ ...initialFormData, tipo_cadastro: defaultTipo });
  const [consultandoCnpj, setConsultandoCnpj] = useState(false);
  const [consultandoCep, setConsultandoCep] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setFormData({ ...initialFormData, tipo_cadastro: defaultTipo });
    }
  }, [open, defaultTipo]);

  const handleConsultaCnpj = async () => {
    const cnpj = formData.cpf_cnpj.replace(/\D/g, "");
    if (cnpj.length !== 14) {
      toast.error("CNPJ deve ter 14 dígitos");
      return;
    }
    setConsultandoCnpj(true);
    try {
      const response = await axios.get(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
      const data = response.data;
      setFormData({
        ...formData,
        nome_razao: data.razao_social || formData.nome_razao,
        apelido_fantasia: data.nome_fantasia || formData.apelido_fantasia,
        telefone: data.ddd_telefone_1 || formData.telefone,
        email: data.email || formData.email,
        cep: data.cep || formData.cep,
        endereco: data.logradouro || formData.endereco,
        numero: data.numero || formData.numero,
        complemento: data.complemento || formData.complemento,
        bairro: data.bairro || formData.bairro,
        cidade: data.municipio || formData.cidade,
        uf: data.uf || formData.uf,
      });
      toast.success("Dados preenchidos automaticamente!");
    } catch (error) {
      toast.error("Erro ao consultar CNPJ");
    } finally {
      setConsultandoCnpj(false);
    }
  };

  const handleConsultaCep = async () => {
    const cep = formData.cep.replace(/\D/g, "");
    if (cep.length !== 8) {
      toast.error("CEP deve ter 8 dígitos");
      return;
    }
    setConsultandoCep(true);
    try {
      const response = await axios.get(`https://viacep.com.br/ws/${cep}/json/`);
      if (response.data.erro) {
        toast.error("CEP não encontrado");
        return;
      }
      setFormData({
        ...formData,
        endereco: response.data.logradouro || formData.endereco,
        bairro: response.data.bairro || formData.bairro,
        cidade: response.data.localidade || formData.cidade,
        uf: response.data.uf || formData.uf,
      });
      toast.success("Endereço preenchido!");
    } catch (error) {
      toast.error("Erro ao consultar CEP");
    } finally {
      setConsultandoCep(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.nome_razao.trim()) {
      toast.error("Nome/Razão Social é obrigatório");
      return;
    }
    setSubmitting(true);
    try {
      const dataToSend = {
        ...formData,
        limite_credito: formData.limite_credito ? parseFloat(formData.limite_credito) : null,
      };
      const response = await axios.post(`${API}/admin/cadastros`, dataToSend);
      toast.success("Cadastro realizado com sucesso!");
      onOpenChange(false);
      if (onSuccess) {
        onSuccess(response.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao cadastrar");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" data-testid="cadastro-form-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus size={20} />
            Novo Cadastro
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Tipo e Status */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="form-label">Tipo de Cadastro *</label>
              <Select value={formData.tipo_cadastro} onValueChange={(v) => setFormData({...formData, tipo_cadastro: v})}>
                <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  {tiposCadastro.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="form-label">Pessoa *</label>
              <Select value={formData.tipo_pessoa} onValueChange={(v) => setFormData({...formData, tipo_pessoa: v})}>
                <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  <SelectItem value="PF">Pessoa Física</SelectItem>
                  <SelectItem value="PJ">Pessoa Jurídica</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="form-label">Status *</label>
              <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                <SelectTrigger className="w-full h-11"><SelectValue /></SelectTrigger>
                <SelectContent className="z-[9999]">
                  <SelectItem value="ativo">Ativo</SelectItem>
                  <SelectItem value="inativo">Inativo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Dados principais */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="form-label">{formData.tipo_pessoa === "PJ" ? "Razão Social" : "Nome"} *</label>
              <Input 
                value={formData.nome_razao} 
                onChange={(e) => setFormData({...formData, nome_razao: e.target.value})} 
                required 
                data-testid="cadastro-nome-razao"
              />
            </div>
            <div>
              <label className="form-label">{formData.tipo_pessoa === "PJ" ? "Nome Fantasia" : "Apelido"}</label>
              <Input value={formData.apelido_fantasia} onChange={(e) => setFormData({...formData, apelido_fantasia: e.target.value})} />
            </div>
            <div>
              <label className="form-label">{formData.tipo_pessoa === "PJ" ? "CNPJ" : "CPF"}</label>
              <div className="flex gap-2">
                <Input 
                  value={formData.cpf_cnpj} 
                  onChange={(e) => setFormData({...formData, cpf_cnpj: formData.tipo_pessoa === "PJ" ? formatCNPJ(e.target.value) : formatCPF(e.target.value)})} 
                  placeholder={formData.tipo_pessoa === "PJ" ? "00.000.000/0000-00" : "000.000.000-00"} 
                  className="flex-1"
                  data-testid="cadastro-cpf-cnpj"
                />
                {formData.tipo_pessoa === "PJ" && (
                  <Button 
                    type="button" 
                    size="sm" 
                    variant="outline"
                    onClick={handleConsultaCnpj}
                    disabled={consultandoCnpj}
                    className="text-[#D4A000] border-[#D4A000] hover:bg-[#D4A000] hover:text-white"
                    title="Consultar CNPJ e preencher dados"
                  >
                    {consultandoCnpj ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                  </Button>
                )}
              </div>
              {formData.tipo_pessoa === "PJ" && (
                <p className="text-xs text-gray-500 mt-1">Clique na lupa para consultar e preencher automaticamente</p>
              )}
            </div>
            <div>
              <label className="form-label">{formData.tipo_pessoa === "PJ" ? "Inscrição Estadual" : "RG"}</label>
              <Input value={formData.rg_ie} onChange={(e) => setFormData({...formData, rg_ie: e.target.value})} />
            </div>
          </div>

          {/* Contato */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="form-label">Telefone</label>
              <Input 
                value={formData.telefone} 
                onChange={(e) => setFormData({...formData, telefone: formatTelefone(e.target.value)})} 
                placeholder="(00) 0000-0000" 
                data-testid="cadastro-telefone"
              />
            </div>
            <div>
              <label className="form-label">Celular</label>
              <Input value={formData.celular} onChange={(e) => setFormData({...formData, celular: formatTelefone(e.target.value)})} placeholder="(00) 00000-0000" />
            </div>
            <div>
              <label className="form-label">Email</label>
              <Input 
                type="email" 
                value={formData.email} 
                onChange={(e) => setFormData({...formData, email: e.target.value})} 
                data-testid="cadastro-email"
              />
            </div>
          </div>

          {/* Endereço */}
          <div className="grid grid-cols-6 gap-4">
            <div>
              <label className="form-label">CEP</label>
              <div className="flex gap-1">
                <Input 
                  value={formData.cep} 
                  onChange={(e) => setFormData({...formData, cep: formatCEP(e.target.value)})} 
                  placeholder="00000-000" 
                  className="flex-1"
                />
                <Button 
                  type="button" 
                  size="sm" 
                  variant="outline"
                  onClick={handleConsultaCep}
                  disabled={consultandoCep}
                  className="text-blue-600 border-blue-600 hover:bg-blue-600 hover:text-white px-2"
                  title="Buscar endereço pelo CEP"
                >
                  {consultandoCep ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                </Button>
              </div>
            </div>
            <div className="col-span-3">
              <label className="form-label">Endereço</label>
              <Input value={formData.endereco} onChange={(e) => setFormData({...formData, endereco: e.target.value})} />
            </div>
            <div>
              <label className="form-label">Número</label>
              <Input value={formData.numero} onChange={(e) => setFormData({...formData, numero: e.target.value})} />
            </div>
            <div>
              <label className="form-label">Complemento</label>
              <Input value={formData.complemento} onChange={(e) => setFormData({...formData, complemento: e.target.value})} />
            </div>
            <div className="col-span-2">
              <label className="form-label">Bairro</label>
              <Input value={formData.bairro} onChange={(e) => setFormData({...formData, bairro: e.target.value})} />
            </div>
            <div className="col-span-2">
              <label className="form-label">Cidade</label>
              <Input value={formData.cidade} onChange={(e) => setFormData({...formData, cidade: e.target.value})} />
            </div>
            <div>
              <label className="form-label">UF</label>
              <Input value={formData.uf} onChange={(e) => setFormData({...formData, uf: e.target.value})} maxLength={2} />
            </div>
          </div>

          {/* Dados adicionais */}
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="form-label">Grupo</label>
              <Input value={formData.grupo} onChange={(e) => setFormData({...formData, grupo: e.target.value})} />
            </div>
            <div>
              <label className="form-label">Rota</label>
              <Input value={formData.rota} onChange={(e) => setFormData({...formData, rota: e.target.value})} />
            </div>
            <div>
              <label className="form-label">Vendedor</label>
              <Input value={formData.vendedor} onChange={(e) => setFormData({...formData, vendedor: e.target.value})} />
            </div>
            <div>
              <label className="form-label">Limite de Crédito</label>
              <Input type="number" step="0.01" value={formData.limite_credito} onChange={(e) => setFormData({...formData, limite_credito: e.target.value})} />
            </div>
          </div>

          <div>
            <label className="form-label">Observações</label>
            <Input value={formData.observacoes} onChange={(e) => setFormData({...formData, observacoes: e.target.value})} />
          </div>

          <div className="flex gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="flex-1">Cancelar</Button>
            <Button 
              type="submit" 
              className="flex-1 bg-[#D4A000] hover:bg-[#b38900]"
              disabled={submitting}
              data-testid="cadastro-submit-btn"
            >
              {submitting ? <Loader2 size={16} className="animate-spin mr-2" /> : null}
              Cadastrar
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
