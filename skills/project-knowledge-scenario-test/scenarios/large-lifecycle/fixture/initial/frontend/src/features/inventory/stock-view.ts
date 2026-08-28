export function stockLabel(available: number, reserved: number): string {
  return `${available - reserved} available`;
}
