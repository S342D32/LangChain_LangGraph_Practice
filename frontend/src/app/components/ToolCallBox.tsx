"use client";

import { ChartRenderer, type ChartData } from "@/app/components/ChartRenderer";
import { ToolApprovalInterrupt } from "@/app/components/ToolApprovalInterrupt";
import { ActionRequest, ReviewConfig, ToolCall } from "@/app/types/types";
import { cn } from "@/lib/utils";
import { LoadExternalComponent } from "@langchain/langgraph-sdk/react-ui";
import {
  AlertCircle,
  Check,
  ChevronDown,
  ChevronUp,
  CircleCheckBigIcon,
  Loader2,
  StopCircle,
  Terminal,
  X,
} from "lucide-react";
import React, { useCallback, useMemo, useState } from "react";

interface ToolCallBoxProps {
  toolCall: ToolCall;
  uiComponent?: any;
  stream?: any;
  graphId?: string;
  actionRequest?: ActionRequest;
  reviewConfig?: ReviewConfig;
  onResume?: (value: any) => void;
  isLoading?: boolean;
}

export const ToolCallBox = React.memo<ToolCallBoxProps>(
  ({
    toolCall,
    uiComponent,
    stream,
    graphId,
    actionRequest,
    reviewConfig,
    onResume,
    isLoading,
  }) => {
    // Auto-expand when there's GenUI content or a chart result;
    // for action requests stay collapsed so the inline Approve/Reject
    // buttons are the primary call-to-action.
    const [isExpanded, setIsExpanded] = useState(
      () => !!uiComponent || toolCall.name === "generate_chart" || toolCall.name === "generate_image"
    );
    const [expandedArgs, setExpandedArgs] = useState<Record<string, boolean>>(
      {}
    );

    const { name, args, result, status } = useMemo(() => {
      return {
        name: toolCall.name || "Unknown Tool",
        args: toolCall.args || {},
        result: toolCall.result,
        status: toolCall.status || "completed",
      };
    }, [toolCall]);

    const statusIcon = useMemo(() => {
      switch (status) {
        case "completed":
          return <CircleCheckBigIcon />;
        case "error":
          return (
            <AlertCircle
              size={14}
              className="text-destructive"
            />
          );
        case "pending":
          return (
            <Loader2
              size={14}
              className="animate-spin"
            />
          );
        case "interrupted":
          return (
            <StopCircle
              size={14}
              className="text-orange-500"
            />
          );
        default:
          return (
            <Terminal
              size={14}
              className="text-muted-foreground"
            />
          );
      }
    }, [status]);

    const toggleExpanded = useCallback(() => {
      setIsExpanded((prev) => !prev);
    }, []);

    const toggleArgExpanded = useCallback((argKey: string) => {
      setExpandedArgs((prev) => ({
        ...prev,
        [argKey]: !prev[argKey],
      }));
    }, []);

    const hasContent = result || Object.keys(args).length > 0;

    const imagePath = useMemo<string | null>(() => {
      if (name !== "generate_image" || !result) return null;
      const match = String(result).match(/generated_images\/[^\s]+\.png/);
      return match ? `/images/${match[0]}` : null;
    }, [name, result]);

    const chartData = useMemo<ChartData | null>(() => {
      if (name !== "generate_chart" || !args) return null;
      try {
        const raw = typeof args === "string" ? JSON.parse(args) : args;
        if (raw.type && raw.labels && raw.datasets) return raw as ChartData;
        return null;
      } catch {
        return null;
      }
    }, [name, args]);

    // Quick approval handlers — used inline in the header row.
    const showInlineActions = !!actionRequest && !!onResume && !uiComponent;
    const handleQuickApprove = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        onResume?.({ decisions: [{ type: "approve" }] });
      },
      [onResume]
    );
    const handleQuickReject = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        onResume?.({ decisions: [{ type: "reject", message: "" }] });
      },
      [onResume]
    );

    return (
      <div
        className={cn(
          "w-full overflow-hidden rounded-lg border-none shadow-none outline-none transition-colors duration-200 hover:bg-accent",
          isExpanded && hasContent && "bg-accent"
        )}
      >
        <div
          onClick={toggleExpanded}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              toggleExpanded();
            }
          }}
          className={cn(
            "flex w-full cursor-pointer items-center justify-between gap-2 border-none px-2 py-2 text-left shadow-none outline-none focus-visible:ring-0 focus-visible:ring-offset-0",
            !hasContent && "pointer-events-none"
          )}
        >
          <div className="flex min-w-0 flex-1 items-center gap-2">
            {statusIcon}
            <span className="truncate text-[15px] font-medium tracking-[-0.6px] text-foreground">
              {name}
            </span>
            {status === "interrupted" && (
              <span className="shrink-0 rounded-full bg-orange-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-orange-600 dark:text-orange-400">
                Approval needed
              </span>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {showInlineActions && status === "interrupted" && (
              <>
                <button
                  type="button"
                  onClick={handleQuickReject}
                  disabled={isLoading}
                  title="Reject"
                  className="inline-flex h-7 items-center gap-1 rounded-md border border-border bg-background px-2 text-xs font-medium text-foreground transition-colors hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
                >
                  <X size={12} />
                  <span>Reject</span>
                </button>
                <button
                  type="button"
                  onClick={handleQuickApprove}
                  disabled={isLoading}
                  title="Approve"
                  className="inline-flex h-7 items-center gap-1 rounded-md bg-green-600 px-2 text-xs font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
                >
                  <Check size={12} />
                  <span>Approve</span>
                </button>
              </>
            )}
            {hasContent &&
              (isExpanded ? (
                <ChevronUp
                  size={14}
                  className="shrink-0 text-muted-foreground"
                />
              ) : (
                <ChevronDown
                  size={14}
                  className="shrink-0 text-muted-foreground"
                />
              ))}
          </div>
        </div>

        {isExpanded && hasContent && (
          <div className="px-4 pb-4">
            {chartData ? (
              <ChartRenderer chartData={chartData} />
            ) : imagePath ? (
              <img
                src={imagePath}
                alt={String(args.prompt ?? "generated image")}
                className="mt-4 max-w-full rounded-md border border-border"
              />
            ) : uiComponent && stream && graphId ? (
              <div className="mt-4">
                <LoadExternalComponent
                  key={uiComponent.id}
                  stream={stream}
                  message={uiComponent}
                  namespace={graphId}
                  meta={{ status, args, result: result ?? "No Result Yet" }}
                />
              </div>
            ) : actionRequest && onResume ? (
              // Show tool approval UI when there's an action request but no GenUI
              <div className="mt-4">
                <ToolApprovalInterrupt
                  actionRequest={actionRequest}
                  reviewConfig={reviewConfig}
                  onResume={onResume}
                  isLoading={isLoading}
                />
              </div>
            ) : (
              <>
                {Object.keys(args).length > 0 && (
                  <div className="mt-4">
                    <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Arguments
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(args).map(([key, value]) => (
                        <div
                          key={key}
                          className="rounded-sm border border-border"
                        >
                          <button
                            onClick={() => toggleArgExpanded(key)}
                            className="flex w-full items-center justify-between bg-muted/30 p-2 text-left text-xs font-medium transition-colors hover:bg-muted/50"
                          >
                            <span className="font-mono">{key}</span>
                            {expandedArgs[key] ? (
                              <ChevronUp
                                size={12}
                                className="text-muted-foreground"
                              />
                            ) : (
                              <ChevronDown
                                size={12}
                                className="text-muted-foreground"
                              />
                            )}
                          </button>
                          {expandedArgs[key] && (
                            <div className="border-t border-border bg-muted/20 p-2">
                              <pre className="m-0 overflow-x-auto whitespace-pre-wrap break-all font-mono text-xs leading-6 text-foreground">
                                {typeof value === "string"
                                  ? value
                                  : JSON.stringify(value, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {result && (
                  <div className="mt-4">
                    <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Result
                    </h4>
                    <pre className="m-0 overflow-x-auto whitespace-pre-wrap break-all rounded-sm border border-border bg-muted/40 p-2 font-mono text-xs leading-7 text-foreground">
                      {typeof result === "string"
                        ? result
                        : JSON.stringify(result, null, 2)}
                    </pre>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    );
  }
);

ToolCallBox.displayName = "ToolCallBox";
