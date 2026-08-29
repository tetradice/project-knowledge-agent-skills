import { describe, expect, it } from "vitest";
import { visibleOrders } from "../src/features/orders/order-list";

describe("orders", () => {
  it("hides cancelled orders", () => expect(visibleOrders([{id:"1",state:"cancelled",totalMinor:0}])).toEqual([]));
});
