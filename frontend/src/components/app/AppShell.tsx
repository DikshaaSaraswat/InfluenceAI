import { Link } from "@tanstack/react-router";
import { useState, type ReactNode } from "react";
import { LayoutDashboard, Users, Sparkles, Mail, CalendarClock, MessageSquareReply, Menu } from "lucide-react";
import { Sheet, SheetContent, SheetTitle, SheetDescription, SheetTrigger } from "@/components/ui/sheet";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/influencers", label: "Influencers", icon: Users },
  { to: "/analysis", label: "AI Analysis", icon: Sparkles },
  { to: "/outreach", label: "Email Outreach", icon: Mail },
  { to: "/followups", label: "Follow-ups", icon: CalendarClock },
  { to: "/replies", label: "Replies", icon: MessageSquareReply },
] as const;

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Main" className="space-y-1 px-3">
      {nav.map(({ to, label, icon: Icon }) => (
        <Link key={to} to={to} onClick={onNavigate} activeOptions={{ exact: to === "/" }}
          className="flex min-h-11 items-center gap-3 rounded-md px-3 py-2 text-sm text-sidebar-foreground outline-none hover:bg-sidebar-accent focus-visible:ring-2 focus-visible:ring-ring"
          activeProps={{ className: "bg-sidebar-accent font-medium text-sidebar-primary", "aria-current": "page" }}>
          <Icon className="h-4 w-4" aria-hidden="true" />{label}
        </Link>
      ))}
    </nav>
  );
}

const Brand = () => <span className="text-lg font-semibold text-foreground">Influence<span className="text-primary">AI</span></span>;

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [announce, setAnnounce] = useState("");
  const toggle = (o: boolean) => { setOpen(o); setAnnounce(o ? "Navigation menu opened" : "Navigation menu closed"); };
  return (
    <div className="flex min-h-dvh w-full bg-background">
      <div role="status" aria-live="polite" className="sr-only">{announce}</div>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:ring-2 focus:ring-ring">Skip to content</a>
      <aside className="hidden w-60 shrink-0 border-r bg-sidebar md:sticky md:top-0 md:block md:h-dvh">
        <div className="px-5 py-5"><Brand /></div>
        <NavLinks />
      </aside>
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-10 flex h-12 items-center border-b bg-background px-2 md:hidden">
          <Sheet open={open} onOpenChange={toggle}>
            <SheetTrigger aria-label={open ? "Close navigation menu" : "Open navigation menu"} aria-controls="mobile-nav" className="grid min-h-11 min-w-11 place-items-center rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Menu className="h-5 w-5" aria-hidden="true" />
            </SheetTrigger>
            <SheetContent id="mobile-nav" aria-label="Navigation menu" side="left" className="w-64 bg-sidebar p-0">
              <div className="px-5 py-5"><SheetTitle asChild><h2><Brand /></h2></SheetTitle></div>
              <SheetDescription className="sr-only">Site navigation</SheetDescription>
              <NavLinks onNavigate={() => toggle(false)} />
            </SheetContent>
          </Sheet>
          <span className="ml-2 font-semibold">InfluenceAI</span>
        </header>
        <main id="main" tabIndex={-1} className="mx-auto max-w-6xl p-4 outline-none md:p-8">{children}</main>
      </div>
    </div>
  );
}
