import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, inf } from "@/lib/api";
import { useInfluencers } from "@/components/app/InfluencerSelect";
import { Card, PageHeader, Loading, ErrorBox, Empty, StatusBadge, Field, Json } from "@/components/app/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export const Route = createFileRoute("/influencers")({
  head: () => ({
    meta: [
      { title: "Influencers — InfluenceAI" },
      { name: "description", content: "Browse, filter and add Instagram influencers." },
      { property: "og:title", content: "Influencers — InfluenceAI" },
      { property: "og:description", content: "Browse, filter and add Instagram influencers." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" }
    ]
  }),
  component: Influencers,
});

const STATUSES = [
  "New Lead",
  "Email Available",
  "Email Sent",
  "Follow-up Due",
  "Replied",
  "Interested",
  "Not Interested",
  "Collaboration Confirmed"
];

function Influencers() {
  const q = useInfluencers();
  const [search, setSearch] = useState("");
  const [niche, setNiche] = useState("");
  const [loc, setLoc] = useState("");
  const [minF, setMinF] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [selId, setSelId] = useState<string | null>(null);

  const sel = (q.data ?? []).find((x) => String(inf.id(x)) === selId) ?? null;

  const rows = useMemo(() => (q.data ?? []).filter((x) => {
    const s = search.toLowerCase();
    return (!s || `${inf.name(x)} ${inf.username(x)} ${inf.email(x)}`.toLowerCase().includes(s))
      && (!niche || inf.niche(x).toLowerCase().includes(niche.toLowerCase()))
      && (!loc || inf.location(x).toLowerCase().includes(loc.toLowerCase()))
      && (!minF || inf.followers(x) >= Number(minF));
  }), [q.data, search, niche, loc, minF]);

  return (
    <div>
      <PageHeader
        title="Influencers"
        desc="All influencers stored in your CRM."
        actions={
          <Button onClick={() => setShowAdd(!showAdd)}>
            {showAdd ? "Close" : "Add influencer"}
          </Button>
        }
      />

      {showAdd && <AddForm onDone={() => setShowAdd(false)} />}

      <div className="mb-4 grid gap-3 sm:grid-cols-4">
        <Input
          placeholder="Search name, username, email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Input
          placeholder="Niche"
          value={niche}
          onChange={(e) => setNiche(e.target.value)}
        />
        <Input
          placeholder="Location"
          value={loc}
          onChange={(e) => setLoc(e.target.value)}
        />
        <Input
          type="number"
          placeholder="Min followers"
          value={minF}
          onChange={(e) => setMinF(e.target.value)}
        />
      </div>

      <ErrorBox error={q.error} />

      <Card className="overflow-x-auto p-0">
        {q.isLoading ? (
          <div className="px-5"><Loading /></div>
        ) : q.error ? (
          <Empty>Influencers are unavailable until the backend connection is restored.</Empty>
        ) : rows.length === 0 ? (
          <Empty>No influencers found.</Empty>
        ) : (
          <table className="w-full min-w-[560px] text-sm">
            <thead className="border-b bg-muted/50 text-left text-muted-foreground">
              <tr>
                {["Name", "Username", "Niche", "Followers", "Email", "Status", ""].map((h) => (
                  <th key={h} className="px-4 py-2.5 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {rows.map((x) => (
                <tr key={inf.id(x)}>
                  <td className="px-4 py-2.5 font-medium">{inf.name(x)}</td>
                  <td className="px-4 py-2.5">@{inf.username(x)}</td>
                  <td className="px-4 py-2.5">{inf.niche(x)}</td>
                  <td className="px-4 py-2.5">{inf.followers(x).toLocaleString()}</td>
                  <td className="px-4 py-2.5">{inf.email(x) || "—"}</td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={inf.status(x)} />
                  </td>
                  <td className="px-4 py-2.5">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelId(String(inf.id(x)))}
                    >
                      View
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Dialog open={!!sel} onOpenChange={(o) => !o && setSelId(null)}>
        <DialogContent className="max-h-[90vh] max-w-lg overflow-y-auto">
          {sel && <Details x={sel} onClose={() => setSelId(null)} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AddForm({ onDone }: { onDone: () => void }) {
  const qc = useQueryClient();

  const [f, setF] = useState({
    name: "",
    instagram_username: "",
    niche: "",
    location: "",
    followers: "",
    email: "",
    profile_url: ""
  });

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);

    try {
      const { instagram_username, ...rest } = f;

      const body: Record<string, unknown> = {
        ...rest,
        username: instagram_username,
        followers: f.followers ? Number(f.followers) : 0
      };

      Object.keys(body).forEach((k) => {
        if (body[k] === "") delete body[k];
      });

      await api.createInfluencer(body);
      await qc.invalidateQueries({ queryKey: ["influencers"] });
      onDone();
    } catch (e) {
      setErr(e);
    } finally {
      setBusy(false);
    }
  };

  const fields: [keyof typeof f, string, string?][] = [
    ["name", "Name"],
    ["instagram_username", "Instagram username"],
    ["niche", "Niche"],
    ["location", "Location"],
    ["followers", "Followers", "number"],
    ["email", "Email", "email"],
    ["profile_url", "Profile URL"]
  ];

  return (
    <Card className="mb-6">
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
        {fields.map(([k, l, t]) => (
          <Field key={k} label={l}>
            <Input
              type={t ?? "text"}
              required={["name", "instagram_username", "niche", "location", "followers"].includes(k)}
              value={f[k]}
              onChange={(e) => setF({ ...f, [k]: e.target.value })}
            />
          </Field>
        ))}

        <div className="sm:col-span-2 space-y-3">
          <ErrorBox error={err} />
          <Button type="submit" disabled={busy}>
            {busy ? "Saving…" : "Save influencer"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function Details({ x, onClose }: { x: any; onClose: () => void }) {
  const qc = useQueryClient();
  const id = inf.id(x);

  const [status, setStatus] = useState(inf.status(x));
  const [email, setEmail] = useState(inf.email(x));
  const [url, setUrl] = useState(String(x.profile_url ?? ""));
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState<unknown>(null);
  const [msg, setMsg] = useState("");

  const run = async (name: string, fn: () => Promise<any>, ok: string) => {
    setBusy(name);
    setErr(null);
    setMsg("");

    try {
      await fn();
      await qc.invalidateQueries({ queryKey: ["influencers"] });
      setMsg(ok);
    } catch (e) {
      setErr(e);
    } finally {
      setBusy("");
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>
          {inf.name(x)}{" "}
          <span className="text-muted-foreground font-normal">
            @{inf.username(x)}
          </span>
        </DialogTitle>
      </DialogHeader>

      <div className="space-y-4">
        <Field label="Status">
          <div className="flex flex-col gap-2 sm:flex-row">
            <select
              className="h-9 flex-1 rounded-md border border-input bg-background px-3 text-sm"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              {[...new Set([status, ...STATUSES])].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>

            <Button
              variant="outline"
              disabled={!!busy}
              onClick={() => run("status", () => api.updateStatus(id, status), "Status updated.")}
            >
              {busy === "status" ? "Updating…" : "Update"}
            </Button>
          </div>
        </Field>

        <Field label="Email">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input value={email} onChange={(e) => setEmail(e.target.value)} />
            <Button
              variant="outline"
              disabled={!!busy}
              onClick={() => run("email", () => api.updateEmail(id, email), "Email updated.")}
            >
              {busy === "email" ? "Updating…" : "Update"}
            </Button>
          </div>
        </Field>

        <Field label="Profile URL">
          <div className="flex flex-col gap-2 sm:flex-row">
            <Input value={url} onChange={(e) => setUrl(e.target.value)} />
            <Button
              variant="outline"
              disabled={!!busy}
              onClick={() => run("url", () => api.updateProfileUrl(id, url), "Profile URL updated.")}
            >
              {busy === "url" ? "Updating…" : "Update"}
            </Button>
          </div>
        </Field>

        <ErrorBox error={err} />
        {msg && <p className="text-sm text-primary">{msg}</p>}

        <details>
          <summary className="cursor-pointer text-sm text-muted-foreground">
            All fields
          </summary>
          <Json value={x} />
        </details>

        <Button variant="ghost" onClick={onClose}>Close</Button>
      </div>
    </>
  );
}
