"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Memory } from "@/lib/api";
import { Brain, Heart, Calendar, User, BookOpen, Trash2 } from "lucide-react";

interface MemoryCardProps {
  memory: Memory;
  onDelete?: (id: string) => void;
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

export function MemoryCard({ memory, onDelete }: MemoryCardProps) {
  const config = typeConfig[memory.type];
  const Icon = config.icon;

  const handleDelete = () => {
    if (onDelete && confirm("이 기억을 삭제하시겠습니까?")) {
      onDelete(memory.id);
    }
  };

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
              <Icon className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant={config.variant} className="text-[10px]">
                  {config.label}
                </Badge>
                <span className="text-[10px] text-muted-foreground">
                  신뢰도 {(memory.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-sm font-medium mb-1 line-clamp-1">
                {memory.summary}
              </p>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {memory.text}
              </p>
              <p className="text-[10px] text-muted-foreground mt-2">
                {new Date(memory.created_at).toLocaleString("ko-KR")}
              </p>
            </div>
          </div>
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 shrink-0 text-destructive hover:text-destructive"
              onClick={handleDelete}
            >
              <Trash2 className="w-4 h-4" />
              <span className="sr-only">삭제</span>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
