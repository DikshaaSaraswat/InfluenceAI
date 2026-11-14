import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api, asList, inf, pick } from "@/lib/api";
import { useInfluencers } from "@/components/app/InfluencerSelect";
import { Card, PageHeader, Loading, ErrorBox, Empty, StatusBadge } from "@/components/app/ui";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Dashboard — InfluenceAI" }, { name: "description", content: "Overview of influencers, leads, outreach and follow-ups." }, { property: "og:title", content: "Dashboard — InfluenceAI" }, { property: "og:description", content: "Overview of influencers, leads, outreach and follow-ups." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary" }] }),
  component: Dashboard,
});

function Dashboard() {
  const i = useInfluencers();
  const f = useQuery({ queryKey: ["followups"], queryFn: async () => asList(await api.listFollowups()) });
  const list = i.data ?? [];
  const st = (x: any) => inf.status(x).toLowerCase();
  const stats = [
    { label: "Total influencers", value: list.length },
    { label: "New leads", value: list.filter((x) => st(x) === "new" || st(x) === "lead").length },
    { label: "Emails sent", value: list.filter((x) => /sent|contacted|replied/.test(st(x))).length },
    { label: "Follow-ups due", value: f.data ? f.data.filter((x) => /due/.test(String(pick(x, "status") ?? "").toLowerCase())).length : "—" },
  ];
  return (
    <div>
      <PageHeader title="Dashboard" desc="Your outreach pipeline at a glance." />
      <ErrorBox error={i.error} />
      <div className="my-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s) => <Card key={s.label}><p className="text-sm text-muted-foreground">{s.label}</p><p className="mt-2 text-3xl font-semibold">{i.isLoading ? "…" : i.error ? "—" : s.value}</p></Card>)}
      </div>
      {f.error && <p className="mb-4 text-xs text-muted-foreground">Follow-ups unavailable: {(f.error as Error).message}</p>}
      <Card>
        <h2 className="mb-3 font-semibold">Recent influencer activity</h2>
        {i.isLoading ? <Loading /> : i.error ? <Empty>Recent activity is unavailable until the backend connection is restored.</Empty> : list.length === 0 ? <Empty>No influencers yet. <Link to="/influencers" className="text-primary underline">Add one</Link>.</Empty> : (
          <ul className="divide-y">
            {[...list].reverse().slice(0, 8).map((x) => (
              <li key={inf.id(x)} className="flex items-center justify-between py-2.5 text-sm">
                <span><span className="font-medium">{inf.name(x)}</span> <span className="text-muted-foreground">@{inf.username(x)} · {inf.niche(x)}</span></span>
                <StatusBadge status={inf.status(x)} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
