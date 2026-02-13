import { Tooltip, TooltipContent, TooltipTrigger } from "~/components/ui/tooltip";
import type { FigurativeExpression } from "~/api/types";

// =============================================================================
// Expression Type Colors & Labels
// =============================================================================

const expressionTypeColors: Record<FigurativeExpression["type"], string> = {
    idiom: "bg-purple-100 text-purple-700",
    conceptual_metaphor: "bg-blue-100 text-blue-700",
};

const expressionTypeLabels: Record<FigurativeExpression["type"], string> = {
    idiom: "Idiom",
    conceptual_metaphor: "Conceptual Metaphor",
};

interface HighlightedTextProps {
    text: string;
    expressions: FigurativeExpression[];
}

export function HighlightedText({ text, expressions }: HighlightedTextProps) {
    if (expressions.length === 0) {
        return <p className="whitespace-pre-wrap leading-relaxed">{text}</p>;
    }

    const sortedExpressions = [...expressions].sort((a, b) => a.startIndex - b.startIndex);
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedExpressions.forEach((expr, i) => {
        if (expr.startIndex > lastIndex) {
            parts.push(<span key={`text-${i}`}>{text.slice(lastIndex, expr.startIndex)}</span>);
        }

        parts.push(
            <Tooltip key={`expr-${i}`}>
                <TooltipTrigger asChild>
                    <mark className={`px-1 rounded ${expressionTypeColors[expr.type]} cursor-help`}>
                        {expr.original}
                    </mark>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border shadow-lg">
                    <p className="font-medium text-xs mb-1">{expressionTypeLabels[expr.type]}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{expr.explanation}</p>
                </TooltipContent>
            </Tooltip>
        );

        lastIndex = expr.endIndex;
    });

    if (lastIndex < text.length) {
        parts.push(<span key="text-end">{text.slice(lastIndex)}</span>);
    }

    return <p className="whitespace-pre-wrap leading-relaxed">{parts}</p>;
}

export { expressionTypeColors, expressionTypeLabels };
