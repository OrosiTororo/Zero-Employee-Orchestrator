/**
 * WorkflowBuilder — Visual DAG workflow editor with drag-and-drop.
 *
 * Renders plan steps as a visual graph with connections showing dependencies.
 * Supports drag-and-drop node reordering and dependency editing.
 * Inspired by n8n's canvas and LangGraph's visual debugger.
 *
 * Usage:
 *   <WorkflowBuilder steps={planSteps} onStepClick={(id) => ...} />
 *   <WorkflowBuilder steps={planSteps} editable onStepsChange={(steps) => ...} />
 */

import { useCallback, useMemo, useState, useRef } from "react";

interface WorkflowStep {
  id: string;
  title: string;
  depends_on: string[];
  status: "pending" | "running" | "completed" | "failed" | "preview";
  estimated_minutes?: number;
}

interface WorkflowBuilderProps {
  steps: WorkflowStep[];
  onStepClick?: (stepId: string) => void;
  onStepsChange?: (steps: WorkflowStep[]) => void;
  editable?: boolean;
  className?: string;
}

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  pending: { bg: "var(--bg-secondary, #252526)", border: "#555", text: "var(--fg-primary, #d4d4d4)" },
  running: { bg: "#1a3a5c", border: "#007acc", text: "#4fc3f7" },
  completed: { bg: "#1a3c2a", border: "#56ba9f", text: "#56ba9f" },
  failed: { bg: "#3c1a1a", border: "#e5484d", text: "#e5484d" },
  preview: { bg: "#2d2a1a", border: "#d4a72c", text: "#d4a72c" },
};

function getStatusIcon(status: string): string {
  switch (status) {
    case "running": return "\u25b6";
    case "completed": return "\u2713";
    case "failed": return "\u2717";
    case "preview": return "\u25cb";
    default: return "\u2022";
  }
}

/** Compute column (depth) for each node via topological layering. */
function computeLayout(steps: WorkflowStep[]): Map<string, { col: number; row: number }> {
  const stepMap = new Map(steps.map((s) => [s.id, s]));
  const depths = new Map<string, number>();

  function getDepth(id: string): number {
    if (depths.has(id)) return depths.get(id)!;
    const step = stepMap.get(id);
    if (!step || step.depends_on.length === 0) {
      depths.set(id, 0);
      return 0;
    }
    const maxParent = Math.max(...step.depends_on.map((d) => getDepth(d)));
    const depth = maxParent + 1;
    depths.set(id, depth);
    return depth;
  }

  steps.forEach((s) => getDepth(s.id));

  // Group by column and assign rows
  const colGroups = new Map<number, string[]>();
  steps.forEach((s) => {
    const col = depths.get(s.id) ?? 0;
    if (!colGroups.has(col)) colGroups.set(col, []);
    colGroups.get(col)!.push(s.id);
  });

  const layout = new Map<string, { col: number; row: number }>();
  colGroups.forEach((ids, col) => {
    ids.forEach((id, row) => layout.set(id, { col, row }));
  });

  return layout;
}

export default function WorkflowBuilder({
  steps,
  onStepClick,
  onStepsChange,
  editable = false,
  className,
}: WorkflowBuilderProps) {
  const layout = useMemo(() => computeLayout(steps), [steps]);
  const [dragSource, setDragSource] = useState<string | null>(null);
  const [linkSource, setLinkSource] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  /** Drag-and-drop: swap two nodes' positions in the step array. */
  const handleDrop = useCallback(
    (targetId: string) => {
      if (!editable || !dragSource || dragSource === targetId || !onStepsChange) return;
      const newSteps = [...steps];
      const srcIdx = newSteps.findIndex((s) => s.id === dragSource);
      const tgtIdx = newSteps.findIndex((s) => s.id === targetId);
      if (srcIdx >= 0 && tgtIdx >= 0) {
        [newSteps[srcIdx], newSteps[tgtIdx]] = [newSteps[tgtIdx], newSteps[srcIdx]];
        onStepsChange(newSteps);
      }
      setDragSource(null);
    },
    [dragSource, editable, onStepsChange, steps],
  );

  /** Link mode: shift+click source, then click target to add dependency. */
  const handleNodeClick = useCallback(
    (stepId: string, shiftKey: boolean) => {
      if (editable && shiftKey && onStepsChange) {
        if (!linkSource) {
          setLinkSource(stepId);
        } else if (linkSource !== stepId) {
          const newSteps = steps.map((s) =>
            s.id === stepId && !s.depends_on.includes(linkSource)
              ? { ...s, depends_on: [...s.depends_on, linkSource] }
              : s,
          );
          onStepsChange(newSteps);
          setLinkSource(null);
        }
      } else {
        setLinkSource(null);
        onStepClick?.(stepId);
      }
    },
    [editable, linkSource, onStepClick, onStepsChange, steps],
  );
  const maxCol = useMemo(
    () => Math.max(0, ...Array.from(layout.values()).map((l) => l.col)),
    [layout],
  );
  const maxRow = useMemo(
    () => Math.max(0, ...Array.from(layout.values()).map((l) => l.row)),
    [layout],
  );

  const NODE_W = 180;
  const NODE_H = 64;
  const GAP_X = 60;
  const GAP_Y = 24;
  const PAD = 24;

  const svgW = (maxCol + 1) * (NODE_W + GAP_X) + PAD * 2;
  const svgH = (maxRow + 1) * (NODE_H + GAP_Y) + PAD * 2;

  const getPos = useCallback(
    (id: string) => {
      const l = layout.get(id) ?? { col: 0, row: 0 };
      return {
        x: PAD + l.col * (NODE_W + GAP_X),
        y: PAD + l.row * (NODE_H + GAP_Y),
      };
    },
    [layout],
  );

  return (
    <div
      className={className}
      style={{ overflow: "auto", border: "1px solid var(--border-primary, #333)", borderRadius: 8 }}
      role="img"
      aria-label="Workflow execution graph"
    >
      <svg ref={svgRef} width={svgW} height={svgH} style={{ minWidth: svgW, minHeight: svgH }}>
        {/* Edges */}
        {steps.flatMap((step) =>
          step.depends_on.map((dep) => {
            const from = getPos(dep);
            const to = getPos(step.id);
            return (
              <line
                key={`${dep}-${step.id}`}
                x1={from.x + NODE_W}
                y1={from.y + NODE_H / 2}
                x2={to.x}
                y2={to.y + NODE_H / 2}
                stroke="#555"
                strokeWidth={2}
                markerEnd="url(#arrow)"
              />
            );
          }),
        )}

        {/* Arrow marker */}
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#555" />
          </marker>
        </defs>

        {/* Nodes */}
        {steps.map((step) => {
          const pos = getPos(step.id);
          const colors = STATUS_COLORS[step.status] ?? STATUS_COLORS.pending;
          return (
            <g
              key={step.id}
              onClick={(e) => handleNodeClick(step.id, e.shiftKey)}
              onDragStart={() => editable && setDragSource(step.id)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(step.id)}
              draggable={editable}
              style={{
                cursor: editable ? "grab" : onStepClick ? "pointer" : "default",
                outline: linkSource === step.id ? "2px dashed #007acc" : "none",
              }}
              role="button"
              aria-label={`Step: ${step.title}, Status: ${step.status}${editable ? ". Drag to reorder, Shift+click to link." : ""}`}
              tabIndex={0}
            >
              <rect
                x={pos.x}
                y={pos.y}
                width={NODE_W}
                height={NODE_H}
                rx={8}
                fill={colors.bg}
                stroke={colors.border}
                strokeWidth={2}
              />
              <text
                x={pos.x + 12}
                y={pos.y + 20}
                fill={colors.text}
                fontSize={12}
                fontWeight="bold"
                fontFamily="system-ui, sans-serif"
              >
                {getStatusIcon(step.status)} {step.title.slice(0, 20)}
              </text>
              <text
                x={pos.x + 12}
                y={pos.y + 40}
                fill="#888"
                fontSize={10}
                fontFamily="system-ui, sans-serif"
              >
                {step.id}
                {step.estimated_minutes ? ` \u2022 ~${step.estimated_minutes}min` : ""}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
