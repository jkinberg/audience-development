import { useState } from "react";

const COLORS = {
  bg: "#0F0F0F",
  surface: "#1A1A1A",
  surfaceHover: "#222222",
  border: "#2A2A2A",
  borderAccent: "#3A3A3A",
  text: "#E8E4DF",
  textMuted: "#8A857F",
  textDim: "#5A5652",
  accent: "#E8A84C",
  accentDim: "#B8843A",
  human: "#6B9E78",
  humanDim: "#4A7A56",
  agent: "#7B8EC9",
  agentDim: "#5A6EA0",
  hybrid: "#C49070",
  hybridDim: "#A07050",
};

const PhaseCard = ({ phase, title, subtitle, items, isActive, onClick }) => (
  <div
    onClick={onClick}
    style={{
      background: isActive ? COLORS.surfaceHover : COLORS.surface,
      border: `1px solid ${isActive ? COLORS.accent : COLORS.border}`,
      borderRadius: 8,
      padding: "16px 18px",
      cursor: "pointer",
      transition: "all 0.2s ease",
      marginBottom: 10,
    }}
  >
    <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 4 }}>
      <span
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 11,
          color: COLORS.accent,
          letterSpacing: 1,
          textTransform: "uppercase",
        }}
      >
        {phase}
      </span>
      <span
        style={{
          fontFamily: "'Source Serif 4', Georgia, serif",
          fontSize: 17,
          color: COLORS.text,
          fontWeight: 600,
        }}
      >
        {title}
      </span>
    </div>
    <div
      style={{
        fontFamily: "'Source Sans 3', sans-serif",
        fontSize: 13,
        color: COLORS.textMuted,
        lineHeight: 1.4,
        marginBottom: isActive ? 14 : 0,
      }}
    >
      {subtitle}
    </div>
    {isActive && (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {items.map((item, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              padding: "10px 12px",
              background: COLORS.bg,
              borderRadius: 6,
              border: `1px solid ${COLORS.border}`,
            }}
          >
            <div
              style={{
                marginTop: 2,
                width: 8,
                height: 8,
                minWidth: 8,
                borderRadius: "50%",
                background:
                  item.type === "human"
                    ? COLORS.human
                    : item.type === "agent"
                    ? COLORS.agent
                    : COLORS.hybrid,
              }}
            />
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontFamily: "'Source Sans 3', sans-serif",
                  fontSize: 13,
                  color: COLORS.text,
                  fontWeight: 500,
                  lineHeight: 1.4,
                  marginBottom: 3,
                }}
              >
                {item.action}
              </div>
              <div
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  color:
                    item.type === "human"
                      ? COLORS.humanDim
                      : item.type === "agent"
                      ? COLORS.agentDim
                      : COLORS.hybridDim,
                  letterSpacing: 0.5,
                  textTransform: "uppercase",
                }}
              >
                {item.type === "human"
                  ? "→ You do this"
                  : item.type === "agent"
                  ? "→ Agent does this"
                  : "→ Agent assists, you decide"}
              </div>
              {item.tool && (
                <div
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 10,
                    color: COLORS.textDim,
                    marginTop: 3,
                  }}
                >
                  Tool: {item.tool}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);

export default function SubstackGrowthSystem() {
  const [activePhase, setActivePhase] = useState(0);

  const phases = [
    {
      phase: "Foundation",
      title: "Map Your Neighborhood",
      subtitle: "One-time setup · ~2 hours · Identify 15-20 adjacent Substacks",
      items: [
        {
          action:
            "Scan Substack for publications covering product leadership, AI in media, journalism strategy, management/leadership",
          type: "agent",
          tool: "Neighborhood Mapper — crawls Substack directory, analyzes topic overlap with your published articles",
        },
        {
          action:
            "Score each publication by audience overlap potential (subscriber count, topic alignment, engagement quality)",
          type: "agent",
          tool: "Neighborhood Mapper — ranks by relevance signals, filters out growth-hack / low-signal publications",
        },
        {
          action:
            "Review the list, subscribe to 15-20, flag 5-8 high-priority relationship targets",
          type: "human",
        },
      ],
    },
    {
      phase: "Daily Engine",
      title: "15-Minute Engagement Routine",
      subtitle: "Every weekday morning · The algorithm sees this activity",
      items: [
        {
          action:
            "Surface today's 5-8 most relevant posts/Notes from your neighborhood — filtered for topics you can comment on substantively",
          type: "agent",
          tool: "Daily Digest Agent — monitors your 15-20 subscriptions, ranks by topical relevance to your editorial thread",
        },
        {
          action:
            "Read 2-3 posts, leave one substantive comment that adds genuine value and makes readers click your profile",
          type: "human",
        },
        {
          action:
            "Restack 1-2 Notes/posts from aligned writers (highest-leverage algorithm signal for audience overlap)",
          type: "hybrid",
          tool: "Agent surfaces best restack candidates; you choose which to restack",
        },
        {
          action:
            "Post 1 original Note — a standalone thought about product leadership or AI building (not article promotion)",
          type: "human",
        },
      ],
    },
    {
      phase: "Publish Cycle",
      title: "Post-Article Distribution",
      subtitle: "Per article published · ~30 min · Activate your network",
      items: [
        {
          action:
            "Generate a Substack Note with a key insight from the piece — framed as a standalone idea, not just 'new post!'",
          type: "hybrid",
          tool: "Agent drafts 2-3 Note variants from article; you pick and edit",
        },
        {
          action:
            "Identify 3-5 writers in your neighborhood whose audience would specifically care about this article's topic",
          type: "agent",
          tool: "Neighborhood Mapper — matches article topic to writer profiles and recent content",
        },
        {
          action:
            "DM those writers with a personalized note about why the piece is relevant to their readers, ask if they'd consider restacking",
          type: "human",
        },
        {
          action:
            "Restack 1-2 thematically related posts from other writers around the same time (signals topical cluster to algorithm)",
          type: "hybrid",
          tool: "Agent surfaces related recent posts; you choose",
        },
        {
          action: "Cross-post to LinkedIn with standard promotion (existing workflow)",
          type: "human",
        },
      ],
    },
    {
      phase: "Growth Loops",
      title: "Cross-Recommendations & Relationships",
      subtitle: "Ongoing · Relationship-driven · Highest conversion rate on Substack",
      items: [
        {
          action:
            "Track your engagement history — who you've commented on, restacked, DM'd, and how they've responded",
          type: "agent",
          tool: "Relationship Tracker — logs all interactions, flags relationship stage (new / engaged / warm / ready to ask)",
        },
        {
          action:
            "When relationship is warm (4-6 weeks of genuine engagement), propose mutual recommendation",
          type: "human",
        },
        {
          action:
            "When someone subscribes to a recommending writer, they see your publication suggested — single-click subscribe",
          type: "agent",
          tool: "This is Substack's built-in mechanism — no tool needed, just the relationship",
        },
        {
          action:
            "Monitor which recommendations convert subscribers and which writers drive highest-quality audience overlap",
          type: "agent",
          tool: "Growth Analytics Agent — tracks subscriber source, retention by channel",
        },
      ],
    },
    {
      phase: "Learning Loop",
      title: "Track, Measure, Adjust",
      subtitle: "Weekly · 15 min · Feed learnings back into the system",
      items: [
        {
          action:
            "Log: which Notes got traction, which comments generated profile views, which restacks led to follows",
          type: "agent",
          tool: "Analytics Agent — pulls Substack stats, correlates engagement actions with subscriber growth",
        },
        {
          action:
            "Identify patterns: which topics resonate on Notes vs. long-form? Which neighborhood writers drive most discovery?",
          type: "hybrid",
          tool: "Agent surfaces patterns; you interpret and adjust strategy",
        },
        {
          action:
            "Update neighborhood map: add new publications, drop inactive ones, shift priority targets based on what's converting",
          type: "hybrid",
          tool: "Neighborhood Mapper — recommends additions/removals; you approve",
        },
      ],
    },
  ];

  const legend = [
    { color: COLORS.human, label: "Human only — authenticity required" },
    { color: COLORS.agent, label: "Agent — automate fully" },
    { color: COLORS.hybrid, label: "Agent-assisted — you make final call" },
  ];

  return (
    <div
      style={{
        background: COLORS.bg,
        minHeight: "100vh",
        padding: "32px 20px",
        fontFamily: "'Source Sans 3', sans-serif",
      }}
    >
      <link
        href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Source+Sans+3:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
        rel="stylesheet"
      />

      {/* Header */}
      <div style={{ maxWidth: 640, margin: "0 auto 28px" }}>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: COLORS.accent,
            letterSpacing: 2,
            textTransform: "uppercase",
            marginBottom: 8,
          }}
        >
          Audience Development System
        </div>
        <h1
          style={{
            fontFamily: "'Source Serif 4', Georgia, serif",
            fontSize: 26,
            fontWeight: 700,
            color: COLORS.text,
            margin: "0 0 8px",
            lineHeight: 1.2,
          }}
        >
          Substack-Native Growth Engine
        </h1>
        <p
          style={{
            fontSize: 14,
            color: COLORS.textMuted,
            margin: "0 0 20px",
            lineHeight: 1.5,
          }}
        >
          A systematic approach to growing your Substack audience through the platform's
          own discovery algorithm — with agentic tools handling research and tracking so
          your 15 daily minutes are spent on high-value human interactions.
        </p>

        {/* Legend */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "12px 20px",
            padding: "12px 14px",
            background: COLORS.surface,
            borderRadius: 6,
            border: `1px solid ${COLORS.border}`,
          }}
        >
          {legend.map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: item.color,
                }}
              />
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10,
                  color: COLORS.textMuted,
                  letterSpacing: 0.3,
                }}
              >
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Flow Arrow + Phases */}
      <div style={{ maxWidth: 640, margin: "0 auto" }}>
        {/* Vertical flow */}
        {phases.map((phase, i) => (
          <div key={i}>
            <PhaseCard
              {...phase}
              isActive={activePhase === i}
              onClick={() => setActivePhase(activePhase === i ? -1 : i)}
            />
            {i < phases.length - 1 && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  padding: "2px 0",
                }}
              >
                <div
                  style={{
                    width: 1,
                    height: 16,
                    background: COLORS.borderAccent,
                  }}
                />
              </div>
            )}
          </div>
        ))}

        {/* Feedback loop indicator */}
        <div
          style={{
            marginTop: 20,
            padding: "14px 18px",
            background: COLORS.surface,
            border: `1px dashed ${COLORS.borderAccent}`,
            borderRadius: 8,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: COLORS.accent,
              letterSpacing: 1,
              textTransform: "uppercase",
              marginBottom: 6,
            }}
          >
            ↻ Feedback Loop
          </div>
          <div style={{ fontSize: 13, color: COLORS.textMuted, lineHeight: 1.5 }}>
            Learning Loop feeds back into Foundation — your neighborhood map evolves as
            you discover which writers, topics, and engagement patterns actually convert
            readers into subscribers.
          </div>
        </div>

        {/* Build summary */}
        <div style={{ marginTop: 28 }}>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10,
              color: COLORS.agent,
              letterSpacing: 2,
              textTransform: "uppercase",
              marginBottom: 12,
            }}
          >
            What You'd Build
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              {
                name: "Neighborhood Mapper",
                desc: "Discovers and ranks Substack publications by topic overlap. Updates as your content evolves. One-time setup + periodic refresh.",
              },
              {
                name: "Daily Digest Agent",
                desc: "Each morning, surfaces the most relevant posts from your neighborhood for commenting and restacking. Turns random browsing into targeted engagement.",
              },
              {
                name: "Relationship Tracker",
                desc: "Logs your interactions with other writers. Flags when a relationship is warm enough to propose a cross-recommendation.",
              },
              {
                name: "Growth Analytics",
                desc: "Correlates your daily actions (comments, restacks, Notes) with subscriber growth. Surfaces what's actually working.",
              },
            ].map((tool, i) => (
              <div
                key={i}
                style={{
                  padding: "12px 14px",
                  background: COLORS.surface,
                  border: `1px solid ${COLORS.border}`,
                  borderRadius: 6,
                }}
              >
                <div
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 12,
                    color: COLORS.agent,
                    fontWeight: 500,
                    marginBottom: 4,
                  }}
                >
                  {tool.name}
                </div>
                <div
                  style={{
                    fontSize: 13,
                    color: COLORS.textMuted,
                    lineHeight: 1.5,
                  }}
                >
                  {tool.desc}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key insight */}
        <div
          style={{
            marginTop: 28,
            padding: "16px 18px",
            background: COLORS.surface,
            borderLeft: `3px solid ${COLORS.accent}`,
            borderRadius: "0 6px 6px 0",
          }}
        >
          <div
            style={{
              fontFamily: "'Source Serif 4', Georgia, serif",
              fontSize: 15,
              color: COLORS.text,
              fontWeight: 600,
              marginBottom: 6,
            }}
          >
            The Key Insight
          </div>
          <div style={{ fontSize: 13, color: COLORS.textMuted, lineHeight: 1.6 }}>
            The algorithm rewards authentic human engagement — that can't be automated.
            But the research, surfacing, and tracking around that engagement absolutely can.
            The agents eliminate the overhead that makes audience development feel like a
            slog, so your 15 daily minutes go entirely toward the interactions that actually
            move the needle.
          </div>
        </div>
      </div>
    </div>
  );
}
