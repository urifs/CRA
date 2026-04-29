import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";

/**
 * Input monetário no padrão brasileiro (R$ 1.234,56).
 * - Prop `value`: número (float) ou string numérica vinda do backend.
 * - Prop `onChange(numericValue)`: callback recebe SEMPRE um number (float).
 * - O componente formata visualmente conforme o usuário digita.
 *
 * Exemplo:
 *   <MoneyInput value={formData.valor} onChange={(v) => setFormData({...formData, valor: v})} />
 */
export function MoneyInput({ value, onChange, placeholder = "R$ 0,00", className, prefix = "R$ ", ...rest }) {
  const numToDisplay = (v) => {
    if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "";
    const num = Number(v);
    const fixed = num.toFixed(2);
    const [intPart, decPart] = fixed.split(".");
    const intFmt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `${prefix}${intFmt},${decPart}`;
  };

  const [display, setDisplay] = useState(numToDisplay(value));

  // Sincroniza com mudanças externas (ex: openModal carregando dados)
  useEffect(() => {
    setDisplay(numToDisplay(value));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const handleChange = (e) => {
    // Mantém só dígitos. O usuário pode digitar 12345 → R$ 123,45
    const digits = e.target.value.replace(/\D/g, "");
    if (digits === "") {
      setDisplay("");
      onChange?.(0);
      return;
    }
    const cents = parseInt(digits, 10);
    const num = cents / 100;
    setDisplay(numToDisplay(num));
    onChange?.(num);
  };

  return (
    <Input
      type="text"
      inputMode="numeric"
      value={display}
      onChange={handleChange}
      placeholder={placeholder}
      className={className}
      {...rest}
    />
  );
}

export default MoneyInput;
