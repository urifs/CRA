import { Card, CardContent } from "@/components/ui/card";
import { FileText, AlertTriangle } from "lucide-react";

export default function NFEPage() {
  return (
    <div data-testid="nfe-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Notas Fiscais Eletrônicas</h1>
          <p className="text-gray-500 mt-1">Emissão e gerenciamento de NF-e</p>
        </div>
      </div>

      {/* Coming Soon */}
      <Card>
        <CardContent className="py-16 text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="text-[#D4A000]" size={32} />
          </div>
          <h2 className="text-xl font-bold text-black mb-2">Módulo de NF-e</h2>
          <p className="text-gray-500 mb-4 max-w-md mx-auto">
            A emissão de Notas Fiscais Eletrônicas requer integração com a SEFAZ e certificado digital A1.
          </p>
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 max-w-md mx-auto">
            <div className="flex items-center gap-2 text-[#E31A1A]">
              <AlertTriangle size={20} />
              <span className="font-medium">Funcionalidade em desenvolvimento</span>
            </div>
            <p className="text-sm text-[#E31A1A] mt-1">
              Para emitir NF-e, será necessário configurar o certificado digital e dados fiscais da empresa.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
