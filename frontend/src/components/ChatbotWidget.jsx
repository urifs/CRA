import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  MessageCircle, 
  X, 
  Send, 
  Loader2, 
  Bot, 
  User,
  Minimize2,
  Maximize2,
  Paperclip,
  FileText,
  Image as ImageIcon,
  File
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL;

// Hook para detectar mobile
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return isMobile;
};

// Função para formatar markdown para HTML
const formatMessage = (text) => {
  if (!text) return "";
  
  let formatted = text;
  
  // Converter **texto** para negrito
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // Converter *texto* para itálico (mas não se for lista)
  formatted = formatted.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>');
  
  // Converter listas com * no início da linha
  formatted = formatted.replace(/^\*\s+(.+)$/gm, '• $1');
  
  // Converter listas com - no início da linha  
  formatted = formatted.replace(/^-\s+(.+)$/gm, '• $1');
  
  // Converter ### para título
  formatted = formatted.replace(/^###\s+(.+)$/gm, '<div class="font-bold text-base mt-2 mb-1">$1</div>');
  
  // Converter ## para título maior
  formatted = formatted.replace(/^##\s+(.+)$/gm, '<div class="font-bold text-lg mt-2 mb-1">$1</div>');
  
  // Converter # para título principal
  formatted = formatted.replace(/^#\s+(.+)$/gm, '<div class="font-bold text-xl mt-2 mb-1">$1</div>');
  
  // Adicionar espaçamento em linhas vazias
  formatted = formatted.replace(/\n\n/g, '</p><p class="mt-2">');
  
  // Converter quebras de linha simples
  formatted = formatted.replace(/\n/g, '<br/>');
  
  return formatted;
};

// Componente para renderizar mensagem formatada
const FormattedMessage = ({ content, accentColor }) => {
  const formattedContent = formatMessage(content);
  
  return (
    <div 
      className="text-sm leading-relaxed"
      dangerouslySetInnerHTML={{ __html: formattedContent }}
      style={{ 
        '--accent-color': accentColor,
      }}
    />
  );
};

export default function ChatbotWidget({ module = "gerenciamento", accentColor = "#E31A1A", hasFab = false }) {
  const isMobile = useIsMobile();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Olá! Sou o assistente virtual do Sistema de Gerenciamento.

Tenho acesso a todas as informações da plataforma e posso ajudar com:

• Informações sobre máquinas e manutenções
• Status do estoque
• Dados financeiros (contas, OS, aluguéis)
• Estatísticas e relatórios

Como posso ajudar?`
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API}/api/chatbot/ask`,
        { message: userMessage, module },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: response.data.response 
      }]);
    } catch (error) {
      console.error("Erro no chatbot:", error);
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Posição do chatbot - acima da barra de navegação no mobile
  const bottomPosition = isMobile ? 'calc(90px + env(safe-area-inset-bottom))' : '24px';
  // Quando há FAB, posiciona o botão mais à esquerda no mobile
  const rightPosition = isMobile && hasFab && !isOpen ? 'calc(16px + 56px + 16px)' : (isMobile ? '16px' : '24px');

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed w-14 h-14 rounded-full shadow-lg z-40 flex items-center justify-center hover:scale-110 transition-transform"
        style={{ backgroundColor: accentColor, bottom: bottomPosition, right: rightPosition }}
        data-testid="chatbot-toggle-btn"
      >
        <MessageCircle size={24} className="text-white" />
      </Button>
    );
  }

  return (
    <Card 
      className={`fixed right-4 md:right-6 z-40 shadow-2xl border-gray-700 bg-gray-900 transition-all duration-300 ${
        isMinimized ? "w-72 h-14" : "w-[calc(100vw-32px)] md:w-96 h-[60vh] md:h-[500px] max-h-[500px]"
      }`}
      style={{ bottom: bottomPosition }}
      data-testid="chatbot-widget"
    >
      {/* Header */}
      <CardHeader 
        className="p-3 border-b border-gray-700 cursor-pointer flex flex-row items-center justify-between"
        style={{ backgroundColor: accentColor }}
        onClick={() => isMinimized && setIsMinimized(false)}
      >
        <div className="flex items-center gap-2">
          <Bot size={20} className="text-white" />
          <CardTitle className="text-sm font-medium text-white">
            Assistente Virtual
          </CardTitle>
        </div>
        <div className="flex items-center gap-1">
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-7 w-7 p-0 text-white hover:bg-white/20"
            onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}
          >
            {isMinimized ? <Maximize2 size={14} /> : <Minimize2 size={14} />}
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-7 w-7 p-0 text-white hover:bg-white/20"
            onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
          >
            <X size={14} />
          </Button>
        </div>
      </CardHeader>

      {!isMinimized && (
        <>
          {/* Messages */}
          <CardContent className="p-3 flex-1 overflow-y-auto flex flex-col gap-3 bg-gray-900" style={{ height: 'calc(100% - 110px)' }}>
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 ${
                    msg.role === "user"
                      ? "bg-gray-700 text-white"
                      : "bg-gray-800 text-gray-100 border border-gray-700"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {msg.role === "assistant" && (
                      <Bot size={16} className="mt-1 shrink-0" style={{ color: accentColor }} />
                    )}
                    <div className="flex-1 overflow-hidden">
                      {msg.role === "assistant" ? (
                        <FormattedMessage content={msg.content} accentColor={accentColor} />
                      ) : (
                        <p className="text-sm">{msg.content}</p>
                      )}
                    </div>
                    {msg.role === "user" && (
                      <User size={16} className="mt-1 shrink-0 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <Bot size={16} style={{ color: accentColor }} />
                    <Loader2 size={16} className="animate-spin text-gray-400" />
                    <span className="text-sm text-gray-400">Pensando...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </CardContent>

          {/* Input */}
          <div className="p-3 border-t border-gray-700 bg-gray-900">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua pergunta..."
                className="flex-1 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                disabled={isLoading}
                data-testid="chatbot-input"
              />
              <Button
                onClick={handleSend}
                disabled={!inputValue.trim() || isLoading}
                className="shrink-0"
                style={{ backgroundColor: accentColor }}
                data-testid="chatbot-send-btn"
              >
                {isLoading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Send size={18} />
                )}
              </Button>
            </div>
          </div>
        </>
      )}
    </Card>
  );
}
