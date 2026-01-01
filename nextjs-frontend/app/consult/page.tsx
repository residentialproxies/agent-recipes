import { fetchCapabilities } from "@/lib/api";
import ConsultForm from "@/components/ConsultForm";

export default async function ConsultPage() {
  const caps = await fetchCapabilities().catch(() => [] as string[]);
  return (
    <>
      <div className="hero">
        <h1>Consult WebManus</h1>
        <p>
          Tell us the task you want automated. Get 1–3 AI workers and a short
          workflow-focused explanation.
        </p>
      </div>
      <ConsultForm capabilities={caps} />
    </>
  );
}
