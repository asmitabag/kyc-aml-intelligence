export interface ShapFeature {
  feature: string;
  value: number;
  importance: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  transaction_id: string;
  importance: number;
}

export interface GraphExplanation {
  nodes: string[];
  edges: GraphEdge[];
  important_features: Array<{ feature: string; importance: number }>;
}

export interface CaseRecord {
  case_id: string;
  customer_id: string | null;
  kyc_risk: number | null;
  aml_risk: number | null;
  fused_risk: number | null;
  uncertainty: number | null;
  priority: string | null;
  human_review_required: boolean;
  suspected_typology: string | null;
  shap_features: ShapFeature[] | null;
  graph_explanation: GraphExplanation | null;
  status: string;
}

export type CaseStatus = "OPEN" | "UNDER_REVIEW" | "CLOSED";
export type AnalystDecision =
  | "CONFIRMED"
  | "FALSE_POSITIVE"
  | "NEEDS_MORE_INVESTIGATION";

export interface FeedbackPayload {
  analyst_decision: AnalystDecision;
  comment: string | null;
}
