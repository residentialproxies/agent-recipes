import AgentDetail from "./agent-detail";

export function generateStaticParams() {
  return [];
}

interface PageProps {
  params: {
    id: string;
  };
}

export default function AgentDetailPage({ params }: PageProps) {
  return <AgentDetail id={params.id} />;
}
