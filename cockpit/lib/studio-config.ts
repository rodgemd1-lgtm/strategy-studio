// RUSR Studio type definitions

export interface RusrStatus {
  studio: string;
  config: StudioConfig;
  metrics: Metrics;
  quality_gates: QualityGate[];
  artifacts: Artifact[];
  audit_log: AuditEntry[];
}

export interface StudioConfig {
  name: string;
  diamond: string;  // D1 | D2 | D3
  bands: string[];  // A1, A2, A3, A4
  budget: { per_run: number; per_step: number };
  gates: string[];
  mcp: string[];
}

export interface Metrics {
  run_id: string;
  status: string;
  layer: number;
  gates: Record<string, GateState>;
  budget_used: number;
  budget_ceiling: number;
  tool_calls: number;
  tool_ceiling: number;
  wall_elapsed: number;
  wall_ceiling: number;
  context_tokens: number;
  context_ceiling: number;
  artifact_count: number;
  latest_artifact: string;
}

export type GateState = "LOCKED" | "READY" | "PASS" | "FAIL" | "SKIP";
export type GateStatusType = GateState;

export interface QualityGate {
  id: string;
  label: string;
  status: GateStatusType;
  blockers: string[];
}

export interface Artifact {
  id: string;
  type: string;
  rig_l: number;
  sigma: number;
  sigma_pass: boolean;
  source_count: number;
  genesis: string;
  created_at: string;
}

export interface AuditEntry {
  ts: string;
  layer: number;
  event: string;
  detail: string;
  user: string;
}