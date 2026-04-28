import React from "react";
import { Input } from "./ui/input";
import { formatDate, parseDate, formatDateFromISO } from "../utils/masks";

/**
 * Input de data com máscara dd/mm/aaaa.
 *
 * - Internamente exibe o valor formatado como "dd/mm/aaaa"
 * - Externamente (onChange) expõe o valor no padrão ISO "aaaa-mm-dd"
 *   (compatível com `<Input type="date" />` que o restante do app usa)
 *
 * Props:
 *  - value: string ISO (aaaa-mm-dd) ou dd/mm/aaaa
 *  - onChange: (isoString) => void
 *  - ...rest: demais props repassadas para o Input
 */
export const MaskedDateInput = React.forwardRef(function MaskedDateInput(
  { value, onChange, placeholder = "dd/mm/aaaa", className = "", ...rest },
  ref
) {
  const display = value ? formatDateFromISO(value) : "";

  const handleChange = (e) => {
    const raw = e.target.value;
    const masked = formatDate(raw);
    // Quando completar 8 dígitos, converte para ISO; caso contrário, envia o que tem
    const numbers = masked.replace(/\D/g, "");
    if (numbers.length === 8) {
      onChange?.(parseDate(masked));
    } else if (numbers.length === 0) {
      onChange?.("");
    } else {
      // valor parcial: mantém em formato BR para o usuário continuar digitando
      onChange?.(masked);
    }
  };

  return (
    <Input
      ref={ref}
      type="text"
      inputMode="numeric"
      maxLength={10}
      value={display}
      onChange={handleChange}
      placeholder={placeholder}
      className={className}
      {...rest}
    />
  );
});

export default MaskedDateInput;
