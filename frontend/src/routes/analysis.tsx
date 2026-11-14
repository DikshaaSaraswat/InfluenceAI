import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, pick } from "@/lib/api";
import { InfluencerSelect } from "@/components/app/InfluencerSelect";
import { Card, PageHeader, ErrorBox, Field, Json } from "@/components/app/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/analysis")({
  head: () => ({
    meta: [
      { title: "AI Analysis — InfluenceAI" },
      { name: "description", content: "Score how well an influencer fits your brand campaign." },
      { property: "og:title", content: "AI Analysis — InfluenceAI" },
      { property: "og:description", content: "Score how well an influencer fits your brand campaign." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" }
    ]
  }),
  component: Analysis,
});

function Analysis() {
  const qc = useQueryClient();

  const [id, setId] = useState("");
  const [f, setF] = useState({
    name: "",
    niche: "",
    campaign: ""
  });

  const [res, setRes] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setRes(null);

    try {
      const result = await api.analyzeInfluencer(id, f);
      setRes(result);
      await qc.invalidateQueries({ queryKey: ["influencers"] });
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  };

  const r = res?.analysis ?? res;

  const items: [string, any][] = r ? [
    ["Relevance score", pick(r, "relevance_score", "score")],
    ["Category", pick(r, "category", "relevance_category")],
    ["Summary", pick(r, "summary")],
    ["Reason", pick(r, "reason", "reasoning")],
    ["Recommendation", pick(r, "recommendation")],
  ] : [];

  return (
    <div>
      <PageHeader
        title="AI Analysis"
        desc="Run the backend AI relevance analysis for an influencer."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <form onSubmit={submit} className="space-y-4">
            <Field label="Influencer">
              <InfluencerSelect value={id} onChange={setId} />
            </Field>

            <Field label="Brand name">
              <Input
                required
                value={f.name}
                onChange={(e) => setF({ ...f, name: e.target.value })}
              />
            </Field>

            <Field label="Brand niche">
              <Input
                required
                value={f.niche}
                onChange={(e) => setF({ ...f, niche: e.target.value })}
              />
            </Field>

            <Field label="Campaign description">
              <Textarea
                rows={5}
                required
                value={f.campaign}
                onChange={(e) => setF({ ...f, campaign: e.target.value })}
              />
            </Field>

            <ErrorBox error={err} />

            <Button type="submit" disabled={!id || busy}>
              {busy ? "Analyzing…" : "Analyze"}
            </Button>
          </form>
        </Card>

        <Card>
          <h2 className="mb-3 font-semibold">Result</h2>

          {!res ? (
            <p className="text-sm text-muted-foreground">
              Results from the backend will appear here.
            </p>
          ) : (
            <div className="space-y-3">
              {items.map(([k, v]) => (
                <div key={k}>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">
                    {k}
                  </p>
                  <p className={k === "Relevance score" ? "text-3xl font-semibold text-primary" : "text-sm"}>
                    {v ?? "—"}
                  </p>
                </div>
              ))}

              <details>
                <summary className="cursor-pointer text-sm text-muted-foreground">
                  Raw response
                </summary>
                <Json value={res} />
              </details>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
