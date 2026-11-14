import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";

export function PageHeader({ title, desc, actions }: { title: string; desc?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-xl sm:text-2xl font-semibold text-foreground">{title}</h1>
        {desc && <p className="mt-1 text-sm text-muted-foreground">{desc}</p>}
      </div>
      {actions}
    </div>
  );
}
export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-lg border bg-card p-5 ${className}`}>{children}</div>;
}
export function Loading({ label = "Loading…" }: { label?: string }) {
  return <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />{label}</div>;
}
export function ErrorBox({ error }: { error: unknown }) {
  if (!error) return null;
  return <div className="rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">{error instanceof Error ? error.message : String(error)}</div>;
}
export function Empty({ children }: { children: ReactNode }) {
  return <div className="py-8 text-center text-sm text-muted-foreground">{children}</div>;
}
export function StatusBadge({ status }: { status?: string }) {
  return <span className="inline-flex rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">{status || "—"}</span>;
}
export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block space-y-1.5"><span className="text-sm font-medium text-foreground">{label}</span>{children}</label>;
}
export function Json({ value }: { value: unknown }) {
  return <pre className="max-h-72 overflow-auto rounded-md bg-muted p-3 text-xs text-foreground">{JSON.stringify(value, null, 2)}</pre>;
}
