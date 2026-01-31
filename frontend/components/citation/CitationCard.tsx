"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Citation } from "@/lib/api";
import { Brain, Heart, Calendar, User, BookOpen } from "lucide-react";

interface CitationCardProps {
  citation: Citation;
}

const typeConfig = {
  decision: {
    icon: Brain,
    label: "결정",
    variant: "decision" as const,
  },
  preference: {
    icon: Heart,
    label: "선호",
    variant: "preference" as const,
  },
  plan: {
    icon: Calendar,
    label: "계획",
    variant: "plan" as const,
  },
  profile: {
    icon: User,
    label: "프로필",
    variant: "profile" as const,
  },
  episode: {
    icon: BookOpen,
    label: "에피소드",
    variant: "episode" as const,
  },
};

export function CitationCard({ citation }: CitationCardProps) {
  const config = typeConfig[citation.type];
  const Icon = config.icon;

  return (
    <Card className="bg-muted/50 border-none shadow-none">
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          <div className="w-6 h-6 rounded-full bg-background flex items-center justify-center shrink-0">
            <Icon className="w-3 h-3 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={config.variant} className="text-[10px] px-1.5 py-0">
                {config.label}
              </Badge>
              <span className="text-[10px] text-muted-foreground">
                {new Date(citation.created_at).toLocaleDateString("ko-KR")}
              </span>
            </div>
            <p className="text-xs text-foreground line-clamp-2">
              {citation.summary}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface CitationListProps {
  citations: Citation[];
  hideHeader?: boolean;
}

export function CitationList({ citations, hideHeader = false }: CitationListProps) {
  if (citations.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        사용된 기억이 없습니다
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {!hideHeader && (
        <h3 className="font-semibold flex items-center gap-2">
          <Brain className="w-4 h-4" />
          참고한 기억
        </h3>
      )}
      {citations.map((citation) => (
        <CitationCard key={citation.id} citation={citation} />
      ))}
    </div>
  );
}
