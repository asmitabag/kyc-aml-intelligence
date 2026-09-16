import { useMemo, useState } from "react";
import type { PointerEvent } from "react";
import { Maximize2, Minus, Move, Plus, RotateCcw } from "lucide-react";
import type { GraphExplanation } from "../../types/case";

interface Point {
  x: number;
  y: number;
}

type Selection =
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string }
  | null;

function formatImportance(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

function buildPositions(nodes: string[]): Map<string, Point> {
  const positions = new Map<string, Point>();
  const center = { x: 260, y: 140 };
  const radius = Math.min(105, 42 + nodes.length * 12);
  nodes.forEach((node, index) => {
    const angle =
      nodes.length === 1
        ? 0
        : (Math.PI * 2 * index) / nodes.length - Math.PI / 2;
    positions.set(node, {
      x: center.x + Math.cos(angle) * radius,
      y: center.y + Math.sin(angle) * radius,
    });
  });
  return positions;
}

export function AMLGraph({ graph }: { graph: GraphExplanation | null }) {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [selection, setSelection] = useState<Selection>(null);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(
    null,
  );

  const nodes = useMemo(() => graph?.nodes ?? [], [graph]);
  const edges = graph?.edges ?? [];
  const positions = useMemo(() => buildPositions(nodes), [nodes]);
  const selectedNode = selection?.kind === "node" ? selection.id : null;
  const selectedEdge =
    selection?.kind === "edge"
      ? edges.find((edge) => edge.transaction_id === selection.id)
      : null;
  const importantEdgeCount = edges.filter(
    (edge) => edge.importance >= 0.75,
  ).length;

  if (!graph || nodes.length === 0) {
    return (
      <div className="aml-graph-empty">
        <Move size={20} />
        <strong>No transaction network available</strong>
        <span>This case has no account nodes or graph evidence.</span>
      </div>
    );
  }

  const resetView = () => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
    setSelection(null);
  };
  const handlePointerDown = (event: PointerEvent<SVGSVGElement>) => {
    setDragStart({ x: event.clientX - offset.x, y: event.clientY - offset.y });
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const handlePointerMove = (event: PointerEvent<SVGSVGElement>) => {
    if (dragStart)
      setOffset({
        x: event.clientX - dragStart.x,
        y: event.clientY - dragStart.y,
      });
  };
  const handlePointerUp = () => setDragStart(null);

  return (
    <div className="aml-graph-shell">
      <div className="aml-graph-toolbar">
        <div>
          <span className="graph-stat">
            <strong>{nodes.length}</strong> accounts
          </span>
          <span className="graph-stat">
            <strong>{edges.length}</strong> connections
          </span>
          <span className="graph-stat">
            <strong>{importantEdgeCount}</strong> important edges
          </span>
        </div>
        <div className="graph-controls">
          <button
            type="button"
            onClick={() => setZoom((value) => Math.min(value + 0.15, 2))}
            aria-label="Zoom in"
          >
            <Plus size={15} />
          </button>
          <button
            type="button"
            onClick={() => setZoom((value) => Math.max(value - 0.15, 0.65))}
            aria-label="Zoom out"
          >
            <Minus size={15} />
          </button>
          <button
            type="button"
            onClick={resetView}
            aria-label="Reset graph view"
          >
            <RotateCcw size={14} />
          </button>
          <span className="zoom-label">{Math.round(zoom * 100)}%</span>
        </div>
      </div>
      <div className="aml-graph-layout">
        <div className="aml-graph-viewport">
          <svg
            className="aml-graph-canvas"
            viewBox="0 0 520 280"
            role="img"
            aria-label="AML transaction network"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
          >
            <defs>
              <marker
                id="aml-arrow"
                markerWidth="8"
                markerHeight="8"
                refX="7"
                refY="4"
                orient="auto"
              >
                <path d="M0,0 L8,4 L0,8 Z" fill="#c98677" />
              </marker>
            </defs>
            <g
              transform={`translate(${offset.x} ${offset.y}) translate(260 140) scale(${zoom}) translate(-260 -140)`}
            >
              {edges.map((edge) => {
                const source = positions.get(edge.source);
                const target = positions.get(edge.target);
                if (!source || !target) return null;
                const important = edge.importance >= 0.75;
                return (
                  <g
                    key={edge.transaction_id}
                    className={`aml-edge ${important ? "important" : ""} ${selectedEdge?.transaction_id === edge.transaction_id ? "selected" : ""}`}
                    onClick={(event) => {
                      event.stopPropagation();
                      setSelection({ kind: "edge", id: edge.transaction_id });
                    }}
                  >
                    <line
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      markerEnd="url(#aml-arrow)"
                    />
                    <text
                      x={(source.x + target.x) / 2}
                      y={(source.y + target.y) / 2 - 7}
                    >
                      {edge.transaction_id}
                    </text>
                  </g>
                );
              })}
              {nodes.map((node) => {
                const point = positions.get(node);
                if (!point) return null;
                return (
                  <g
                    key={node}
                    className={`aml-node ${selectedNode === node ? "selected" : ""}`}
                    transform={`translate(${point.x} ${point.y})`}
                    onClick={(event) => {
                      event.stopPropagation();
                      setSelection({ kind: "node", id: node });
                    }}
                  >
                    <circle r="22" />
                    <text y="4">{node}</text>
                  </g>
                );
              })}
            </g>
          </svg>
          <span className="graph-pan-hint">
            <Move size={13} /> Drag to pan
          </span>
        </div>
        <aside className="aml-graph-inspector">
          <div className="inspector-heading">
            <span>{selection ? "Selected evidence" : "Network context"}</span>
            <Maximize2 size={14} />
          </div>
          {selectedNode ? (
            <>
              <strong>{selectedNode}</strong>
              <p>Account node from the AML graph.</p>
            </>
          ) : selectedEdge ? (
            <>
              <strong>{selectedEdge.transaction_id}</strong>
              <p>
                {selectedEdge.source} to {selectedEdge.target}
              </p>
              <div className="inspector-value">
                Importance <b>{formatImportance(selectedEdge.importance)}</b>
              </div>
            </>
          ) : (
            <>
              <strong>Click evidence</strong>
              <p>
                Select an account or transaction to inspect the returned graph
                data.
              </p>
            </>
          )}
        </aside>
      </div>
      <div className="aml-graph-legend">
        <span>
          <i className="legend-node" />
          Account node
        </span>
        <span>
          <i className="legend-edge" />
          Transaction edge
        </span>
        <span>
          <i className="legend-important" />
          Higher importance
        </span>
      </div>
      {graph.important_features?.length ? (
        <div className="graph-feature-list">
          <span className="feature-label">Important AML features</span>
          <div className="graph-feature-grid">
            {graph.important_features.map((feature) => (
              <div className="graph-feature" key={feature.feature}>
                <div>
                  <span>{feature.feature.replaceAll("_", " ")}</span>
                  <b>{formatImportance(feature.importance)}</b>
                </div>
                <div className="graph-feature-track">
                  <i
                    style={{
                      width: `${Math.min(feature.importance * 100, 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
