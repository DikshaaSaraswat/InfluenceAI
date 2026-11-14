import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { InfluencerSelect } from "@/components/app/InfluencerSelect";
import { DraftEditor } from "@/components/app/DraftEditor";
import { Card, PageHeader, ErrorBox, Field, Loading } from "@/components/app/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/outreach")({
  head: () => ({
    meta: [
      { title: "Email Outreach — InfluenceAI" },
      { name: "description", content: "Generate, edit, approve and send personalized outreach emails." },
      { property: "og:title", content: "Email Outreach — InfluenceAI" },
      { property: "og:description", content: "Generate, edit, approve and send personalized outreach emails." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" }
    ]
  }),
  component: Outreach,
});

function Outreach() {
  const qc = useQueryClient();

  const [id, setId] = useState("");
  const [brand, setBrand] = useState({
    name: "",
    niche: "",
    campaign: ""
  });

  const [draft, setDraft] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<unknown>(null);

  const loadExistingDraft = async (influencerId: string) => {
    setLoading(true);
    setErr(null);
    setDraft(null);

    try {
      const result = await api.getDraftEmail(influencerId);
      setDraft(result);
    } catch (e) {
      const error = e as any;
      const isNotFound =
        error?.status === 404 ||
        error?.response?.status === 404 ||
        String(error?.message ?? error).includes("404");

      if (!isNotFound) {
        setErr(e);
      }
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    if (!id) return;

    await Promise.all([
      loadExistingDraft(id),
      qc.invalidateQueries({ queryKey: ["influencers"] }),
      qc.invalidateQueries({ queryKey: ["followups"] }),
    ]);
  };

  const generateDraft = async () => {
    if (!id) return;

    setLoading(true);
    setErr(null);
    setDraft(null);

    try {
      const result = await api.generateDraftEmail(id, brand);
      setDraft(result);
      await qc.invalidateQueries({ queryKey: ["influencers"] });
    } catch (e) {
      setErr(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setDraft(null);
    setErr(null);

    if (id) {
      void loadExistingDraft(id);
    }
  }, [id]);

  return (
    <div>
      <PageHeader
        title="Email Outreach"
        desc="Generate, edit, approve and send personalized outreach emails."
      />

      <Card className="mb-6 space-y-4">
        <Field label="Influencer">
          <InfluencerSelect value={id} onChange={setId} />
        </Field>

        <Field label="Brand name">
          <Input
            required
            placeholder="e.g. TechNova"
            value={brand.name}
            onChange={(e) => setBrand({ ...brand, name: e.target.value })}
          />
        </Field>

        <Field label="Brand niche">
          <Input
            required
            placeholder="e.g. Technology"
            value={brand.niche}
            onChange={(e) => setBrand({ ...brand, niche: e.target.value })}
          />
        </Field>

        <Field label="Campaign description">
          <Textarea
            required
            rows={4}
            placeholder="Describe the product and collaboration campaign..."
            value={brand.campaign}
            onChange={(e) => setBrand({ ...brand, campaign: e.target.value })}
          />
        </Field>

        <Button
          disabled={!id || loading || !brand.name.trim() || !brand.niche.trim() || !brand.campaign.trim()}
          onClick={generateDraft}
        >
          {loading ? "Generating…" : "Generate AI draft"}
        </Button>
      </Card>

      {loading && <Loading />}

      {err && !loading && (
        <div className="mb-4">
          <ErrorBox error={err} />
        </div>
      )}

      {draft && !loading && (
        <Card>
          <DraftEditor
            key={id}
            initial={draft}
            onSave={(d) => api.updateDraftEmail(id, d)}
            onApprove={() => api.approveEmail(id)}
            onSend={() => api.sendEmail(id)}
            onDone={() => {
              void refresh();
            }}
          />
        </Card>
      )}
    </div>
  );
}
