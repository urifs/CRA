import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  FileDown, 
  Loader2, 
  FileText,
  Truck,
  Wrench,
  Package,
  Building2,
  DollarSign,
  Users,
  ClipboardList,
  CreditCard,
  Download,
  CheckCircle2
} from "lucide-react";

const CATEGORY_ICONS = {
  machines: Truck,
  maintenances: Wrench,
  categories: FileText,
  stock_items: Package,
  stock_movements: Package,
  obras: Building2,
  usage_logs: ClipboardList,
  contas_pagar: DollarSign,
  contas_receber: DollarSign,
  cadastros: Users,
  produtos_admin: Package,
  ordens_servico: ClipboardList,
  alugueis: Truck,
  plano_contas: FileText,
  centros_custo: Building2,
  formas_pagamento: CreditCard,
};

export default function ExportPage({ module = "gerenciamento" }) {
  const { token } = useAuth();
  const [categories, setCategories] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null);

  const accentColor = module === "gerenciamento" ? "#E31A1A" : "#D4A000";

  useEffect(() => {
    fetchCategories();
  }, [module]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/api/export/categories/${module}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data);
    } catch (error) {
      console.error("Erro ao carregar categorias:", error);
      toast.error("Erro ao carregar categorias de exportação");
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (categoryId) => {
    setSelectedCategories(prev => 
      prev.includes(categoryId) 
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const selectAll = () => {
    if (selectedCategories.length === categories.length) {
      setSelectedCategories([]);
    } else {
      setSelectedCategories(categories.map(c => c.id));
    }
  };

  const exportPDF = async (categoryId) => {
    setExporting(categoryId);
    try {
      const response = await axios.get(`${API}/api/export/pdf/${categoryId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `CRA_Relatorio_${categoryId}.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("PDF exportado com sucesso!");
    } catch (error) {
      console.error("Erro ao exportar:", error);
      toast.error("Erro ao exportar PDF");
    } finally {
      setExporting(null);
    }
  };

  const exportSelected = async () => {
    if (selectedCategories.length === 0) {
      toast.error("Selecione pelo menos uma categoria");
      return;
    }

    for (const categoryId of selectedCategories) {
      await exportPDF(categoryId);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: accentColor }} />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div 
            className="w-12 h-12 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${accentColor}20` }}
          >
            <FileDown size={24} style={{ color: accentColor }} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Exportação de Relatórios</h1>
            <p className="text-sm text-gray-500">Selecione as categorias para exportar em PDF</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={selectAll}
            className="border-gray-300"
          >
            {selectedCategories.length === categories.length ? "Desmarcar Todos" : "Selecionar Todos"}
          </Button>
          <Button
            onClick={exportSelected}
            disabled={selectedCategories.length === 0 || exporting}
            style={{ backgroundColor: accentColor }}
            className="text-white"
          >
            {exporting ? (
              <Loader2 size={18} className="animate-spin mr-2" />
            ) : (
              <Download size={18} className="mr-2" />
            )}
            Exportar ({selectedCategories.length})
          </Button>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {categories.map((category) => {
          const Icon = CATEGORY_ICONS[category.id] || FileText;
          const isSelected = selectedCategories.includes(category.id);
          const isExporting = exporting === category.id;

          return (
            <Card 
              key={category.id}
              className={`cursor-pointer transition-all hover:shadow-md border-2 ${
                isSelected ? 'border-current shadow-md' : 'border-gray-200 hover:border-gray-300'
              }`}
              style={{ 
                borderColor: isSelected ? accentColor : undefined,
              }}
              onClick={() => toggleCategory(category.id)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div 
                      className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0`}
                      style={{ 
                        backgroundColor: isSelected ? accentColor : `${accentColor}15`,
                        color: isSelected ? 'white' : accentColor
                      }}
                    >
                      <Icon size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{category.label}</h3>
                      <p className="text-sm text-gray-500 mt-1">{category.description}</p>
                    </div>
                  </div>
                  {isSelected && (
                    <CheckCircle2 size={20} style={{ color: accentColor }} className="shrink-0" />
                  )}
                </div>
                <div className="mt-4 pt-3 border-t border-gray-100 flex justify-end">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      exportPDF(category.id);
                    }}
                    disabled={isExporting}
                    className="text-gray-600 hover:text-gray-900"
                  >
                    {isExporting ? (
                      <Loader2 size={16} className="animate-spin mr-2" />
                    ) : (
                      <FileDown size={16} className="mr-2" />
                    )}
                    Exportar PDF
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Info Box */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="p-4">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <FileText size={18} style={{ color: accentColor }} />
            Informações sobre a Exportação
          </h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: accentColor }} />
              Os relatórios são gerados em formato PDF com a identidade visual da CRA Construtora
            </li>
            <li className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: accentColor }} />
              Todos os dados são exportados em tabelas organizadas e de fácil leitura
            </li>
            <li className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: accentColor }} />
              O download inicia automaticamente após a geração do arquivo
            </li>
            <li className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: accentColor }} />
              Selecione múltiplas categorias e clique em "Exportar" para baixar todos de uma vez
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
