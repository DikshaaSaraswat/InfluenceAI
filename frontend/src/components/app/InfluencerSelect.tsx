import { useQuery } from "@tanstack/react-query";
import { api, asList, inf } from "@/lib/api";
import { ErrorBox } from "./ui";

export const useInfluencers = () => useQuery({ queryKey: ["influencers"], queryFn: async () => asList(await api.listInfluencers()) });

export function InfluencerSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const q = useInfluencers();
  if (q.error) return <ErrorBox error={q.error} />;
  return (
    <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={value} onChange={(e) => onChange(e.target.value)} disabled={q.isLoading}>
      <option value="">{q.isLoading ? "Loading influencers…" : "Select an influencer"}</option>
      {(q.data ?? []).map((i) => <option key={inf.id(i)} value={String(inf.id(i))}>{inf.name(i)} {inf.username(i) && `(@${inf.username(i)})`}</option>)}
    </select>
  );
}
