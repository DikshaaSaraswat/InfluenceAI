import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, asList, pick } from "@/lib/api";
import { DraftEditor } from "@/components/app/DraftEditor";
import { Card, PageHeader, ErrorBox, Loading, Empty, StatusBadge } from "@/components/app/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/followups")({
  head: () => ({
    meta: [
      { title: "Follow-ups — InfluenceAI" },
      { name: "description", content: "Manage scheduled follow-up emails for your outreach." },
      { property: "og:title", content: "Follow-ups — InfluenceAI" },
      { property: "og:description", content: "Manage scheduled follow-up emails for your outreach." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Followups,
});

const fid = (x: any) => pick(x, "id", "followup_id", "_id");

function Followups() {
  const q = useQuery({
    queryKey: ["followups"],
    queryFn: async () => asList(await api.listFollowups()),
  });

  const [sel, setSel] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState<unknown>(null);
  const [msg, setMsg] = useState("");

  const [brand, setBrand] = useState({
    name: "TechNova",
    niche: "Technology",
    campaign: "We are promoting an AI-powered productivity application designed for students and young professionals. We want to reach out to technology creators and explore an authentic collaboration.",
  });

  const act = async (
    name: string,
    fn: () => Promise<any>,
    after?: (r: any) => void
  ) => {
    setBusy(name);
    setErr(null);
    setMsg("");

    try {
      const r = await fn();
      after?.(r);
    } catch (e) {
      setErr(e);
    } finally {
      setBusy("");
    }
  };

  const open = (id: string) => {
    setSel(id);
    setDetail(null);
    setMsg("");

    act("open", async () => {
      const result = await api.getFollowup(id);
      return result?.followup ?? result;
    }, setDetail);
  };

  const refresh = () => {
    if (!sel) return;

    act("refresh", async () => {
      const [, updated] = await Promise.all([
        q.refetch(),
        api.getFollowup(sel),
      ]);

      return updated?.followup ?? updated;
    }, setDetail);
  };

  const generate = () => {
    if (!sel) return;

    if (!brand.name.trim() || !brand.niche.trim() || !brand.campaign.trim()) {
      setErr("Please fill in all brand details before generating the draft.");
      return;
    }

    act("gen", async () => {
      const created = await api.generateFollowup(sel, brand);
      await q.refetch();
      return created?.followup ?? created;
    }, setDetail);
  };

  return (
    <div>
      <PageHeader
        title="Follow-ups"
        desc="Manage scheduled follow-up emails."
        actions={
          <Button
            variant="outline"
            disabled={!!busy}
            onClick={() =>
              act("due", () => api.updateDueFollowups(), () => q.refetch())
            }
          >
            {busy === "due" ? "Updating…" : "Update due follow-ups"}
          </Button>
        }
      />

      <ErrorBox error={q.error} />
      <ErrorBox error={err} />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="overflow-x-auto p-0">
          {q.isLoading ? (
            <div className="px-5"><Loading /></div>
          ) : q.error ? (
            <Empty>Follow-ups are unavailable until the backend connection is restored.</Empty>
          ) : (q.data ?? []).length === 0 ? (
            <Empty>No follow-ups scheduled.</Empty>
          ) : (
            <table className="w-full min-w-[560px] text-sm">
              <thead className="border-b bg-muted/50 text-left text-muted-foreground">
                <tr>
                  {["Influencer", "#", "Scheduled", "Status", ""].map((h) => (
                    <th key={h} className="px-4 py-2.5 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>

              <tbody className="divide-y">
                {q.data!.map((x) => (
                  <tr
                    key={fid(x)}
                    className={String(fid(x)) === sel ? "bg-accent/50" : ""}
                  >
                    <td className="px-4 py-2.5">
                      {pick(x, "influencer_name", "name") ??
                        pick(x?.influencer, "name") ??
                        `#${pick(x, "influencer_id") ?? "—"}`}
                    </td>

                    <td className="px-4 py-2.5">
                      {pick(x, "sequence_number", "sequence", "step") ?? "—"}
                    </td>

                    <td className="px-4 py-2.5">
                      {String(
                        pick(x, "scheduled_date", "scheduled_at", "due_date") ?? "—"
                      ).slice(0, 16).replace("T", " ")}
                    </td>

                    <td className="px-4 py-2.5">
                      <StatusBadge status={pick(x, "status")} />
                    </td>

                    <td className="px-4 py-2.5">
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={!!busy}
                        onClick={() => open(String(fid(x)))}
                      >
                        Open
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card>
          {!sel ? (
            <p className="text-sm text-muted-foreground">
              Select a follow-up to view or edit its draft.
            </p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">Follow-up #{sel}</h2>

                <Button
                  size="sm"
                  variant="outline"
                  disabled={!!busy}
                  onClick={generate}
                >
                  {busy === "gen" ? "Generating…" : "Generate draft"}
                </Button>
              </div>

              <div className="space-y-3">
                <h3 className="text-sm font-medium">Brand details</h3>

                <div className="space-y-1">
                  <label className="text-sm">Brand name</label>
                  <Input
                    value={brand.name}
                    onChange={(e) =>
                      setBrand({ ...brand, name: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-sm">Brand niche</label>
                  <Input
                    value={brand.niche}
                    onChange={(e) =>
                      setBrand({ ...brand, niche: e.target.value })
                    }
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-sm">Campaign description</label>
                  <Textarea
                    rows={4}
                    value={brand.campaign}
                    onChange={(e) =>
                      setBrand({ ...brand, campaign: e.target.value })
                    }
                  />
                </div>
              </div>

              {busy === "open" || busy === "gen" ? (
                <Loading />
              ) : detail ? (
                <DraftEditor
                  key={sel}
                  initial={detail}
                  onSave={(d) => api.updateFollowupDraft(sel, d)}
                  onApprove={() => api.approveFollowup(sel)}
                  onSend={() => api.sendFollowup(sel)}
                  onDone={refresh}
                />
              ) : (
                <p className="text-sm text-muted-foreground">
                  Select a follow-up to view its draft or generate a new one.
                </p>
              )}

              {msg && (
                <p className="text-sm text-primary">{msg}</p>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
