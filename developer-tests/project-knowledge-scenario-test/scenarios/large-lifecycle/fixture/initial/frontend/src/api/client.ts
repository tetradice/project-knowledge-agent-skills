export const requiredHeaders = ["X-Tenant-Id"] as const;

export function orderPath(id: string): string {
  return `/v1/orders/${id}`;
}
