"use client";

import { useMemo, useState } from "react";
import { Background, Controls, Handle, Position, ReactFlow, type Node, type Edge } from "@xyflow/react";
import { GitBranch } from "lucide-react";
import type { LineageGraphSchema, LineageNodeSchema } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useDbtDocs } from "@/features/dbt/use-dbt-docs";
import { useDbtLineage } from "@/features/dbt/use-dbt-lineage";
import { cn } from "@/lib/utils";

import "@xyflow/react/dist/style.css";

const RESOURCE_COLOR: Record<string, string> = {
  source: "border-l-muted-foreground",
  seed: "border-l-amber-500",
  model: "border-l-primary",
  snapshot: "border-l-fuchsia-500",
};

const LAYER_COLUMN: Record<string, number> = { staging: 1, intermediate: 2, marts: 3 };

function columnFor(node: LineageNodeSchema): number {
  if (node.resource_type === "source") return 0;
  if (node.resource_type === "seed") return 1;
  if (node.resource_type === "snapshot") return 3;
  if (node.layer && node.layer in LAYER_COLUMN) return LAYER_COLUMN[node.layer];
  return 4;
}

function LineageNodeCard({ data }: { data: { node: LineageNodeSchema } }) {
  const { node } = data;
  return (
    <div
      className={cn(
        "min-w-40 rounded-md border border-l-4 border-border bg-card px-3 py-2 text-xs shadow-sm",
        RESOURCE_COLOR[node.resource_type] ?? "border-l-border",
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />
      <p className="truncate font-mono font-medium text-foreground">{node.name}</p>
      <p className="mt-0.5 text-[10px] text-muted-foreground uppercase">
        {node.resource_type}
        {node.materialized ? ` · ${node.materialized}` : ""}
      </p>
      <Handle type="source" position={Position.Right} className="!bg-border" />
    </div>
  );
}

const NODE_TYPES = { lineageNode: LineageNodeCard };

function layoutGraph(graph: LineageGraphSchema): { nodes: Node[]; edges: Edge[] } {
  const columnCounts = new Map<number, number>();
  const nodes: Node[] = graph.nodes.map((n) => {
    const column = columnFor(n);
    const row = columnCounts.get(column) ?? 0;
    columnCounts.set(column, row + 1);
    return {
      id: n.unique_id,
      type: "lineageNode",
      position: { x: column * 260, y: row * 84 },
      data: { node: n },
    };
  });
  const edges: Edge[] = graph.edges.map((e) => ({
    id: `${e.from_unique_id}->${e.to_unique_id}`,
    source: e.from_unique_id,
    target: e.to_unique_id,
    animated: false,
  }));
  return { nodes, edges };
}

/** A real DAG, laid out left-to-right by layer, built from dbt's own manifest.json (not a simulation). */
export function DbtLineageGraph() {
  const lineageQuery = useDbtLineage();
  const docsQuery = useDbtDocs();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const layout = useMemo(() => (lineageQuery.data ? layoutGraph(lineageQuery.data) : null), [lineageQuery.data]);

  if (lineageQuery.isLoading) return <LoadingState count={1} itemClassName="h-[28rem]" />;
  if (lineageQuery.isError || !layout) {
    return (
      <EmptyState
        icon={GitBranch}
        title="No lineage yet"
        description="Run the dbt Lab (Run, Test, Build, or Docs Generate) at least once to see the real dependency graph."
      />
    );
  }

  const selectedNode = layout.nodes.find((n) => n.id === selectedId)?.data.node as LineageNodeSchema | undefined;
  const selectedDoc = docsQuery.data?.find((d) => d.unique_id === selectedId);
  const nodesById = new Map(layout.nodes.map((n) => [n.id, (n.data.node as LineageNodeSchema).name]));

  return (
    <div className="h-[28rem] rounded-lg border border-border">
      <ReactFlow
        nodes={layout.nodes}
        edges={layout.edges}
        nodeTypes={NODE_TYPES}
        onNodeClick={(_, node) => setSelectedId(node.id)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>

      <Sheet open={Boolean(selectedNode)} onOpenChange={(open) => !open && setSelectedId(null)}>
        <SheetContent side="right" className="w-96">
          {selectedNode ? (
            <>
              <SheetHeader>
                <SheetTitle className="font-mono">{selectedNode.name}</SheetTitle>
              </SheetHeader>
              <div className="space-y-4 overflow-y-auto px-4 pb-4 text-sm">
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="outline">{selectedNode.resource_type}</Badge>
                  {selectedNode.materialized ? <Badge variant="secondary">{selectedNode.materialized}</Badge> : null}
                  {selectedNode.layer ? <Badge variant="secondary">{selectedNode.layer}</Badge> : null}
                </div>
                {selectedNode.description ? (
                  <p className="text-muted-foreground">{selectedNode.description}</p>
                ) : null}

                {selectedNode.depends_on.length > 0 ? (
                  <div>
                    <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                      Depends on
                    </p>
                    <ul className="space-y-0.5 font-mono text-xs text-foreground">
                      {selectedNode.depends_on.map((id) => (
                        <li key={id}>{nodesById.get(id) ?? id}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {selectedDoc ? (
                  <div>
                    <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                      Columns{" "}
                      {selectedDoc.test_unique_ids.length > 0 ? `(${selectedDoc.test_unique_ids.length} tests)` : ""}
                    </p>
                    <ul className="divide-y divide-border rounded-md border border-border">
                      {selectedDoc.columns.map((col) => (
                        <li key={col.name} className="px-2 py-1.5">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-mono text-xs text-foreground">{col.name}</span>
                            {col.data_type ? (
                              <span className="text-[10px] text-muted-foreground uppercase">{col.data_type}</span>
                            ) : null}
                          </div>
                          {col.description ? (
                            <p className="mt-0.5 text-xs text-muted-foreground">{col.description}</p>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}
