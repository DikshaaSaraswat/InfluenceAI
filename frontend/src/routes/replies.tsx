import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { api, pick } from "@/lib/api";
import { Card, PageHeader, ErrorBox, Loading, Empty, StatusBadge, Json } from "@/components/app/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export const Route = createFileRoute("/replies")({
  head: () => ({
    meta: [
      { title: "Reply Management — InfluenceAI" },
      { name: "description", content: "Review incoming replies with AI classification and suggested responses." },
    ],
  }),
  component: Replies,
});

function Replies() {
  const [syncInfo, setSyncInfo] = useState<any>(null);
  const [sel, setSel] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [lookup, setLookup] = useState("");
  const [replyText, setReplyText] = useState("");
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState<unknown>(null);
  const [msg, setMsg] = useState("");

  const d = detail?.reply ?? detail;

  useEffect(() => {
    setReplyText(
      String(pick(d, "suggested_reply", "suggested_response", "draft") ?? "")
    );
  }, [detail]);

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
    act("open", () => api.getReply(id), setDetail);
  };

  const saveDraft = () =>
    act(
      "save",
      () => api.updateReplyDraft(sel!, { suggested_reply: replyText }),
      () => setMsg("Suggested reply saved.")
    );

  const analyze = async () => {
    if (!sel) return;
    setBusy("an");
    setErr(null);
    setMsg("");

    try {
      await api.analyzeReply(sel);
      const updated = await api.getReply(sel);
      setDetail(updated);
      setMsg("Reply analyzed successfully.");
    } catch (e) {
      setErr(e);
    } finally {
      setBusy("");
    }
  };

  return (
    <div>
      <PageHeader
        title="Reply Management"
        desc="Sync incoming Gmail replies or open a reply using its ID."
        actions={
          <Button
            disabled={!!busy}
            onClick={() =>
              act("sync", () => api.syncReplies(), setSyncInfo)
            }
          >
            {busy === "sync" ? "Syncing…" : "Sync replies"}
          </Button>
        }
      />

      <ErrorBox error={err} />

      <div className="mt-4 grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (lookup.trim()) open(lookup.trim());
            }}
          >
            <Input
              placeholder="Open reply by ID"
              value={lookup}
              onChange={(e) => setLookup(e.target.value)}
            />
            <Button variant="outline" type="submit" disabled={!!busy}>
              Open
            </Button>
          </form>

          {busy === "sync" ? (
            <Loading />
          ) : syncInfo ? (
            <div className="space-y-3">
              <p className="text-sm font-medium">Gmail sync completed</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Replies found</p>
                  <p className="text-xl font-semibold">
                    {syncInfo.replies_found ?? 0}
                  </p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">New replies saved</p>
                  <p className="text-xl font-semibold">
                    {syncInfo.new_replies_saved ?? 0}
                  </p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                {syncInfo.message ?? "Sync completed."}
              </p>
              <Json value={syncInfo} />
            </div>
          ) : (
            <Empty>
              Click "Sync replies" to fetch incoming Gmail replies.
            </Empty>
          )}
        </Card>

        <Card>
          {!sel ? (
            <p className="text-sm text-muted-foreground">
              Enter a reply ID to review an incoming reply.
            </p>
          ) : busy === "open" ? (
            <Loading />
          ) : d ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">Reply #{sel}</h2>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!!busy}
                  onClick={analyze}
                >
                  {busy === "an" ? "Analyzing…" : "Analyze with AI"}
                </Button>
              </div>

              <div>
                <p className="text-xs uppercase text-muted-foreground">
                  Original message
                </p>
                <p className="whitespace-pre-wrap text-sm">
                  {pick(d, "body", "content", "message", "snippet") ?? "—"}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs uppercase text-muted-foreground">
                  Classification
                </span>
                <StatusBadge
                  status={pick(d, "classification", "category", "intent")}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Suggested reply
                </label>
                <Textarea
                  rows={8}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Generate or write a suggested reply..."
                />
              </div>

              {msg && (
                <p className="text-sm text-primary">{msg}</p>
              )}

              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  disabled={!!busy || !replyText.trim()}
                  onClick={saveDraft}
                >
                  {busy === "save" ? "Saving…" : "Save draft"}
                </Button>

                <Button
                  variant="secondary"
                  disabled={!!busy || !replyText.trim()}
                  onClick={() =>
                    act(
                      "approve",
                      async () => {
                        await api.updateReplyDraft(sel, {
                          suggested_reply: replyText,
                        });
                        return api.approveReply(sel);
                      },
                      () => setMsg("Reply approved.")
                    )
                  }
                >
                  {busy === "approve" ? "Approving…" : "Approve"}
                </Button>

                <Button
                  disabled={!!busy}
                  onClick={() => {
                    if (confirm("Send this reply now?")) {
                      act(
                        "send",
                        () => api.sendReply(sel),
                        () => setMsg("Reply sent.")
                      );
                    }
                  }}
                >
                  {busy === "send" ? "Sending…" : "Send"}
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">
                Replies require human approval before sending. Sending happens
                only when you explicitly click Send.
              </p>
            </div>
          ) : (
            <Empty>Reply details could not be loaded.</Empty>
          )}
        </Card>
      </div>
    </div>
  );
}
