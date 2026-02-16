import React, { useMemo } from "react";
import { cn } from "~/lib/utils";
import type { Span } from "~/lib/api";

interface TextAnnotatorProps {
    text: string;
    goldSpans?: Span[];
    predictedSpans?: Span[];
    className?: string;
}

interface Segment {
    start: number;
    end: number;
    text: string;
    isGold: boolean;
    isPredicted: boolean;
}

export function TextAnnotator({
    text,
    goldSpans = [],
    predictedSpans = [],
    className,
}: TextAnnotatorProps) {
    const segments = useMemo(() => {
        if (!text) return [];

        // Collect all boundaries
        const boundaries = new Set<number>([0, text.length]);
        goldSpans.forEach((s) => {
            boundaries.add(Math.max(0, Math.min(s.start, text.length)));
            boundaries.add(Math.max(0, Math.min(s.end, text.length)));
        });
        predictedSpans.forEach((s) => {
            boundaries.add(Math.max(0, Math.min(s.start, text.length)));
            boundaries.add(Math.max(0, Math.min(s.end, text.length)));
        });

        const sortedBoundaries = Array.from(boundaries).sort((a, b) => a - b);
        const result: Segment[] = [];

        for (let i = 0; i < sortedBoundaries.length - 1; i++) {
            const start = sortedBoundaries[i];
            const end = sortedBoundaries[i + 1];
            const segmentText = text.slice(start, end);

            const isGold = goldSpans.some((s) => s.start <= start && s.end >= end);
            const isPredicted = predictedSpans.some(
                (s) => s.start <= start && s.end >= end
            );

            result.push({
                start,
                end,
                text: segmentText,
                isGold,
                isPredicted,
            });
        }

        return result;
    }, [text, goldSpans, predictedSpans]);

    return (
        <div className={cn("font-mono text-sm whitespace-pre-wrap leading-relaxed", className)}>
            {segments.map((seg, i) => {
                let bgClass = "bg-transparent";
                let textClass = "text-inherit";
                let title = "";

                if (seg.isGold && seg.isPredicted) {
                    bgClass = "bg-purple-200 dark:bg-purple-900/50";
                    textClass = "text-purple-900 dark:text-purple-100";
                    title = "Gold & Predicted";
                } else if (seg.isGold) {
                    bgClass = "bg-red-200 dark:bg-red-900/50";
                    textClass = "text-red-900 dark:text-red-100";
                    title = "Gold Ground Truth";
                } else if (seg.isPredicted) {
                    bgClass = "bg-blue-200 dark:bg-blue-900/50";
                    textClass = "text-blue-900 dark:text-blue-100";
                    title = "Predicted";
                }

                return (
                    <span
                        key={i}
                        className={cn(bgClass, textClass, "px-0.5 rounded-sm transition-colors")}
                        title={title}
                    >
                        {seg.text}
                    </span>
                );
            })}
        </div>
    );
}
