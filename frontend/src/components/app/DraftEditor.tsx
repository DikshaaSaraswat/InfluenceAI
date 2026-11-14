import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ErrorBox, Field } from "./ui";
import { draftOf } from "@/lib/api";

type Draft = { subject: string; body: string };

/** Edit / save / approve / send a draft. Sending is always a manual, confirmed action. */
export function DraftEditor({ initial, onSave, onApprove, onSend, onDone }: {
  initial: any;
  onSave: (d: Draft) => Promise<any>;
  onApprove: () => Promise<any>;
  onSend: () => Promise<any>;
  onDone?: () => void;
}) {
  const [d, setD] = useState<Draft>(draftOf(initial));
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const [msg, setMsg] = useState("");
  useEffect(() => setD(draftOf(initial)), [initial]);

  const run = async (name: string, fn: () => Promise<any>, ok: string) => {
    setBusy(name); setErr(null); setMsg("");
    try { await fn(); setMsg(ok); onDone?.(); } catch (e) { setErr(e); } finally { setBusy(null); }
  };

  return (
    <div className="space-y-4">
      <Field label="Subject"><Input value={d.subject} onChange={(e) => setD({ ...d, subject: e.target.value })} /></Field>
      <Field label="Body"><Textarea rows={10} value={d.body} onChange={(e) => setD({ ...d, body: e.target.value })} /></Field>
      <ErrorBox error={err} />
      {msg && <p className="text-sm text-primary">{msg}</p>}
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" disabled={!!busy} onClick={() => run("save", () => onSave(d), "Draft saved.")}>{busy === "save" ? "Saving…" : "Save draft"}</Button>
        <Button variant="secondary" disabled={!!busy} onClick={() => run("approve", async () => { await onSave(d); return onApprove(); }, "Draft approved.")}>{busy === "approve" ? "Approving…" : "Approve"}</Button>
        <Button disabled={!!busy} onClick={() => { if (confirm("Send this email now?")) run("send", onSend, "Email sent."); }}>{busy === "send" ? "Sending…" : "Send"}</Button>
      </div>
      <p className="text-xs text-muted-foreground">Emails are only sent when you click Send. The backend may require approval first.</p>
    </div>
  );
}
