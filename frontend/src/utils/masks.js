// Máscaras de formatação automática para CPF, CNPJ, CEP e Telefone

export const formatCPF = (value) => {
  if (!value) return "";
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, "");
  // Limita a 11 dígitos
  const limited = numbers.slice(0, 11);
  // Aplica a máscara: 000.000.000-00
  return limited
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
};

export const formatCNPJ = (value) => {
  if (!value) return "";
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, "");
  // Limita a 14 dígitos
  const limited = numbers.slice(0, 14);
  // Aplica a máscara: 00.000.000/0000-00
  return limited
    .replace(/(\d{2})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1/$2")
    .replace(/(\d{4})(\d{1,2})$/, "$1-$2");
};

export const formatCPFouCNPJ = (value) => {
  if (!value) return "";
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, "");
  // Se tem até 11 dígitos, formata como CPF
  if (numbers.length <= 11) {
    return formatCPF(value);
  }
  // Se tem mais de 11, formata como CNPJ
  return formatCNPJ(value);
};

export const formatCEP = (value) => {
  if (!value) return "";
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, "");
  // Limita a 8 dígitos
  const limited = numbers.slice(0, 8);
  // Aplica a máscara: 00000-000
  return limited.replace(/(\d{5})(\d{1,3})$/, "$1-$2");
};

export const formatTelefone = (value) => {
  if (!value) return "";
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, "");
  // Limita a 11 dígitos (celular com DDD)
  const limited = numbers.slice(0, 11);
  // Aplica a máscara
  if (limited.length <= 10) {
    // Telefone fixo: (00) 0000-0000
    return limited
      .replace(/(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{4})(\d{1,4})$/, "$1-$2");
  }
  // Celular: (00) 00000-0000
  return limited
    .replace(/(\d{2})(\d)/, "($1) $2")
    .replace(/(\d{5})(\d{1,4})$/, "$1-$2");
};

// Função para remover formatação (útil para enviar ao backend)
export const removeFormat = (value) => {
  if (!value) return "";
  return value.replace(/\D/g, "");
};

// Máscara para valores monetários (R$ 1.500,00)
export const formatCurrency = (value) => {
  if (!value) return "";
  
  // Remove tudo que não é número
  let numbers = value.toString().replace(/\D/g, "");
  
  // Limita a 15 dígitos (trilhões)
  numbers = numbers.slice(0, 15);
  
  if (numbers === "") return "";
  
  // Converte para centavos e depois para reais
  const cents = parseInt(numbers, 10);
  const reais = (cents / 100).toFixed(2);
  
  // Formata com separadores brasileiros
  const parts = reais.split(".");
  const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const decPart = parts[1];
  
  return `R$ ${intPart},${decPart}`;
};

// Função para extrair valor numérico de string formatada como moeda
export const parseCurrency = (value) => {
  if (!value) return 0;
  // Remove "R$", espaços, pontos de milhar
  const cleaned = value.toString().replace(/R\$\s?/g, "").replace(/\./g, "").replace(",", ".");
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
};

// Máscara para data (dd/mm/aaaa)
export const formatDate = (value) => {
  if (!value) return "";
  
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, "");
  
  // Limita a 8 dígitos
  const limited = numbers.slice(0, 8);
  
  // Aplica a máscara: dd/mm/aaaa
  if (limited.length <= 2) {
    return limited;
  } else if (limited.length <= 4) {
    return `${limited.slice(0, 2)}/${limited.slice(2)}`;
  } else {
    return `${limited.slice(0, 2)}/${limited.slice(2, 4)}/${limited.slice(4)}`;
  }
};

// Função para converter data formatada (dd/mm/aaaa) para ISO (aaaa-mm-dd)
export const parseDate = (value) => {
  if (!value) return "";
  const numbers = value.replace(/\D/g, "");
  if (numbers.length !== 8) return "";
  const day = numbers.slice(0, 2);
  const month = numbers.slice(2, 4);
  const year = numbers.slice(4, 8);
  return `${year}-${month}-${day}`;
};

// Função para converter ISO (aaaa-mm-dd) para formato brasileiro (dd/mm/aaaa)
export const formatDateFromISO = (isoDate) => {
  if (!isoDate) return "";
  // Se já está no formato dd/mm/aaaa, retorna como está
  if (isoDate.includes("/")) return isoDate;
  // Se é ISO (aaaa-mm-dd)
  const parts = isoDate.split("-");
  if (parts.length !== 3) return isoDate;
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
};
