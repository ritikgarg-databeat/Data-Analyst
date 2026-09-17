import { PageHeader } from "@/components/shared/page-header";
import { MetricsLibrary } from "@/components/features/metrics/metrics-library";

export default function MetricsPage() {
  return (
    <div>
      <PageHeader title="Metrics Library" subtitle="A reference library of the business and product metrics analysts own." />
      <MetricsLibrary />
    </div>
  );
}
