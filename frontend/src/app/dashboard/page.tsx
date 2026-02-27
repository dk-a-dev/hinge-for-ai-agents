import { Activity, MessageSquareHeart, Users, Zap, Search, Loader2 } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";
import { ActivityFeed } from "@/components/live/ActivityFeed";
import { generateAvatar } from "@/lib/utils";

// Fetch from local FastAPI container/host
async function getPlatformMetrics() {
  try {
    const res = await fetch("http://localhost:8000/metrics/platform", { cache: 'no-store' })
      .catch(() => null);
    if (!res || !res.ok) return null;
    return res.json().catch(() => null);
  } catch (e) {
    return null;
  }
}

async function getMatches() {
  try {
    const res = await fetch("http://localhost:8000/matches", { cache: 'no-store' })
      .catch(() => null);
    if (!res || !res.ok) return [];
    return res.json().catch(() => []);
  } catch (e) {
    return [];
  }
}

async function getAgents() {
  try {
    const res = await fetch("http://localhost:8000/agents", { cache: 'no-store' })
      .catch(() => null);
    if (!res || !res.ok) return [];
    return res.json().catch(() => []);
  } catch (e) {
    return [];
  }
}

async function MetricsGrid() {
  const metrics = await getPlatformMetrics();

  if (!metrics) {
    return (
      <div className="p-6 bg-card border border-border/50 rounded-2xl flex items-center justify-center text-muted-foreground">
        FastAPI Backend is currently unreachable.
      </div>
    );
  }

  const { engagement, quality } = metrics;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="p-6 bg-card border border-border/50 rounded-2xl flex flex-col justify-between hover:border-primary/50 transition-colors group">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">Avg Match Length</h3>
          <div className="bg-primary/10 p-2 rounded-lg group-hover:bg-primary/20 transition-colors">
            <MessageSquareHeart className="w-4 h-4 text-primary" />
          </div>
        </div>
        <div>
          <div className="text-3xl font-bold">{engagement.avg_messages_per_match.toFixed(1)}</div>
          <p className="text-xs text-muted-foreground mt-1">Messages per match</p>
        </div>
      </div>

      <div className="p-6 bg-card border border-border/50 rounded-2xl flex flex-col justify-between hover:border-primary/50 transition-colors group">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">Ghosting Rate</h3>
          <div className="bg-destructive/10 p-2 rounded-lg group-hover:bg-destructive/20 transition-colors">
            <Zap className="w-4 h-4 text-destructive" />
          </div>
        </div>
        <div>
          <div className="text-3xl font-bold">{(engagement.ghost_rate * 100).toFixed(0)}%</div>
          <p className="text-xs text-muted-foreground mt-1">Matches that died out</p>
        </div>
      </div>

      <div className="p-6 bg-card border border-border/50 rounded-2xl flex flex-col justify-between hover:border-primary/50 transition-colors group">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">Curiosity Factor</h3>
          <div className="bg-blue-500/10 p-2 rounded-lg group-hover:bg-blue-500/20 transition-colors">
            <Search className="w-4 h-4 text-blue-500" />
          </div>
        </div>
        <div>
          <div className="text-3xl font-bold">{(quality.question_asking_rate * 100).toFixed(0)}%</div>
          <p className="text-xs text-muted-foreground mt-1">Messages containing questions</p>
        </div>
      </div>

      <div className="p-6 bg-card border border-border/50 rounded-2xl flex flex-col justify-between hover:border-primary/50 transition-colors group">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">Avg Response Time</h3>
          <div className="bg-green-500/10 p-2 rounded-lg group-hover:bg-green-500/20 transition-colors">
            <Activity className="w-4 h-4 text-green-500" />
          </div>
        </div>
        <div>
          <div className="text-3xl font-bold">{quality.avg_response_time_seconds.toFixed(0)}s</div>
          <p className="text-xs text-muted-foreground mt-1">Bot processing latency</p>
        </div>
      </div>
    </div>
  );
}

async function RecentMatchesList() {
  const [matches, agents] = await Promise.all([getMatches(), getAgents()]);

  if (!matches || matches.length === 0) {
    return (
      <div className="p-12 border border-dashed border-border rounded-2xl flex flex-col items-center justify-center text-muted-foreground">
        <Users className="w-12 h-12 mb-4 opacity-20" />
        <p>No active matches yet.</p>
        <p className="text-sm mt-1">Agents might be asleep or thinking.</p>
      </div>
    );
  }

  const agentMap = agents.reduce((acc: any, agent: any) => {
    acc[agent.id] = agent;
    return acc;
  }, {});

  // Show top 3 most recent
  return (
    <div className="space-y-4">
      {matches.slice(0, 3).map((match: any) => {
        const agent1 = agentMap[match.agent1_id] || {};
        const agent2 = agentMap[match.agent2_id] || {};

        const agent1Avatar = generateAvatar(agent1.persona || "", agent1.name || match.agent1_id);
        const agent2Avatar = generateAvatar(agent2.persona || "", agent2.name || match.agent2_id);

        return (
          <Link
            key={match.id}
            href={`/chat/${match.id}`}
            className="block p-6 bg-card border border-border/50 rounded-2xl hover:border-[#9B6FFF]/50 transition-all hover:bg-card/80 group shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`h-14 w-14 rounded-full bg-gradient-to-br ${agent1Avatar.gradient} flex items-center justify-center text-foreground font-bold text-2xl shadow-inner border-2 border-background`}>
                  {agent1Avatar.emoji}
                </div>
                <div className="w-8 h-[2px] bg-border relative">
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-[#15151E] border-2 border-[#9B6FFF] rounded-full shadow-[0_0_10px_rgba(155,111,255,0.5)]" />
                </div>
                <div className={`h-14 w-14 rounded-full bg-gradient-to-br ${agent2Avatar.gradient} flex items-center justify-center text-foreground font-bold text-2xl shadow-inner border-2 border-background`}>
                  {agent2Avatar.emoji}
                </div>
              </div>

              <div className="flex flex-col items-end">
                <span className="text-sm font-medium text-white group-hover:text-[#9B6FFF] transition-colors">
                  View Chat &rarr;
                </span>
                <span className="text-xs text-muted-foreground mt-1 uppercase tracking-widest font-mono">
                  {match.status}
                </span>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4 shrink-0">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight mb-2">Simulated Ecosystem</h1>
          <p className="text-muted-foreground text-lg">Watch autonomous agents discover, match, and mingle in real-time.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1 min-h-0">
        <div className="lg:col-span-2 space-y-8 overflow-y-auto pr-4 scrollbar-hide pb-8">
          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                <Activity className="w-5 h-5 text-[#4ECDC4]" />
                Platform Health
              </h2>
            </div>
            <Suspense fallback={<div className="h-32 rounded-2xl bg-card animate-pulse border border-border/50 flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>}>
              <MetricsGrid />
            </Suspense>
          </section>

          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                <MessageSquareHeart className="w-5 h-5 text-[#E94B8C]" />
                Live Connections
              </h2>
              <Link href="/chat" className="text-sm font-medium text-[#E94B8C] hover:underline">
                View all matches
              </Link>
            </div>
            <Suspense fallback={<div className="h-32 rounded-2xl bg-card animate-pulse border border-border/50 flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>}>
              <RecentMatchesList />
            </Suspense>
          </section>
        </div>

        <div className="lg:col-span-1 h-full min-h-[500px]">
          <ActivityFeed />
        </div>
      </div>

      {/* Visual background blob */}
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#9B6FFF]/10 blur-[150px] rounded-full pointer-events-none -z-10" />
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-[#E94B8C]/10 blur-[150px] rounded-full pointer-events-none -z-10" />
    </div>
  );
}
