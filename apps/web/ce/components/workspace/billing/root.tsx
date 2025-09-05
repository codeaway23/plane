import { observer } from "mobx-react";
// local imports
import { BillingDashboard } from "./billing-dashboard";

export const BillingRoot = observer(() => {
  return (
    <section className="relative size-full flex flex-col overflow-y-auto scrollbar-hide">
      <BillingDashboard />
    </section>
  );
});
