export type OrderSummary = { id: string; state: string; totalMinor: number };

export function visibleOrders(rows: OrderSummary[]): OrderSummary[] {
  return rows.filter((row) => row.state !== "cancelled");
}
