import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { PythonCellSchema, PythonExecutionResultSchema, PythonRuntimeSchema } from "@data-analyst-lab/shared";

import { PythonNotebook } from "@/components/features/python-lab/python-notebook";
import { apiClient } from "@/lib/api-client";

import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE_URL: "http://localhost:8000",
  ApiError: class ApiError extends Error {},
}));

// The real PythonCellEditor mounts Monaco (via next/dynamic, client-only), which isn't viable in
// jsdom. Stub it with a plain textarea + buttons that preserve the props contract the notebook
// depends on, matching the pattern sql-exercise-workspace.test.tsx uses for SqlEditor.
vi.mock("@/components/features/python-lab/python-cell-editor", () => ({
  PythonCellEditor: ({
    value,
    onChange,
    onRun,
    isRunning,
    cellNumber,
    onDelete,
    onMoveUp,
    onMoveDown,
    canMoveUp,
    canMoveDown,
    ariaLabel,
  }: {
    value: string;
    onChange: (next: string) => void;
    onRun?: () => void;
    isRunning?: boolean;
    cellNumber?: number;
    onDelete?: () => void;
    onMoveUp?: () => void;
    onMoveDown?: () => void;
    canMoveUp?: boolean;
    canMoveDown?: boolean;
    ariaLabel?: string;
  }) => (
    <div>
      <textarea aria-label={ariaLabel} value={value} onChange={(event) => onChange(event.target.value)} />
      {onRun ? (
        <button type="button" onClick={onRun} disabled={isRunning}>
          {isRunning ? `Running ${cellNumber}...` : `Run ${cellNumber}`}
        </button>
      ) : null}
      {onDelete ? (
        <button type="button" onClick={onDelete}>{`Delete cell ${cellNumber}`}</button>
      ) : null}
      {onMoveUp ? (
        <button type="button" onClick={onMoveUp} disabled={!canMoveUp}>{`Move up ${cellNumber}`}</button>
      ) : null}
      {onMoveDown ? (
        <button type="button" onClick={onMoveDown} disabled={!canMoveDown}>{`Move down ${cellNumber}`}</button>
      ) : null}
    </div>
  ),
}));

const WORKSPACE_ID = "ws-1";
const NOW = "2026-01-01T00:00:00Z";

function makeCell(overrides: Partial<PythonCellSchema>): PythonCellSchema {
  return {
    id: "cell-x",
    workspace_id: WORKSPACE_ID,
    display_order: 0,
    code: "",
    last_result: null,
    last_executed_at: null,
    created_at: NOW,
    updated_at: NOW,
    ...overrides,
  };
}

const runtime: PythonRuntimeSchema = {
  id: "rt-1",
  status: "READY",
  workspace_id: WORKSPACE_ID,
  timeout_seconds: 30,
  error_message: null,
  created_at: NOW,
  last_used_at: NOW,
};

const executionResult: PythonExecutionResultSchema = {
  status: "success",
  stdout: "hello\n",
  stdout_truncated: false,
  display_value: null,
  variables: [],
  charts: [],
  error: null,
  execution_time_ms: 12,
};

let cellsState: PythonCellSchema[];

describe("PythonNotebook", () => {
  beforeEach(() => {
    cellsState = [makeCell({ id: "cell-1", display_order: 0, code: "print('hello')" })];

    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
    vi.mocked(apiClient.patch).mockReset();
    vi.mocked(apiClient.delete).mockReset();

    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === `/python/workspaces/${WORKSPACE_ID}/cells`) {
        return [...cellsState].sort((a, b) => a.display_order - b.display_order);
      }
      throw new Error(`Unhandled GET ${path}`);
    });

    vi.mocked(apiClient.post).mockImplementation(async (path: string, body?: unknown) => {
      if (path === `/python/workspaces/${WORKSPACE_ID}/cells`) {
        const requestBody = body as { code?: string } | undefined;
        const newCell = makeCell({
          id: `cell-${cellsState.length + 1}`,
          display_order: cellsState.length,
          code: requestBody?.code ?? "",
        });
        cellsState.push(newCell);
        return newCell;
      }
      if (path === `/python/runtimes?workspace_id=${WORKSPACE_ID}`) {
        return runtime;
      }
      if (path === `/python/runtimes/${runtime.id}/execute`) {
        return executionResult;
      }
      const resultMatch = path.match(/^\/python\/workspaces\/ws-1\/cells\/([^/]+)\/result$/);
      if (resultMatch) {
        const cell = cellsState.find((c) => c.id === resultMatch[1]);
        const requestBody = body as { result: PythonExecutionResultSchema };
        if (cell) cell.last_result = requestBody.result;
        return cell;
      }
      throw new Error(`Unhandled POST ${path}`);
    });

    vi.mocked(apiClient.patch).mockImplementation(async (path: string, body?: unknown) => {
      const match = path.match(/^\/python\/workspaces\/ws-1\/cells\/([^/]+)$/);
      if (match) {
        const cell = cellsState.find((c) => c.id === match[1]);
        const requestBody = body as { code?: string; display_order?: number };
        if (cell) {
          if (requestBody.code != null) cell.code = requestBody.code;
          if (requestBody.display_order != null) cell.display_order = requestBody.display_order;
        }
        return cell;
      }
      throw new Error(`Unhandled PATCH ${path}`);
    });

    vi.mocked(apiClient.delete).mockImplementation(async (path: string) => {
      const match = path.match(/^\/python\/workspaces\/ws-1\/cells\/([^/]+)$/);
      if (match) {
        cellsState = cellsState.filter((c) => c.id !== match[1]);
        return undefined;
      }
      throw new Error(`Unhandled DELETE ${path}`);
    });
  });

  it("renders the workspace's cells, numbered", async () => {
    renderWithProviders(<PythonNotebook workspaceId={WORKSPACE_ID} />);

    const editor = (await screen.findByLabelText("Python cell 1 editor")) as HTMLTextAreaElement;
    expect(editor.value).toBe("print('hello')");
    expect(apiClient.get).toHaveBeenCalledWith(`/python/workspaces/${WORKSPACE_ID}/cells`);
  });

  it("adds a new cell via the notebook toolbar", async () => {
    renderWithProviders(<PythonNotebook workspaceId={WORKSPACE_ID} />);

    await screen.findByLabelText("Python cell 1 editor");
    fireEvent.click(screen.getByRole("button", { name: "Add Cell" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(`/python/workspaces/${WORKSPACE_ID}/cells`, { code: "" }),
    );
    await screen.findByLabelText("Python cell 2 editor");
  });

  it("running a cell creates a runtime, persists the code, executes it, and shows stdout", async () => {
    renderWithProviders(<PythonNotebook workspaceId={WORKSPACE_ID} />);

    await screen.findByLabelText("Python cell 1 editor");
    fireEvent.click(screen.getByRole("button", { name: "Run 1" }));

    await waitFor(() => expect(apiClient.post).toHaveBeenCalledWith(`/python/runtimes?workspace_id=${WORKSPACE_ID}`));
    await waitFor(() =>
      expect(apiClient.patch).toHaveBeenCalledWith(`/python/workspaces/${WORKSPACE_ID}/cells/cell-1`, {
        code: "print('hello')",
      }),
    );
    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(`/python/runtimes/${runtime.id}/execute`, {
        code: "print('hello')",
        workspace_id: WORKSPACE_ID,
      }),
    );
    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(`/python/workspaces/${WORKSPACE_ID}/cells/cell-1/result`, {
        result: executionResult,
      }),
    );

    expect(await screen.findByText("hello")).toBeInTheDocument();
  });

  it("deletes a cell once more than one exists", async () => {
    cellsState.push(makeCell({ id: "cell-2", display_order: 1, code: "" }));

    renderWithProviders(<PythonNotebook workspaceId={WORKSPACE_ID} />);

    await screen.findByLabelText("Python cell 2 editor");
    expect(screen.getAllByRole("button", { name: /^Delete cell/ })).toHaveLength(2);

    fireEvent.click(screen.getByRole("button", { name: "Delete cell 1" }));

    await waitFor(() => expect(apiClient.delete).toHaveBeenCalledWith(`/python/workspaces/${WORKSPACE_ID}/cells/cell-1`));
    // Only one cell remains, and a lone cell has no delete affordance (there must always be at least one cell).
    await waitFor(() => expect(screen.queryByRole("button", { name: /^Delete cell/ })).not.toBeInTheDocument());
  });
});
