import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";

/**
 * Input numérico decimal no padrão brasileiro (1.234,56) — SEM prefixo R$.
 * Usado para porcentagens, quantidades, horas, estoque, alíquotas, etc.
 * - Prop `value`: número ou string numérica.
 * - Prop `onChange(numericValue)`: callback SEMPRE recebe number (float).
 * - Aceita vírgula OU ponto durante a digitação; salva sempre como float.
 *
 * Exemplo:
 *   <DecimalInput value={formData.aliquota} onChange={(v) => setFormData({...formData, aliquota: v})} />
 */
export function DecimalInput({ value, onChange, placeholder = "0,00", className, decimals = 2, ...rest }) {
  const numToDisplay = (v) => {
    if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "";
    const num = Number(v);
    if (Number.isNaN(num)) return "";
    return num.toLocaleString("pt-BR", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  };

  const [display, setDisplay] = useState(numToDisplay(value));
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!editing) setDisplay(numToDisplay(value));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, editing]);

  const handleChange = (e) => {
    setEditing(true);
    let raw = e.target.value;
    // Mantém apenas dígitos, vírgula e ponto
    raw = raw.replace(/[^\d.,]/g, "");
    setDisplay(raw);

    // Para o backend: troca vírgula por ponto e remove pontos de milhar
    // Se houver vários separadores, considera o último como decimal
    const lastDot = raw.lastIndexOf(".");
    const lastComma = raw.lastIndexOf(",");
    const lastSep = Math.max(lastDot, lastComma);
    let normalized;
    if (lastSep === -1) {
      normalized = raw;
    } else {
      const intPart = raw.slice(0, lastSep).replace(/[.,]/g, "");
      const decPart = raw.slice(lastSep + 1).replace(/[.,]/g, "");
      normalized = decPart ? `${intPart}.${decPart}` : intPart;
    }
    const num = parseFloat(normalized);
    onChange?.(Number.isNaN(num) ? 0 : num);
  };

  const handleBlur = () => {
    setEditing(false);
    setDisplay(numToDisplay(value));
  };

  return (
    <Input
      type="text"
      inputMode="decimal"
      value={display}
      onChange={handleChange}
      onBlur={handleBlur}
      placeholder={placeholder}
      className={className}
      {...rest}
    />
  );
}

export default DecimalInput;
