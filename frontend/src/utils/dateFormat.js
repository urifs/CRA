/**
 * Helpers para formatação de datas em PT-BR sem o bug de timezone.
 *
 * O bug clássico: `new Date("2026-05-13")` em fuso BR é interpretado como UTC
 * meia-noite, virando 12/05/2026 quando exibido localmente. Estas funções
 * tratam strings `YYYY-MM-DD` como data local (sem hora UTC).
 */

/**
 * Formata uma data para `DD/MM/YYYY`.
 * Aceita:
 *  - string "YYYY-MM-DD"  → tratada como data local pura (sem timezone)
 *  - string ISO 8601 com hora ("YYYY-MM-DDTHH:mm:ss[Z|+/-HH:mm]") → respeita o fuso
 *  - Date object
 *  - null/undefined/"" → retorna fallback
 */
export function formatDateBR(value, fallback = "-") {
  if (value === null || value === undefined || value === "") return fallback;

  // Caso 1: string YYYY-MM-DD pura (sem hora)
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split("-");
    return `${d}/${m}/${y}`;
  }

  // Caso 2: string ISO com hora ou Date — usa toLocaleDateString
  try {
    const dt = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(dt.getTime())) return fallback;
    return dt.toLocaleDateString("pt-BR");
  } catch {
    return fallback;
  }
}

/**
 * Formata data + hora `DD/MM/YYYY HH:mm`. Aceita ISO 8601 com timezone.
 */
export function formatDateTimeBR(value, fallback = "-") {
  if (value === null || value === undefined || value === "") return fallback;
  try {
    const dt = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(dt.getTime())) return fallback;
    return dt.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return fallback;
  }
}
