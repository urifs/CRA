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
