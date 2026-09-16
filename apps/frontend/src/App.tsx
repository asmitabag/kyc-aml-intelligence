import { useEffect, useMemo, useState } from "react";
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useSearchParams,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  ArrowUpRight,
  Bell,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  ChevronLeft,
  CircleHelp,
  ClipboardCheck,
  FileSearch,
  Gauge,
  GitBranch,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";
import {
  createCase,
  getCase,
  getCases,
  submitCaseFeedback,
  updateCaseStatus,
} from "./api/cases";
import type { AnalystDecision, CaseRecord, CaseStatus } from "./types/case";
import type { KYCResponse } from "./types/kyc";
import { AMLGraph } from "./components/aml/AMLGraph";
import { SARPage } from "./components/sar/SARPage";
import "./App.css";

const navItems = [
  { label: "Overview", icon: LayoutDashboard, path: "/" },
  { label: "Cases", icon: BriefcaseBusiness, path: "/cases" },
  { label: "Investigations", icon: FileSearch, disabled: true, note: "Soon" },
  { label: "KYC Review", icon: ShieldCheck, disabled: true, note: "Soon" },
  { label: "AML Network", icon: Network, disabled: true, note: "Soon" },
  { label: "Analytics", icon: Gauge, disabled: true, note: "Soon" },
  {
    label: "SAR Review",
    icon: ClipboardCheck,
    disabled: true,
    note: "From case",
  },
];

const formatRisk = (value: number | null | undefined) =>
  `${Math.round((value ?? 0) * 100)}%`;
const formatImportance = (value: number | null | undefined) =>
  `${(value ?? 0) >= 0 ? "+" : ""}${(value ?? 0).toFixed(3)}`;
const titleCase = (value: string | null | undefined) =>
  value
    ? value
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(/(^|\s)\S/g, (letter) => letter.toUpperCase())
    : "Unclassified";
const riskClass = (value: string | null | undefined) =>
  (value ?? "").toLowerCase().replace("_", "-");
const statusClass = (value: string | null | undefined) =>
  (value ?? "").toLowerCase().replace("_", "-");

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [globalQuery, setGlobalQuery] = useState("");
  const location = useLocation();
  const navigate = useNavigate();
  const pageTitle =
    location.pathname === "/cases"
      ? "Case queue"
      : location.pathname.startsWith("/cases/")
        ? "Case investigation"
        : "Overview";

  return (
    <div className="app-shell">
      <MeshBackground />
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={17} />
          </div>
          <div>
            <strong>Verity</strong>
            <span>Intelligence</span>
          </div>
          <button
            className="mobile-close"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={18} />
          </button>
        </div>
        <div className="workspace-label">
          Workspace <ChevronDown size={14} />
        </div>
        <nav className="side-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return item.disabled ? (
              <div
                className="nav-item disabled"
                key={item.label}
                title={
                  item.note === "From case"
                    ? "Open SAR Review from a case detail page"
                    : "This workspace is not available yet"
                }
              >
                <Icon size={18} />
                <span>{item.label}</span>
                <small>{item.note}</small>
              </div>
            ) : (
              <NavLink
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }: { isActive: boolean }) =>
                  `nav-item ${isActive ? "active" : ""}`
                }
                end={item.path === "/"}
                key={item.label}
                to={item.path ?? "/"}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="nav-item disabled">
            <Settings size={18} />
            <span>Settings</span>
          </div>
          <div className="analyst-mini">
            <div className="avatar avatar-coral">AR</div>
            <div>
              <strong>Alex Rivera</strong>
              <span>Compliance analyst</span>
            </div>
            <LogOut size={16} />
          </div>
        </div>
      </aside>
      {sidebarOpen && (
        <button
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        />
      )}
      <main className="main-content">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setSidebarOpen(true)}>
            <Menu size={21} />
          </button>
          <div>
            <p className="eyebrow">Compliance workspace / {pageTitle}</p>
            <h1>{pageTitle}</h1>
          </div>
          <div className="topbar-actions">
            <form
              className="global-search"
              onSubmit={(event) => {
                event.preventDefault();
                if (globalQuery.trim())
                  navigate(
                    `/cases?query=${encodeURIComponent(globalQuery.trim())}`,
                  );
              }}
            >
              <Search size={16} />
              <input
                aria-label="Search cases"
                value={globalQuery}
                onChange={(event) => setGlobalQuery(event.target.value)}
                placeholder="Search cases"
              />
              <kbd>/</kbd>
            </form>
            <div className="header-popover-wrap">
              <button
                className="icon-button notification"
                aria-label="Show notifications"
                onClick={() => {
                  setNotificationsOpen(!notificationsOpen);
                  setProfileOpen(false);
                }}
              >
                <Bell size={19} />
                <span />
              </button>
              {notificationsOpen && (
                <div className="header-popover notification-popover">
                  <strong>Notifications</strong>
                  <p>Priority case queue is up to date.</p>
                  <span className="popover-status">
                    <i />
                    Live workspace
                  </span>
                </div>
              )}
            </div>
            <div className="header-popover-wrap">
              <button
                className="profile profile-button"
                aria-label="Open analyst menu"
                onClick={() => {
                  setProfileOpen(!profileOpen);
                  setNotificationsOpen(false);
                }}
              >
                <div className="avatar avatar-dark">AR</div>
                <div>
                  <strong>Alex Rivera</strong>
                  <span>Analyst</span>
                </div>
                <ChevronDown size={15} />
              </button>
              {profileOpen && (
                <div className="header-popover profile-popover">
                  <strong>Alex Rivera</strong>
                  <p>Compliance analyst</p>
                  <button onClick={() => setProfileOpen(false)}>
                    <Settings size={14} /> Workspace settings
                  </button>
                  <button onClick={() => setProfileOpen(false)}>
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cases" element={<CasesPage />} />
          <Route path="/cases/:caseId" element={<CaseDetail />} />
          <Route path="/cases/:caseId/sar" element={<SARPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}

function MeshBackground() {
  return (
    <div className="mesh-background" aria-hidden="true">
      <span className="mesh-orb mesh-orb-one" />
      <span className="mesh-orb mesh-orb-two" />
      <span className="mesh-grid" />
    </div>
  );
}

function useCases() {
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = () => {
    setLoading(true);
    setError("");
    getCases()
      .then(setCases)
      .catch(() =>
        setError(
          "Unable to reach the intelligence service. Check that the backend is running at 127.0.0.1:8000.",
        ),
      )
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    getCases()
      .then(setCases)
      .catch(() =>
        setError(
          "Unable to reach the intelligence service. Check that the backend is running at 127.0.0.1:8000.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);
  return { cases, setCases, loading, error, reload: load };
}

function PageIntro({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-intro">
      <div>
        <p className="eyebrow accent-text">{eyebrow}</p>
        <h2>{title}</h2>
        <p className="page-description">{description}</p>
      </div>
      {action}
    </div>
  );
}

function Dashboard() {
  const { cases, loading, error, reload } = useCases();
  const stats = useMemo(
    () => ({
      total: cases.length,
      high: cases.filter((item) => item.priority === "HIGH").length,
      review: cases.filter((item) => item.status === "UNDER_REVIEW").length,
      avg: cases.length
        ? cases.reduce((sum, item) => sum + (item.fused_risk ?? 0), 0) /
          cases.length
        : 0,
    }),
    [cases],
  );
  const distribution = [
    {
      name: "Low",
      value: cases.filter((item) => (item.fused_risk ?? 0) < 0.45).length,
      color: "#5da88a",
    },
    {
      name: "Medium",
      value: cases.filter(
        (item) =>
          (item.fused_risk ?? 0) >= 0.45 && (item.fused_risk ?? 0) < 0.75,
      ).length,
      color: "#dda348",
    },
    {
      name: "High",
      value: cases.filter((item) => (item.fused_risk ?? 0) >= 0.75).length,
      color: "#df6d62",
    },
  ];
  return (
    <div className="page">
      <PageIntro
        eyebrow="Good morning, Alex"
        title="Risk at a glance"
        description="A focused view of the customers and activity that need your attention."
        action={
          <button className="button button-light" onClick={reload}>
            <RefreshCw size={16} /> Refresh data
          </button>
        }
      />
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading ? (
        <DashboardSkeleton />
      ) : (
        <>
          <section className="stat-grid">
            <StatCard
              label="Total cases"
              value={stats.total}
              detail="Active in workspace"
              icon={BriefcaseBusiness}
              tone="coral"
            />
            <StatCard
              label="High risk cases"
              value={stats.high}
              detail={
                stats.total
                  ? `${Math.round((stats.high / stats.total) * 100)}% of total cases`
                  : "No cases yet"
              }
              icon={AlertTriangle}
              tone="red"
            />
            <StatCard
              label="Under review"
              value={stats.review}
              detail="Awaiting analyst action"
              icon={ClipboardCheck}
              tone="amber"
            />
            <StatCard
              label="Average risk score"
              value={formatRisk(stats.avg)}
              detail="Across all case signals"
              icon={Gauge}
              tone="blue"
            />
          </section>
          <div className="dashboard-grid">
            <section className="card chart-card">
              <div className="card-heading">
                <div>
                  <h3>Risk overview</h3>
                  <p>Current case distribution by fused score</p>
                </div>
                <span className="live-dot">Live</span>
              </div>
              <div className="risk-chart-wrap">
                {cases.length ? (
                  <>
                    <ResponsiveContainer width="48%" height={190}>
                      <PieChart>
                        <Pie
                          data={distribution}
                          dataKey="value"
                          innerRadius={54}
                          outerRadius={78}
                          paddingAngle={4}
                          stroke="none"
                        >
                          {distribution.map((entry) => (
                            <Cell key={entry.name} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(value) => [`${value} cases`, "Count"]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="legend-list">
                      {distribution.map((entry) => (
                        <div className="legend-row" key={entry.name}>
                          <span className="legend-label">
                            <i style={{ background: entry.color }} />
                            {entry.name}
                          </span>
                          <strong>{entry.value}</strong>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <EmptyState
                    title="No risk data yet"
                    text="Cases will appear here once they are available."
                  />
                )}
              </div>
            </section>
            <section className="card chart-card">
              <div className="card-heading">
                <div>
                  <h3>Cases over time</h3>
                  <p>Case volume from the current API snapshot</p>
                </div>
                <span className="chart-period">
                  All cases <ChevronDown size={14} />
                </span>
              </div>
              <div className="area-chart">
                {cases.length ? (
                  <ResponsiveContainer width="100%" height={205}>
                    <AreaChart
                      data={cases
                        .slice()
                        .reverse()
                        .map((item, index) => ({
                          label: `Case ${index + 1}`,
                          risk: Math.round((item.fused_risk ?? 0) * 100),
                        }))}
                    >
                      <defs>
                        <linearGradient
                          id="riskFill"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#ff6545"
                            stopOpacity={0.28}
                          />
                          <stop
                            offset="100%"
                            stopColor="#ff6545"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} stroke="#ecece8" />
                      <XAxis dataKey="label" hide />
                      <YAxis
                        domain={[0, 100]}
                        tickFormatter={(value) => `${value}%`}
                        width={37}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: "#999991", fontSize: 11 }}
                      />
                      <Tooltip formatter={(value) => [`${value}%`, "Risk"]} />
                      <Area
                        type="monotone"
                        dataKey="risk"
                        stroke="#ff6545"
                        strokeWidth={2.5}
                        fill="url(#riskFill)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    title="No timeline data yet"
                    text="The chart will populate from live cases."
                  />
                )}
              </div>
            </section>
          </div>
          <section className="card priority-card">
            <div className="card-heading">
              <div>
                <h3>Priority cases</h3>
                <p>Highest risk cases requiring a closer look</p>
              </div>
              <Link className="text-link" to="/cases">
                View all cases <ArrowUpRight size={15} />
              </Link>
            </div>
            <CaseList
              cases={cases
                .slice()
                .sort((a, b) => (b.fused_risk ?? 0) - (a.fused_risk ?? 0))
                .slice(0, 5)}
            />
          </section>
        </>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string | number;
  detail: string;
  icon: typeof Gauge;
  tone: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}>
        <Icon size={19} />
      </div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <span className="stat-detail">
          <ArrowUpRight size={13} />
          {detail}
        </span>
      </div>
    </div>
  );
}

function CasesPage() {
  const { cases, loading, error, reload } = useCases();
  const navigate = useNavigate();
  const [addCaseOpen, setAddCaseOpen] = useState(false);
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState(() => searchParams.get("query") ?? "");
  const [priority, setPriority] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [sortDesc, setSortDesc] = useState(true);
  const filtered = cases
    .filter(
      (item) =>
        `${item.case_id} ${item.customer_id} ${item.suspected_typology}`
          .toLowerCase()
          .includes(query.toLowerCase()) &&
        (priority === "ALL" || item.priority === priority) &&
        (status === "ALL" || item.status === status),
    )
    .sort((a, b) =>
      sortDesc
        ? (b.fused_risk ?? 0) - (a.fused_risk ?? 0)
        : (a.fused_risk ?? 0) - (b.fused_risk ?? 0),
    );
  return (
    <div className="page">
      <PageIntro
        eyebrow="Investigation queue"
        title="Cases"
        description="Review model-prioritized customer activity and make the next decision."
        action={
          <div className="page-actions">
            <button
              className="button button-primary"
              onClick={() => setAddCaseOpen(true)}
            >
              <Plus size={16} /> Add case
            </button>
            <button className="button button-light" onClick={reload}>
              <RefreshCw size={16} /> Refresh
            </button>
          </div>
        }
      />
      {addCaseOpen && (
        <AddCaseModal
          onClose={() => setAddCaseOpen(false)}
          onCreated={(createdCase) => navigate(`/cases/${createdCase.case_id}`)}
        />
      )}
      {error && <ErrorState message={error} onRetry={reload} />}
      {loading ? (
        <TableSkeleton />
      ) : (
        <section className="card case-table-card">
          <div className="table-toolbar">
            <div className="case-search">
              <Search size={16} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search case, customer, or typology"
              />
            </div>
            <div className="filter-set">
              <select
                value={priority}
                onChange={(event) => setPriority(event.target.value)}
              >
                <option value="ALL">All priorities</option>
                <option value="HIGH">High priority</option>
                <option value="MEDIUM">Medium priority</option>
                <option value="LOW">Low priority</option>
              </select>
              <select
                value={status}
                onChange={(event) => setStatus(event.target.value)}
              >
                <option value="ALL">All statuses</option>
                <option value="OPEN">Open</option>
                <option value="UNDER_REVIEW">Under review</option>
                <option value="CLOSED">Closed</option>
              </select>
              <button
                className={`filter-button ${sortDesc ? "active" : ""}`}
                onClick={() => setSortDesc(!sortDesc)}
              >
                <SlidersHorizontal size={15} /> Risk{" "}
                {sortDesc ? "high to low" : "low to high"}
              </button>
            </div>
          </div>
          {filtered.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Case / customer</th>
                    <th>Fused risk</th>
                    <th>KYC / AML</th>
                    <th>Uncertainty</th>
                    <th>Typology</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((item) => (
                    <tr
                      key={item.case_id}
                      className={item.priority === "HIGH" ? "high-row" : ""}
                    >
                      <td>
                        <Link
                          className="case-cell"
                          to={`/cases/${item.case_id}`}
                        >
                          <strong>{item.case_id}</strong>
                          <span>{item.customer_id ?? "Unknown customer"}</span>
                        </Link>
                      </td>
                      <td>
                        <strong className="risk-number">
                          {formatRisk(item.fused_risk)}
                        </strong>
                      </td>
                      <td>
                        <span className="dual-risk">
                          {formatRisk(item.kyc_risk)} <i>/</i>{" "}
                          {formatRisk(item.aml_risk)}
                        </span>
                      </td>
                      <td>{formatRisk(item.uncertainty)}</td>
                      <td>
                        <span className="typology">
                          {titleCase(item.suspected_typology)}
                        </span>
                      </td>
                      <td>
                        <RiskBadge value={item.priority} />
                      </td>
                      <td>
                        <StatusBadge value={item.status} />
                      </td>
                      <td>
                        <Link
                          className="row-arrow"
                          to={`/cases/${item.case_id}`}
                        >
                          <ArrowUpRight size={16} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              title="No matching cases"
              text="Try adjusting the search or filters."
            />
          )}
        </section>
      )}
    </div>
  );
}

type KYCForm = {
  customer_id: string;
  document_tamper_probability: string;
  liveness_probability: string;
  deepfake_probability: string;
  kyc_risk: string;
  document_fingerprint: string;
  tamper_mask_path: string;
  evidence_ids: string;
};

const emptyKYCForm: KYCForm = {
  customer_id: "",
  document_tamper_probability: "",
  liveness_probability: "",
  deepfake_probability: "",
  kyc_risk: "",
  document_fingerprint: "",
  tamper_mask_path: "",
  evidence_ids: "",
};

function AddCaseModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (caseData: CaseRecord) => void;
}) {
  const [form, setForm] = useState<KYCForm>(emptyKYCForm);
  const [validationError, setValidationError] = useState("");
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const updateField = (field: keyof KYCForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setValidationError("");
    setApiError("");
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const probabilityFields = [
      ["document_tamper_probability", form.document_tamper_probability],
      ["liveness_probability", form.liveness_probability],
      ["deepfake_probability", form.deepfake_probability],
      ["kyc_risk", form.kyc_risk],
    ] as const;
    const invalidProbability = probabilityFields.find(([, value]) => {
      const numericValue = Number(value);
      return (
        value.trim() === "" ||
        !Number.isFinite(numericValue) ||
        numericValue < 0 ||
        numericValue > 1
      );
    });
    if (
      !form.customer_id.trim() ||
      !form.document_fingerprint.trim() ||
      !form.evidence_ids.trim()
    ) {
      setValidationError(
        "Customer ID, document fingerprint, and at least one evidence ID are required.",
      );
      return;
    }
    if (invalidProbability) {
      setValidationError(
        `${titleCase(invalidProbability[0])} must be a number between 0 and 1.`,
      );
      return;
    }
    const kycData: KYCResponse = {
      customer_id: form.customer_id.trim(),
      document_tamper_probability: Number(form.document_tamper_probability),
      liveness_probability: Number(form.liveness_probability),
      deepfake_probability: Number(form.deepfake_probability),
      kyc_risk: Number(form.kyc_risk),
      document_fingerprint: form.document_fingerprint.trim(),
      tamper_mask_path: form.tamper_mask_path.trim() || null,
      evidence_ids: form.evidence_ids
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
    };
    setSubmitting(true);
    setApiError("");
    try {
      onCreated(await createCase(kycData));
    } catch {
      setApiError(
        "The case could not be created. Check the backend connection and submitted values.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-case-title"
      >
        <div className="modal-heading">
          <div>
            <p className="eyebrow accent-text">New investigation</p>
            <h3 id="add-case-title">Add case</h3>
            <p>
              Submit the KYC assessment fields accepted by the case service.
            </p>
          </div>
          <button
            className="icon-button modal-close"
            type="button"
            onClick={onClose}
            aria-label="Close add case form"
          >
            <X size={18} />
          </button>
        </div>
        <form onSubmit={submit} className="case-form">
          <div className="form-grid">
            <FormField label="Customer ID" required>
              <input
                value={form.customer_id}
                onChange={(event) =>
                  updateField("customer_id", event.target.value)
                }
                placeholder="Customer identifier"
              />
            </FormField>
            <FormField label="Document fingerprint" required>
              <input
                value={form.document_fingerprint}
                onChange={(event) =>
                  updateField("document_fingerprint", event.target.value)
                }
                placeholder="Fingerprint value"
              />
            </FormField>
            <FormField label="Document tamper probability" required>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={form.document_tamper_probability}
                onChange={(event) =>
                  updateField("document_tamper_probability", event.target.value)
                }
                placeholder="0.00 - 1.00"
              />
            </FormField>
            <FormField label="Liveness probability" required>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={form.liveness_probability}
                onChange={(event) =>
                  updateField("liveness_probability", event.target.value)
                }
                placeholder="0.00 - 1.00"
              />
            </FormField>
            <FormField label="Deepfake probability" required>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={form.deepfake_probability}
                onChange={(event) =>
                  updateField("deepfake_probability", event.target.value)
                }
                placeholder="0.00 - 1.00"
              />
            </FormField>
            <FormField label="KYC risk" required>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={form.kyc_risk}
                onChange={(event) =>
                  updateField("kyc_risk", event.target.value)
                }
                placeholder="0.00 - 1.00"
              />
            </FormField>
            <FormField label="Tamper mask path">
              <input
                value={form.tamper_mask_path}
                onChange={(event) =>
                  updateField("tamper_mask_path", event.target.value)
                }
                placeholder="Optional path"
              />
            </FormField>
            <FormField label="Evidence IDs" hint="Comma-separated" required>
              <input
                value={form.evidence_ids}
                onChange={(event) =>
                  updateField("evidence_ids", event.target.value)
                }
                placeholder="evidence-01, evidence-02"
              />
            </FormField>
          </div>
          {(validationError || apiError) && (
            <div className="form-error" role="alert">
              <AlertTriangle size={15} />
              {validationError || apiError}
            </div>
          )}
          <div className="modal-actions">
            <button
              className="button button-light"
              type="button"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              className="button button-primary"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Creating case..." : "Create case"}
              <ArrowUpRight size={15} />
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function FormField({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="form-field">
      <span>
        {label}
        {required && <b>*</b>}
        {hint && <small>{hint}</small>}
      </span>
      {children}
    </label>
  );
}

function CaseList({ cases }: { cases: CaseRecord[] }) {
  return cases.length ? (
    <div className="priority-list">
      {cases.map((item) => (
        <Link
          className="priority-row"
          to={`/cases/${item.case_id}`}
          key={item.case_id}
        >
          <div className={`priority-avatar ${riskClass(item.priority)}`}>
            {(item.case_id || "C").slice(-2)}
          </div>
          <div className="priority-info">
            <strong>{item.case_id}</strong>
            <span>
              {item.customer_id} · {titleCase(item.suspected_typology)}
            </span>
          </div>
          <div className="priority-score">
            <strong>{formatRisk(item.fused_risk)}</strong>
            <RiskBadge value={item.priority} />
          </div>
          <ArrowUpRight size={16} className="muted-icon" />
        </Link>
      ))}
    </div>
  ) : (
    <EmptyState
      title="No cases available"
      text="The priority queue is empty."
    />
  );
}

function RiskBadge({ value }: { value: string | null | undefined }) {
  return (
    <span className={`badge risk-badge ${riskClass(value)}`}>
      {titleCase(value)}
    </span>
  );
}
function StatusBadge({ value }: { value: string | null | undefined }) {
  return (
    <span className={`badge status-badge ${statusClass(value)}`}>
      <i />
      {titleCase(value)}
    </span>
  );
}
function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <CircleHelp size={20} />
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}
function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="error-state">
      <AlertTriangle size={19} />
      <span>{message}</span>
      <button onClick={onRetry}>Retry</button>
    </div>
  );
}
function DashboardSkeleton() {
  return (
    <>
      <div className="stat-grid">
        {[1, 2, 3, 4].map((item) => (
          <div className="skeleton stat-card" key={item}>
            <div />
            <div />
          </div>
        ))}
      </div>
      <div className="dashboard-grid">
        <div className="skeleton chart-card" />
        <div className="skeleton chart-card" />
      </div>
      <div className="skeleton priority-card" />
    </>
  );
}
function TableSkeleton() {
  return <div className="skeleton table-skeleton" />;
}

function DetailSkeleton() {
  return (
    <div className="detail-skeleton">
      <div className="skeleton detail-skeleton-back" />
      <div className="skeleton detail-skeleton-header" />
      <div className="detail-skeleton-grid">
        <div className="skeleton detail-skeleton-card" />
        <div className="skeleton detail-skeleton-card" />
        <div className="skeleton detail-skeleton-card detail-skeleton-wide" />
        <div className="skeleton detail-skeleton-card detail-skeleton-wide" />
      </div>
    </div>
  );
}

function CaseDetail() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<CaseRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusSaving, setStatusSaving] = useState(false);
  const [feedbackSaving, setFeedbackSaving] = useState(false);
  const [decision, setDecision] = useState<AnalystDecision>("CONFIRMED");
  const [comment, setComment] = useState("");
  const [notice, setNotice] = useState<{
    kind: "success" | "error";
    message: string;
  } | null>(null);
  const retryCase = () => {
    if (!caseId) return;
    setLoading(true);
    setError("");
    getCase(caseId)
      .then(setCaseData)
      .catch((requestError: Error & { status?: number }) =>
        setError(
          requestError.status === 404
            ? "This case does not exist."
            : "Unable to load this case from the backend.",
        ),
      )
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    if (!caseId) return;
    getCase(caseId)
      .then(setCaseData)
      .catch((requestError: Error & { status?: number }) =>
        setError(
          requestError.status === 404
            ? "This case does not exist."
            : "Unable to load this case from the backend.",
        ),
      )
      .finally(() => setLoading(false));
  }, [caseId]);
  const changeStatus = async (status: CaseStatus) => {
    if (!caseData) return;
    setStatusSaving(true);
    try {
      setCaseData(await updateCaseStatus(caseData.case_id, status));
      setNotice({
        kind: "success",
        message: `Case marked ${titleCase(status)}.`,
      });
    } catch {
      setNotice({ kind: "error", message: "Status could not be updated." });
    } finally {
      setStatusSaving(false);
    }
  };
  const submitFeedback = async () => {
    if (!caseData) return;
    setFeedbackSaving(true);
    try {
      setCaseData(
        await submitCaseFeedback(caseData.case_id, {
          analyst_decision: decision,
          comment: comment || null,
        }),
      );
      setNotice({ kind: "success", message: "Analyst feedback submitted." });
      setComment("");
      setDecision("CONFIRMED");
    } catch {
      setNotice({ kind: "error", message: "Feedback could not be submitted." });
    } finally {
      setFeedbackSaving(false);
    }
  };
  if (loading)
    return (
      <div className="page">
        <DetailSkeleton />
      </div>
    );
  if (error || !caseData)
    return (
      <div className="page">
        <button className="back-link" onClick={() => navigate("/cases")}>
          <ChevronLeft size={16} /> Back to cases
        </button>
        <div className="detail-error">
          <AlertTriangle size={24} />
          <h2>{error || "Case not found"}</h2>
          <p>We could not find the requested case.</p>
          {error && (
            <button className="button button-light" onClick={retryCase}>
              <RefreshCw size={15} /> Retry loading case
            </button>
          )}
        </div>
      </div>
    );
  return (
    <div className="page detail-page">
      <button className="back-link" onClick={() => navigate("/cases")}>
        <ChevronLeft size={16} /> Back to cases
      </button>
      <div className="detail-header">
        <div>
          <div className="case-title-line">
            <span className="case-kicker">CASE</span>
            <span className="case-id">{caseData.case_id}</span>
            <RiskBadge value={caseData.priority} />
            <StatusBadge value={caseData.status} />
          </div>
          <h2>Investigation brief</h2>
          <p>
            Customer ID <strong>{caseData.customer_id ?? "Unknown"}</strong> ·
            Model-assisted case review
          </p>
        </div>
        <div className="header-risk-score">
          <span>Fused risk</span>
          <strong>{formatRisk(caseData.fused_risk)}</strong>
          <small>Priority signal</small>
        </div>
        <div className="detail-actions">
          <button
            className="button button-light"
            onClick={() => navigate(`/cases/${caseData.case_id}/sar`)}
          >
            <FileSearch size={16} /> SAR review
          </button>
          <select
            value={caseData.status}
            disabled={statusSaving || feedbackSaving}
            onChange={(event) => changeStatus(event.target.value as CaseStatus)}
          >
            <option value="OPEN">Open</option>
            <option value="UNDER_REVIEW">Under review</option>
            <option value="CLOSED">Closed</option>
          </select>
          <button
            className="button button-dark"
            disabled={
              statusSaving ||
              feedbackSaving ||
              caseData.status === "UNDER_REVIEW"
            }
            onClick={() => changeStatus("UNDER_REVIEW")}
          >
            <ClipboardCheck size={16} /> Mark under review
          </button>
        </div>
      </div>
      {notice && (
        <div className={`toast ${notice.kind}`} role="status">
          {notice.kind === "success" ? (
            <Check size={16} />
          ) : (
            <AlertTriangle size={16} />
          )}
          {notice.message}
        </div>
      )}
      <div className="detail-grid">
        <section className="card risk-summary">
          <CardTitle
            title="Risk Assessment"
            caption="Signals aggregated by the model"
          />
          <div className="gauge-grid">
            <RiskGauge
              label="Fused risk"
              value={caseData.fused_risk}
              tone="coral"
            />
            <RiskGauge label="KYC risk" value={caseData.kyc_risk} tone="blue" />
            <RiskGauge
              label="AML risk"
              value={caseData.aml_risk}
              tone="amber"
            />
            <RiskGauge
              label="Uncertainty"
              value={caseData.uncertainty}
              tone="gray"
            />
          </div>
        </section>
        <section className="card signals-card">
          <CardTitle title="Risk signals" caption="Contributing indicators" />
          <div className="signal-list">
            <Signal
              label="KYC risk"
              value={formatRisk(caseData.kyc_risk)}
              icon={ShieldCheck}
            />
            <Signal
              label="AML risk"
              value={formatRisk(caseData.aml_risk)}
              icon={Network}
            />
            <Signal
              label="Uncertainty"
              value={formatRisk(caseData.uncertainty)}
              icon={CircleHelp}
            />
            <Signal
              label="Suspected typology"
              value={titleCase(caseData.suspected_typology)}
              icon={GitBranch}
            />
            <Signal
              label="Human review"
              value={
                caseData.human_review_required ? "Required" : "Not required"
              }
              icon={UserRound}
            />
            <Signal
              label="Model confidence"
              value={formatRisk(1 - (caseData.uncertainty ?? 0))}
              icon={Gauge}
            />
          </div>
        </section>
        <section className="card shap-card">
          <CardTitle
            title="Why was this case flagged?"
            caption="SHAP feature importance · model explanation"
          />
          <div className="shap-list">
            {(caseData.shap_features ?? []).length ? (
              caseData.shap_features
                ?.slice()
                .sort((a, b) => b.importance - a.importance)
                .map((feature) => (
                  <div className="shap-row" key={feature.feature}>
                    <div className="shap-meta">
                      <span>{titleCase(feature.feature)}</span>
                      <strong>{formatImportance(feature.importance)}</strong>
                    </div>
                    <div className="shap-track">
                      <i
                        style={{
                          width: `${Math.min(feature.importance * 100 * 2.4, 100)}%`,
                        }}
                      />
                    </div>
                    <span className="shap-value">
                      Value{" "}
                      {typeof feature.value === "number"
                        ? feature.value.toFixed(2)
                        : feature.value}
                    </span>
                  </div>
                ))
            ) : (
              <EmptyState
                title="No feature explanations"
                text="This case has no SHAP data."
              />
            )}
          </div>
        </section>
        <section className="card graph-card">
          <CardTitle
            title="AML Network"
            caption="Interactive transaction relationships from the AML model"
          />
          <AMLGraph graph={caseData.graph_explanation} />
        </section>
        <ReviewCard
          decision={decision}
          setDecision={setDecision}
          comment={comment}
          setComment={setComment}
          submit={submitFeedback}
          saving={feedbackSaving}
        />
      </div>
    </div>
  );
}

function CardTitle({ title, caption }: { title: string; caption: string }) {
  return (
    <div className="card-heading">
      <div>
        <h3>{title}</h3>
        <p>{caption}</p>
      </div>
      <CircleHelp size={17} className="muted-icon" />
    </div>
  );
}
function RiskGauge({
  label,
  value,
  tone,
}: {
  label: string;
  value: number | null;
  tone: string;
}) {
  return (
    <div className="risk-gauge">
      <div className="gauge-top">
        <span>{label}</span>
        <strong>{formatRisk(value)}</strong>
      </div>
      <div className="gauge-track">
        <i
          className={tone}
          style={{ width: `${Math.min((value ?? 0) * 100, 100)}%` }}
        />
      </div>
    </div>
  );
}
function Signal({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof Gauge;
}) {
  return (
    <div className="signal-row">
      <div className="signal-icon">
        <Icon size={16} />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
function ReviewCard({
  decision,
  setDecision,
  comment,
  setComment,
  submit,
  saving,
}: {
  decision: AnalystDecision;
  setDecision: (value: AnalystDecision) => void;
  comment: string;
  setComment: (value: string) => void;
  submit: () => void;
  saving: boolean;
}) {
  return (
    <section className="card review-card">
      <CardTitle
        title="Analyst review"
        caption="Record your decision for this case"
      />
      <div className="decision-options">
        {[
          ["CONFIRMED", "Confirm suspicious"],
          ["FALSE_POSITIVE", "False positive"],
          ["NEEDS_MORE_INVESTIGATION", "Needs more investigation"],
        ].map(([value, label]) => (
          <button
            className={decision === value ? "selected" : ""}
            key={value}
            type="button"
            onClick={() => setDecision(value as AnalystDecision)}
          >
            {decision === value ? <Check size={15} /> : <span />} {label}
          </button>
        ))}
      </div>
      <textarea
        value={comment}
        onChange={(event) => setComment(event.target.value)}
        placeholder="Add context for the next analyst (optional)"
      />
      <button
        className="button button-dark submit-button"
        disabled={saving}
        onClick={submit}
      >
        {saving ? "Submitting..." : "Submit review"}
        <ArrowUpRight size={16} />
      </button>
    </section>
  );
}
function NotFound() {
  return (
    <div className="page">
      <div className="detail-error">
        <CircleHelp size={24} />
        <h2>Page not found</h2>
        <p>That workspace view does not exist.</p>
        <Link className="button button-dark" to="/">
          Return to overview
        </Link>
      </div>
    </div>
  );
}

export default App;
