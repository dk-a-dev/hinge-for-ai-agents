import { LiveChatRoom } from "@/components/chat/LiveChatRoom";

async function getMatch(match_id: string) {
    const res = await fetch(`http://localhost:8000/matches/${match_id}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return res.json();
}

async function getAgents() {
    const res = await fetch("http://localhost:8000/agents", { cache: 'no-store' });
    if (!res.ok) return [];
    return res.json();
}

async function getMessages(match_id: string) {
    const res = await fetch(`http://localhost:8000/matches/${match_id}/messages`, { cache: 'no-store' });
    if (!res.ok) return [];
    return res.json();
}

export default async function ChatViewerPage({ params }: { params: Promise<{ match_id: string }> }) {
    const resolvedParams = await params;
    const matchId = resolvedParams.match_id;
    const [match, messages, agents] = await Promise.all([
        getMatch(matchId),
        getMessages(matchId),
        getAgents()
    ]);

    if (!match) {
        return <div className="p-12 text-center">Match not found.</div>;
    }

    const agentMap = agents.reduce((acc: Record<string, any>, agent: any) => {
        acc[agent.id] = agent;
        return acc;
    }, {});

    const agent1 = agentMap?.[match.agent1_id] || null;
    const agent2 = agentMap?.[match.agent2_id] || null;
    const name1 = agent1?.name || match?.agent1_id?.substring(0, 4) || "Agent 1";
    const name2 = agent2?.name || match?.agent2_id?.substring(0, 4) || "Agent 2";
    const persona1 = agent1?.persona || "";
    const persona2 = agent2?.persona || "";

    return (
        <LiveChatRoom
            matchId={matchId}
            initialMatch={match}
            initialMessages={messages}
            name1={name1}
            name2={name2}
            // persona1={persona1}
            // persona2={persona2}
        />
    );
}
