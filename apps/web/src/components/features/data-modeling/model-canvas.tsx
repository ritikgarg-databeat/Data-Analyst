"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Background,
  Controls,
  ReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
} from "@xyflow/react";
import { ArrowLeft, Plus, Save, ShieldCheck } from "lucide-react";
import type {
  DataModelKind,
  DataModelTableType,
  SaveDataModelGraphRequest,
  ValidationResultSchema,
} from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useDataModel, useSaveDataModelGraph, useValidateDataModel } from "@/features/data-modeling/use-data-model";

import { RelationshipEditorSheet, type RelationshipEdgeData } from "./relationship-editor-sheet";
import { TableEditorSheet } from "./table-editor-sheet";
import { TableNode, type TableNodeData } from "./table-node";
import { ValidationPanel } from "./validation-panel";

import "@xyflow/react/dist/style.css";

const NODE_TYPES = { tableNode: TableNode };

const DEFAULT_TABLE_TYPE: Record<DataModelKind, DataModelTableType> = {
  DIMENSIONAL: "OTHER",
  ARCHITECTURE: "OTHER",
  PIPELINE: "SOURCE",
};

const DEFAULT_RELATIONSHIP_TYPE: Record<DataModelKind, RelationshipEdgeData["relationship_type"]> = {
  DIMENSIONAL: "ONE_TO_MANY",
  ARCHITECTURE: "FLOW",
  PIPELINE: "DEPENDS_ON",
};

interface ModelCanvasProps {
  modelId: string;
  modelKind: DataModelKind;
  basePath: string;
}

export function ModelCanvas({ modelId, modelKind, basePath }: ModelCanvasProps) {
  const modelQuery = useDataModel(modelId);
  const saveMutation = useSaveDataModelGraph(modelId);
  const validateMutation = useValidateDataModel(modelId);

  const [nodes, setNodes] = useState<Node<TableNodeData>[]>([]);
  const [edges, setEdges] = useState<Edge<RelationshipEdgeData>[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResultSchema | null>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current || !modelQuery.data) return;
    initializedRef.current = true;
    const model = modelQuery.data;
    setNodes(
      model.tables.map((table) => ({
        id: table.id,
        type: "tableNode",
        position: { x: table.position_x, y: table.position_y },
        data: {
          name: table.name,
          table_type: table.table_type,
          grain: table.grain,
          notes: table.notes,
          columns: table.columns,
        },
      })),
    );
    setEdges(
      model.relationships.map((rel) => ({
        id: rel.id,
        source: rel.from_table_id,
        target: rel.to_table_id,
        data: {
          from_column: rel.from_column,
          to_column: rel.to_column,
          relationship_type: rel.relationship_type,
          label: rel.label,
        },
      })),
    );
  }, [modelQuery.data]);

  const onNodesChange = useCallback(
    (changes: NodeChange<Node<TableNodeData>>[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange<Edge<RelationshipEdgeData>>[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [],
  );
  const onConnect = useCallback(
    (connection: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            data: {
              from_column: null,
              to_column: null,
              relationship_type: DEFAULT_RELATIONSHIP_TYPE[modelKind],
              label: null,
            },
          },
          eds,
        ),
      ),
    [modelKind],
  );

  function addTable() {
    const id = crypto.randomUUID();
    setNodes((nds) => [
      ...nds,
      {
        id,
        type: "tableNode",
        position: { x: 80 + (nds.length % 5) * 260, y: 80 + Math.floor(nds.length / 5) * 200 },
        data: { name: "new_table", table_type: DEFAULT_TABLE_TYPE[modelKind], grain: null, notes: null, columns: [] },
      },
    ]);
  }

  function buildGraphPayload(): SaveDataModelGraphRequest {
    return {
      tables: nodes.map((n) => ({
        key: n.id,
        name: n.data.name,
        table_type: n.data.table_type,
        grain: n.data.grain,
        notes: n.data.notes,
        columns: n.data.columns,
        position_x: n.position.x,
        position_y: n.position.y,
      })),
      relationships: edges.map((e) => ({
        from_key: e.source,
        to_key: e.target,
        from_column: e.data?.from_column ?? null,
        to_column: e.data?.to_column ?? null,
        relationship_type: e.data?.relationship_type ?? DEFAULT_RELATIONSHIP_TYPE[modelKind],
        label: e.data?.label ?? null,
      })),
    };
  }

  function handleSave(onSaved?: () => void) {
    saveMutation.mutate(buildGraphPayload(), {
      onSuccess: () => {
        initializedRef.current = false; // let the effect above re-sync from the fresh, real ids
        setSelectedNodeId(null);
        setSelectedEdgeId(null);
        setValidationResult(null); // stale relative to the graph that was just saved
        onSaved?.();
      },
    });
  }

  function handleValidate() {
    // Validation reads the last SAVED graph server-side — save first so it reflects current edits.
    handleSave(() => validateMutation.mutate(undefined, { onSuccess: setValidationResult }));
  }

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) ?? null;
  const selectedEdge = edges.find((e) => e.id === selectedEdgeId) ?? null;
  const otherTableNames = nodes.filter((n) => n.id !== selectedNodeId).map((n) => n.data.name);

  if (modelQuery.isLoading) return <LoadingState count={1} itemClassName="h-[32rem]" />;
  if (modelQuery.isError || !modelQuery.data) {
    return (
      <ErrorState
        title="Unable to load this model"
        message="We couldn't reach the API to load this model's tables and relationships."
        retry={() => void modelQuery.refetch()}
      />
    );
  }

  return (
    <div className="flex min-w-0 flex-col gap-3 lg:h-[calc(100dvh-8rem)] lg:min-h-[36rem]">
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-card px-4 py-3">
        <Link href={basePath} className="text-muted-foreground hover:text-foreground">
          <ArrowLeft className="size-4" aria-hidden="true" />
        </Link>
        <p className="min-w-0 flex-1 truncate text-sm font-semibold text-foreground sm:flex-none">{modelQuery.data.name}</p>
        <Badge variant="outline">{modelKind}</Badge>

        <div className="flex w-full flex-wrap items-center gap-2 sm:ml-auto sm:w-auto">
          <Button variant="outline" size="sm" onClick={addTable}>
            <Plus className="size-4" aria-hidden="true" />
            Add table
          </Button>
          <Button variant="outline" size="sm" onClick={handleValidate} disabled={validateMutation.isPending}>
            <ShieldCheck className="size-4" aria-hidden="true" />
            {validateMutation.isPending ? "Validating…" : "Validate"}
          </Button>
          <Button size="sm" onClick={() => handleSave()} disabled={saveMutation.isPending}>
            <Save className="size-4" aria-hidden="true" />
            {saveMutation.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-3 lg:flex-row">
        <div className="min-h-[30rem] min-w-0 flex-1 overflow-hidden rounded-xl border border-border lg:min-h-0">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={NODE_TYPES}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => {
              setSelectedNodeId(node.id);
              setSelectedEdgeId(null);
            }}
            onEdgeClick={(_, edge) => {
              setSelectedEdgeId(edge.id);
              setSelectedNodeId(null);
            }}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        {validationResult ? (
          <div className="w-full shrink-0 overflow-y-auto rounded-xl border border-border bg-card p-3 lg:w-80">
            <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Validation</p>
            <ValidationPanel result={validationResult} />
          </div>
        ) : null}
      </div>

      <TableEditorSheet
        modelKind={modelKind}
        open={Boolean(selectedNode)}
        data={selectedNode?.data ?? null}
        otherTableNames={otherTableNames}
        onChange={(next) =>
          setNodes((nds) => nds.map((n) => (n.id === selectedNodeId ? { ...n, data: next } : n)))
        }
        onDelete={() => {
          setNodes((nds) => nds.filter((n) => n.id !== selectedNodeId));
          setEdges((eds) => eds.filter((e) => e.source !== selectedNodeId && e.target !== selectedNodeId));
          setSelectedNodeId(null);
        }}
        onOpenChange={(open) => !open && setSelectedNodeId(null)}
      />

      <RelationshipEditorSheet
        modelKind={modelKind}
        open={Boolean(selectedEdge)}
        data={selectedEdge?.data ?? null}
        fromTableName={nodes.find((n) => n.id === selectedEdge?.source)?.data.name ?? "?"}
        toTableName={nodes.find((n) => n.id === selectedEdge?.target)?.data.name ?? "?"}
        onChange={(next) =>
          setEdges((eds) => eds.map((e) => (e.id === selectedEdgeId ? { ...e, data: next } : e)))
        }
        onDelete={() => {
          setEdges((eds) => eds.filter((e) => e.id !== selectedEdgeId));
          setSelectedEdgeId(null);
        }}
        onOpenChange={(open) => !open && setSelectedEdgeId(null)}
      />
    </div>
  );
}
