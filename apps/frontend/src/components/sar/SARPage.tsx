import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  ChevronLeft,
  CircleHelp,
  FileText,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { generateSAR, getCase } from "../../api/cases";
import type { CaseRecord } from "../../types/case";
import type { SARFiveWOneH, SARResponse } from "../../types/sar";

const emptyFiveWOneH: SARFiveWOneH = {
  who: "",
  what: "",
  when: "",
  where: "",
  why: "",
  how: "",
};

const formatRisk = (value: number | null | undefined) =>
  `${Math.round((value ?? 0) * 100)}%`;

const titleCase = (value: string | null | undefined) =>
  value
    ? value
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/(^|\s)\S/g, (letter) => letter.toUpperCase())
    : "Unclassified";

export function SARPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState<CaseRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [fiveWOneH, setFiveWOneH] = useState<SARFiveWOneH>(emptyFiveWOneH);

  const [narrative, setNarrative] = useState("");
  const [comments, setComments] = useState("");
  const [notice, setNotice] = useState("");

  const [sarResponse, setSarResponse] = useState<SARResponse | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!caseId) return;

    getCase(caseId)
      .then(setCaseData)
      .catch((requestError: Error & { status?: number }) =>
        setError(
          requestError.status === 404
            ? "This case does not exist."
            : "Unable to load case context from the backend.",
        ),
      )
      .finally(() => setLoading(false));
  }, [caseId]);

  const updateFiveWOneH = (field: keyof SARFiveWOneH, value: string) =>
    setFiveWOneH((current) => ({
      ...current,
      [field]: value,
    }));

  const saveDraft = () =>
    setNotice(
      "Draft changes are local only. No SAR save endpoint is available yet.",
    );

  const handleGenerateSAR = async () => {
    if (!caseId || generating) return;

    setGenerating(true);
    setError("");
    setNotice("");

    try {
      const result = await generateSAR(caseId);

      setSarResponse(result);
      setNarrative(result.sar_draft);
      setNotice("SAR draft generated successfully.");
    } catch (requestError) {
      const requestErrorObject = requestError as Error;

      setError(requestErrorObject.message || "Unable to generate SAR draft.");
    } finally {
      setGenerating(false);
    }
  };

  if (loading)
    return (
      <div className="page">
        <div className="sar-loading skeleton" />
      </div>
    );

  if (error || !caseData)
    return (
      <div className="page">
        <button
          className="back-link"
          onClick={() => navigate(caseId ? `/cases/${caseId}` : "/cases")}
        >
          <ChevronLeft size={16} /> Back to case
        </button>

        <div className="detail-error">
          <AlertTriangle size={24} />

          <h2>{error || "Case not found"}</h2>

          <p>
            {error
              ? "The SAR workspace could not load its case context."
              : "We could not find the requested case."}
          </p>
        </div>
      </div>
    );

  return (
    <div className="page sar-page">
      <button
        className="back-link"
        onClick={() => navigate(`/cases/${caseData.case_id}`)}
      >
        <ChevronLeft size={16} /> Back to case
      </button>

      <header className="sar-header">
        <div>
          <p className="eyebrow accent-text">Compliance filing workspace</p>

          <h2>SAR Generation &amp; Review</h2>

          <p>
            Prepare and review a suspicious activity report draft for analyst
            approval.
          </p>
        </div>

        <div className="sar-header-actions">
          <button
            className="button button-dark"
            onClick={handleGenerateSAR}
            disabled={generating}
          >
            {generating ? "Generating..." : "Generate SAR"}
            {!generating && <FileText size={15} />}
          </button>

          <button
            className="button button-light"
            onClick={() => navigate(`/cases/${caseData.case_id}`)}
          >
            Case detail <ArrowUpRight size={15} />
          </button>
        </div>
      </header>

      {error && (
        <div className="detail-error">
          <AlertTriangle size={20} />
          <div>
            <strong>SAR generation failed</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      <section className="card sar-case-context">
        <div className="sar-case-id">
          <span>CASE</span>
          <strong>{caseData.case_id}</strong>
          <small>Customer {caseData.customer_id ?? "Unknown"}</small>
        </div>

        <div>
          <span>Priority</span>
          <RiskBadge value={caseData.priority} />
        </div>

        <div>
          <span>Status</span>
          <StatusBadge value={caseData.status} />
        </div>

        <div>
          <span>Fused risk</span>
          <strong className="sar-risk-value">
            {formatRisk(caseData.fused_risk)}
          </strong>
        </div>

        <div>
          <span>Typology</span>
          <strong>{titleCase(caseData.suspected_typology)}</strong>
        </div>
      </section>

      {notice && (
        <div className="toast success">
          <Check size={16} />
          {notice}
        </div>
      )}

      <div className="sar-layout">
        <main className="sar-main">
          <section className="card sar-card">
            <SARCardTitle
              icon={FileText}
              title="Suspicious activity summary"
              caption="Structure the facts before drafting the narrative."
            />

            <div className="five-w-grid">
              {(["who", "what", "when", "where", "why", "how"] as const).map(
                (field) => (
                  <label key={field}>
                    <span>{field.toUpperCase()}</span>

                    <textarea
                      value={fiveWOneH[field]}
                      onChange={(event) =>
                        updateFiveWOneH(field, event.target.value)
                      }
                      placeholder={`Add ${field} details from verified case evidence`}
                    />
                  </label>
                ),
              )}
            </div>
          </section>

          <section className="card sar-card">
            <SARCardTitle
              icon={FileText}
              title="SAR narrative"
              caption={
                sarResponse
                  ? "Generated from structured case evidence. The analyst can edit the draft before review."
                  : "Generate a SAR draft from the current case data."
              }
            />

            <textarea
              className="sar-narrative"
              value={narrative}
              onChange={(event) => setNarrative(event.target.value)}
              placeholder="Draft the suspicious activity narrative using verified facts only."
            />

            <div className="sar-field-meta">
              <span>{narrative.length} characters</span>
              <span>Analyst editable</span>
            </div>
          </section>

          <section className="card sar-card">
            <SARCardTitle
              icon={ShieldCheck}
              title="Evidence &amp; grounding"
              caption="Evidence references returned by the SAR backend."
            />

            {sarResponse ? (
              <div className="sar-evidence-content">
                <div className="sar-validation-row">
                  <span>Validation status</span>

                  <StatusBadge value={sarResponse.validation_status} />
                </div>

                <div className="sar-evidence-list">
                  <span className="sar-section-label">Evidence used</span>

                  {sarResponse.evidence_ids_used.length > 0 ? (
                    <div className="sar-evidence-chips">
                      {sarResponse.evidence_ids_used.map((evidenceId) => (
                        <span key={evidenceId} className="sar-evidence-chip">
                          {evidenceId}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p>No evidence identifiers were returned.</p>
                  )}
                </div>

                {sarResponse.unsupported_claims.length > 0 && (
                  <div className="sar-unsupported">
                    <span className="sar-section-label">
                      Unsupported claims
                    </span>

                    <ul>
                      {sarResponse.unsupported_claims.map((claim) => (
                        <li key={claim}>{claim}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="sar-empty-panel">
                <CircleHelp size={20} />

                <strong>No SAR evidence references available</strong>

                <span>
                  Generate a SAR draft to retrieve evidence references and
                  grounding information.
                </span>
              </div>
            )}
          </section>
        </main>

        <aside className="sar-side">
          <section className="card sar-card">
            <SARCardTitle
              icon={ShieldCheck}
              title="Case risk context"
              caption="Live values from the case API"
            />

            <div className="sar-metric-list">
              <Metric label="KYC risk" value={formatRisk(caseData.kyc_risk)} />

              <Metric label="AML risk" value={formatRisk(caseData.aml_risk)} />

              <Metric
                label="Uncertainty"
                value={formatRisk(caseData.uncertainty)}
              />

              <Metric
                label="Human review"
                value={
                  caseData.human_review_required ? "Required" : "Not required"
                }
              />
            </div>
          </section>

          <section className="card sar-card">
            <SARCardTitle
              icon={CircleHelp}
              title="Validation"
              caption={
                sarResponse
                  ? "Validation returned by the SAR backend."
                  : "Generate a SAR to run validation."
              }
            />

            {sarResponse ? (
              <div className="validation-pending">
                <span className="validation-icon">
                  {sarResponse.validation_status === "VALID" ? (
                    <Check size={15} />
                  ) : (
                    <AlertTriangle size={15} />
                  )}
                </span>

                <strong>{titleCase(sarResponse.validation_status)}</strong>

                <p>
                  The backend validator checked the generated SAR against the
                  structured case evidence.
                </p>

                <span className="validation-row">
                  Evidence references{" "}
                  <b>{sarResponse.evidence_ids_used.length}</b>
                </span>

                <span className="validation-row">
                  Unsupported claims{" "}
                  <b>{sarResponse.unsupported_claims.length}</b>
                </span>

                <span className="validation-row">
                  Validation <b>{sarResponse.validation_status}</b>
                </span>
              </div>
            ) : (
              <div className="validation-pending">
                <span className="validation-icon">
                  <LockKeyhole size={15} />
                </span>

                <strong>Not run</strong>

                <p>Validation will appear after a SAR draft is generated.</p>

                <span className="validation-row">
                  Evidence grounding <b>Pending</b>
                </span>

                <span className="validation-row">
                  Factual validation <b>Pending</b>
                </span>

                <span className="validation-row">
                  SAR validation <b>Pending</b>
                </span>
              </div>
            )}
          </section>

          <section className="card sar-card">
            <SARCardTitle
              icon={FileText}
              title="Analyst review"
              caption="Local review notes until review endpoints are available."
            />

            <textarea
              className="sar-comments"
              value={comments}
              onChange={(event) => setComments(event.target.value)}
              placeholder="Add analyst comments"
            />

            <div className="sar-review-actions">
              <button className="button button-light" onClick={saveDraft}>
                Save draft
              </button>

              <button
                className="button button-dark"
                disabled
                title="No SAR review endpoint exists yet"
              >
                Review pending
              </button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function SARCardTitle({
  icon: Icon,
  title,
  caption,
}: {
  icon: typeof FileText;
  title: string;
  caption: string;
}) {
  return (
    <div className="sar-card-title">
      <div className="sar-title-icon">
        <Icon size={16} />
      </div>

      <div>
        <h3>{title}</h3>
        <p>{caption}</p>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="sar-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RiskBadge({ value }: { value: string | null | undefined }) {
  return (
    <span className={`badge risk-badge ${(value ?? "").toLowerCase()}`}>
      {titleCase(value)}
    </span>
  );
}

function StatusBadge({ value }: { value: string | null | undefined }) {
  return (
    <span
      className={`badge status-badge ${(value ?? "")
        .toLowerCase()
        .replace("_", "-")}`}
    >
      <i />
      {titleCase(value)}
    </span>
  );
}
