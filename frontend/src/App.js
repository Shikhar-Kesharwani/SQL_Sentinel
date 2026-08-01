import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import sql from "react-syntax-highlighter/dist/esm/languages/hljs/sql";
import { githubGist } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

SyntaxHighlighter.registerLanguage("sql", sql);

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8080";
const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function DashboardManager({ onClose }) {
  const [dashboards, setDashboards] = useState([]);

  const fetchDashboards = async () => {
    try {
      const res = await axios.get(`${API}/v1/dashboards`);
      setDashboards(res.data.dashboards);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDashboards();
  }, []);

  const handleDelete = async (id) => {
    await axios.delete(`${API}/v1/dashboards/${id}`);
    fetchDashboards();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ width: 900, maxHeight: "80vh", overflow: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
          <h2 style={{ margin: 0 }}>📊 Saved Dashboards</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer" }}>&times;</button>
        </div>
        
        {dashboards.length === 0 ? (
          <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}>No dashboards saved yet.</div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            {dashboards.map(dash => (
              <div key={dash.id} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 16, background: "#f8fafc" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <h3 style={{ margin: 0, fontSize: 16 }}>{dash.title}</h3>
                  <button onClick={() => handleDelete(dash.id)} style={{ color: "#ef4444", background: "none", border: "none", cursor: "pointer" }}>Delete</button>
                </div>
                <div style={{ fontSize: 12, color: "#64748b", marginBottom: 12 }}>Q: {dash.question}</div>
                <div style={{ background: "#fff", padding: 8, borderRadius: 8, border: "1px solid #e2e8f0" }}>
                  <ChartRenderer config={dash.chart_config} data={dash.data} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DatabaseConnection({ onClose, onConnected }) {
  const [dbPath, setDbPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentDb, setCurrentDb] = useState("");

  useEffect(() => {
    axios.get(`${API}/v1/connect`).then(res => setCurrentDb(res.data.db_path)).catch(() => {});
  }, []);

  const handleConnect = async () => {
    if (!dbPath) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API}/v1/connect`, { db_path: dbPath });
      setCurrentDb(res.data.db_path);
      alert(`Connected! Found ${res.data.tables_found} tables.`);
      if (onConnected) onConnected();
      setDbPath("");
    } catch (e) {
      alert("Failed to connect. Check path.");
    }
    setLoading(false);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ width: 500 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>🗄️ Database Connection</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer" }}>&times;</button>
        </div>
        
        <div style={{ marginBottom: 20, padding: 12, background: "#f1f5f9", borderRadius: 8 }}>
          <strong>Current Active DB:</strong><br/>
          <code style={{ fontSize: 12, wordBreak: "break-all" }}>{currentDb || "Loading..."}</code>
        </div>

        <h3 style={{ margin: "0 0 12px 0", fontSize: 14 }}>Connect New SQLite Database</h3>
        <input 
          placeholder="C:\path\to\your\database.sqlite" 
          value={dbPath} 
          onChange={e => setDbPath(e.target.value)} 
          style={{ padding: 8, marginBottom: 12, width: "100%", borderRadius: 6, border: "1px solid #cbd5e1" }} 
        />
        <button onClick={handleConnect} disabled={loading} style={{ background: "var(--primary-color)", color: "white", padding: "8px 16px", border: "none", borderRadius: 6, cursor: "pointer", width: "100%" }}>
          {loading ? "Connecting & Extracting Schema..." : "Connect"}
        </button>
      </div>
    </div>
  );
}

function ContextManager({ onClose }) {
  const [contextData, setContextData] = useState([]);
  const [type, setType] = useState("sql");
  const [question, setQuestion] = useState("");
  const [sqlQuery, setSqlQuery] = useState("");
  const [docText, setDocText] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchContext = async () => {
    try {
      const res = await axios.get(`${API}/v1/context`);
      setContextData(res.data.context);
    } catch (e) {
      console.error("Failed to fetch context", e);
    }
  };

  useEffect(() => {
    fetchContext();
  }, []);

  const handleAdd = async () => {
    if (type === "sql" && (!question || !sqlQuery)) return;
    if (type === "doc" && !docText) return;
    
    setLoading(true);
    try {
      await axios.post(`${API}/v1/context`, {
        type, question, sql: sqlQuery, doc_text: docText
      });
      setQuestion("");
      setSqlQuery("");
      setDocText("");
      fetchContext();
    } catch (e) {
      console.error(e);
      alert("Failed to add context");
    }
    setLoading(false);
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/v1/context/${id}`);
      fetchContext();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ width: 800, maxHeight: "80vh", overflow: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>🧠 Context Manager (RAG Training)</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer" }}>&times;</button>
        </div>
        
        <div style={{ marginBottom: 24, padding: 16, backgroundColor: "#f8fafc", borderRadius: 8 }}>
          <h3 style={{ margin: "0 0 12px 0" }}>Add New Training Data</h3>
          <select value={type} onChange={e => setType(e.target.value)} style={{ padding: 8, marginBottom: 12, width: "100%", borderRadius: 6, border: "1px solid #cbd5e1" }}>
            <option value="sql">SQL Example (Question -> SQL)</option>
            <option value="doc">Documentation (Rules/Context)</option>
          </select>
          
          {type === "sql" ? (
            <>
              <input placeholder="Example Question" value={question} onChange={e => setQuestion(e.target.value)} style={{ padding: 8, marginBottom: 12, width: "100%", borderRadius: 6, border: "1px solid #cbd5e1" }} />
              <textarea placeholder="Correct SQL Query" value={sqlQuery} onChange={e => setSqlQuery(e.target.value)} rows={4} style={{ padding: 8, marginBottom: 12, width: "100%", borderRadius: 6, border: "1px solid #cbd5e1" }} />
            </>
          ) : (
            <textarea placeholder="Documentation (e.g. 'Revenue is calculated as quantity * price')" value={docText} onChange={e => setDocText(e.target.value)} rows={4} style={{ padding: 8, marginBottom: 12, width: "100%", borderRadius: 6, border: "1px solid #cbd5e1" }} />
          )}
          
          <button onClick={handleAdd} disabled={loading} style={{ background: "var(--primary-color)", color: "white", padding: "8px 16px", border: "none", borderRadius: 6, cursor: "pointer" }}>
            {loading ? "Adding..." : "Add to Vector Store"}
          </button>
        </div>

        <h3>Current Training Data ({contextData.length})</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {contextData.map(item => (
            <div key={item.id} style={{ padding: 12, border: "1px solid #e2e8f0", borderRadius: 8, display: "flex", justifyContent: "space-between" }}>
              <div>
                <span className="badge badge-info">{item.type.toUpperCase()}</span>
                {item.type === "sql" ? (
                  <div style={{ marginTop: 8 }}>
                    <strong>Q:</strong> {item.question}<br/>
                    <code style={{ background: "#f1f5f9", padding: 4, borderRadius: 4, marginTop: 4, display: "inline-block" }}>{item.sql}</code>
                  </div>
                ) : (
                  <div style={{ marginTop: 8 }}>{item.doc_text}</div>
                )}
              </div>
              <button onClick={() => handleDelete(item.id)} style={{ background: "#fee2e2", color: "#ef4444", border: "none", borderRadius: 4, padding: "4px 8px", cursor: "pointer", height: 32 }}>Delete</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ResultTable({ columns, rows }) {
  const downloadCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," 
      + columns.map(c => `"${c}"`).join(",") + "\n"
      + rows.map(e => e.map(v => `"${v !== null ? v : ''}"`).join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "sql_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="data-table-container">
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
        <button onClick={downloadCSV} style={{ padding: "4px 12px", fontSize: 12, background: "#10b981", color: "white", border: "none", borderRadius: 4, cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}>
          <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
          CSV
        </button>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>{cell === null ? <span style={{color: '#9ca3af'}}>null</span> : String(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartRenderer({ config, data }) {
  if (!config || config.type === "none" || !data || data.length === 0) return null;
  const { type, x_key, y_key } = config;

  let processedData = data;
  if (type === "pie" && data.length > 8) {
    const sorted = [...data].sort((a, b) => (Number(b[y_key]) || 0) - (Number(a[y_key]) || 0));
    const top = sorted.slice(0, 7);
    const otherSum = sorted.slice(7).reduce((sum, item) => sum + (Number(item[y_key]) || 0), 0);
    processedData = [...top, { [x_key]: "Other", [y_key]: otherSum }];
  }

  const tooltipFormatter = (value) => typeof value === 'number' ? Number(value.toFixed(2)) : value;

  const downloadChart = () => {
    const svg = document.querySelector('.chart-container svg');
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.fillStyle = "white";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      const a = document.createElement("a");
      a.download = "chart_export.png";
      a.href = canvas.toDataURL("image/png");
      a.click();
    };
    img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
  };

  return (
    <div className="chart-wrapper" style={{ position: "relative", marginTop: 12 }}>
      <button onClick={downloadChart} style={{ position: "absolute", top: -8, right: 0, zIndex: 10, padding: "4px 12px", fontSize: 12, background: "#10b981", color: "white", border: "none", borderRadius: 4, cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}>
        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
        PNG
      </button>
      <div className="chart-container" style={{ height: 350, marginTop: 24 }}>
        <ResponsiveContainer width="100%" height="100%">
        {type === "bar" ? (
          <BarChart data={processedData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis dataKey={x_key} stroke="#6b7280" tick={{fontSize: 12}} />
            <YAxis stroke="#6b7280" tick={{fontSize: 12}} />
            <Tooltip formatter={tooltipFormatter} contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)' }} />
            <Legend wrapperStyle={{fontSize: 12, paddingTop: 10}}/>
            <Bar dataKey={y_key} fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        ) : type === "line" ? (
          <LineChart data={processedData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis dataKey={x_key} stroke="#6b7280" tick={{fontSize: 12}} />
            <YAxis stroke="#6b7280" tick={{fontSize: 12}} />
            <Tooltip formatter={tooltipFormatter} contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)' }} />
            <Legend wrapperStyle={{fontSize: 12, paddingTop: 10}}/>
            <Line type="monotone" dataKey={y_key} stroke="#10b981" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
          </LineChart>
        ) : type === "pie" ? (
          <PieChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <Tooltip formatter={tooltipFormatter} contentStyle={{ borderRadius: 8, border: 'none', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)' }} />
            <Legend wrapperStyle={{fontSize: 12}}/>
            <Pie data={processedData} dataKey={y_key} nameKey={x_key} cx="50%" cy="50%" outerRadius={110} fill="#3b82f6" stroke="none">
              {processedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        ) : null}
      </ResponsiveContainer>
      </div>
    </div>
  );
}

function SqlAccordion({ sql, onExecute }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedSql, setEditedSql] = useState(sql);
  
  if (!sql) return null;
  return (
    <div>
      <div className="accordion-header" onClick={() => setIsOpen(!isOpen)}>
        <span>Generated SQL</span>
        <span>{isOpen ? '▲' : '▼'}</span>
      </div>
      {isOpen && (
        <div className="accordion-content" style={{ background: "#fff", padding: 16 }}>
          {isEditing ? (
            <textarea 
              value={editedSql} 
              onChange={e => setEditedSql(e.target.value)} 
              style={{ width: "100%", height: 120, padding: 12, fontFamily: "monospace", border: "1px solid #cbd5e1", borderRadius: 6, boxSizing: "border-box" }} 
            />
          ) : (
            <SyntaxHighlighter language="sql" style={githubGist} customStyle={{ margin: 0, fontSize: 13 }}>
              {sql}
            </SyntaxHighlighter>
          )}
          
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button 
              onClick={() => {
                if (isEditing) {
                   onExecute(editedSql);
                   setIsEditing(false);
                } else {
                   setIsEditing(true);
                   setEditedSql(sql);
                }
              }} 
              style={{ padding: "6px 16px", background: "#3b82f6", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 13, fontWeight: 600 }}>
              {isEditing ? "Run Custom SQL" : "Edit SQL"}
            </button>
            {isEditing && (
              <button 
                onClick={() => setIsEditing(false)} 
                style={{ padding: "6px 16px", background: "#f1f5f9", color: "#64748b", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 13, fontWeight: 600 }}>
                Cancel
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [engine, setEngine] = useState("fast"); 
  const [showContextManager, setShowContextManager] = useState(false);
  const [showDbConnection, setShowDbConnection] = useState(false);
  const [showDashboards, setShowDashboards] = useState(false);
  
  const endOfMessagesRef = useRef(null);
  
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = async () => {
    if (!input.trim()) return;
    
    const userMsg = { role: "user", content: input };
    
    let previousSql = null;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "ai" && messages[i].result?.sql) {
        previousSql = messages[i].result.sql;
        break;
      }
    }

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const endpoint = engine === "fast" ? `${API}/v1/query` : `${API}/v1/query_graph`;
      const res = await axios.post(endpoint, { 
        question: input,
        previous_sql: previousSql
      });
      setMessages(prev => [...prev, { role: "ai", result: res.data }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "ai", result: { error: e.message } }]);
    }
    setLoading(false);
  };

  const handleExample = (q) => {
    setInput(q);
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <img src="/logo.png" alt="SQLSentinel Logo" className="rollable-icon" style={{ width: 32, height: 32, objectFit: "contain", dropShadow: "0 4px 12px rgba(16,185,129,0.5)" }} />
          SQLSentinel
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 12 }}>
          <button className="sidebar-btn" onClick={() => setMessages([])} style={{ background: '#334155' }}>
            + New Chat
          </button>
          
          <div style={{ marginTop: 24, fontSize: 11, textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, letterSpacing: 0.5, marginBottom: 8 }}>
            Workspace
          </div>
          <button className="sidebar-btn" onClick={() => setShowDbConnection(true)} style={{ background: 'transparent' }}>
            🗄️ Database Connection
          </button>
          <button className="sidebar-btn" onClick={() => setShowContextManager(true)} style={{ background: 'transparent' }}>
            🧠 Context Manager
          </button>
          <button className="sidebar-btn" onClick={() => setShowDashboards(true)} style={{ background: 'transparent' }}>
            📊 Saved Dashboards
          </button>
        </div>
      </div>

      <div className="app-container">
        {/* Chat History */}
        <div className="chat-history">
          {messages.length === 0 && !loading && (
            <div style={{ textAlign: "center", marginTop: 60 }}>
              <img src="/logo.png" alt="SQLSentinel Logo" className="rollable-icon" style={{ width: 80, height: 80, objectFit: "contain", marginBottom: 16, filter: "drop-shadow(0 8px 24px rgba(16, 185, 129, 0.4))" }} />
              <h2 className="aesthetic-heading">Welcome to SQLSentinel</h2>
              
              <div className="example-queries">
                <div className="example-card" onClick={() => handleExample("What are the top 10 artists?")}>
                  <div className="example-title">Top 10 artists</div>
                  <div className="example-subtitle">Show me the most popular musicians</div>
                </div>
                <div className="example-card" onClick={() => handleExample("Show me the total revenue by genre as a pie chart")}>
                  <div className="example-title">Revenue by genre</div>
                  <div className="example-subtitle">Visualize sales distribution</div>
                </div>
                <div className="example-card" onClick={() => handleExample("Who are the top customers in the USA?")}>
                  <div className="example-title">Top US Customers</div>
                  <div className="example-subtitle">Find the biggest spenders in America</div>
                </div>
                <div className="example-card" onClick={() => handleExample("How many employees do we have?")}>
                  <div className="example-title">Employee count</div>
                  <div className="example-subtitle">Total staff members</div>
                </div>
              </div>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className="message-row">
              {msg.role === "user" ? (
                <>
                  <div className="avatar user">U</div>
                  <div className="message-content">
                    <div className="user-message">{msg.content}</div>
                  </div>
                </>
              ) : (
                <>
                  <div className="avatar ai" style={{ background: "transparent", boxShadow: "none" }}>
                    <img src="/logo.png" alt="AI" className="rollable-icon" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
                  </div>
                  <div className="message-content">
                    <div className="ai-message">
                      {msg.result.error ? (
                        <div style={{ color: "var(--error)", padding: 12, background: "#fee2e2", borderRadius: 8, border: "1px solid #fca5a5" }}>
                          <strong>Error:</strong> {msg.result.error}
                        </div>
                      ) : msg.result.blocked ? (
                        <div style={{ color: "var(--error)", padding: 12, background: "#fee2e2", borderRadius: 8, border: "1px solid #fca5a5" }}>
                          <strong>Security Block:</strong> {msg.result.block_reason}
                        </div>
                      ) : (
                        <>
                          <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                            {msg.result.hallucination && (
                              <div className={`badge ${msg.result.hallucination.final_confidence > 0.7 ? 'badge-success' : 'badge-warning'}`}>
                                {Math.round(msg.result.hallucination.final_confidence * 100)}% Confidence
                              </div>
                            )}
                            {msg.result.result?.row_count !== undefined && (
                              <div className="badge badge-info">{msg.result.result.row_count} Rows returned</div>
                            )}
                          </div>

                          <SqlAccordion 
                            sql={msg.result.sql} 
                            onExecute={async (customSql) => {
                              try {
                                const res = await axios.post(`${API}/v1/execute_sql`, { sql: customSql });
                                if (res.data.status === "success") {
                                  setMessages(prev => prev.map((m, i) => i === idx ? { ...m, result: { ...m.result, sql: customSql, result: res.data.result } } : m));
                                } else {
                                  alert("SQL Execution Error: " + res.data.result.error);
                                }
                              } catch (e) {
                                alert("Failed to execute SQL");
                              }
                            }} 
                          />

                          {msg.result.result && !msg.result.result.error && (
                            <>
                              {msg.result.chart_config && msg.result.chart_config.type !== "none" && (
                                <>
                                  <ChartRenderer 
                                    config={msg.result.chart_config} 
                                    data={msg.result.result.rows.map(r => 
                                      msg.result.result.columns.reduce((obj, col, i) => { obj[col] = r[i]; return obj; }, {})
                                    )} 
                                  />
                                  <div style={{ textAlign: "right", marginTop: 8, marginBottom: 16 }}>
                                    <button 
                                      onClick={async () => {
                                        const title = prompt("Enter a title for this dashboard widget:");
                                        if (!title) return;
                                        await axios.post(`${API}/v1/dashboards`, {
                                          title,
                                          question: msg.question || "Saved Query",
                                          sql: msg.result.sql,
                                          chart_config: msg.result.chart_config,
                                          data: msg.result.result.rows.map(r => msg.result.result.columns.reduce((obj, col, i) => { obj[col] = r[i]; return obj; }, {}))
                                        });
                                        alert("Saved to Dashboards!");
                                      }}
                                      style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", borderRadius: 4, padding: "4px 12px", cursor: "pointer", fontSize: 12, fontWeight: "bold" }}>
                                      📌 Save to Dashboard
                                    </button>
                                  </div>
                                </>
                              )}
                              <ResultTable columns={msg.result.result.columns} rows={msg.result.result.rows} />
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          ))}
          {loading && (
            <div className="message-row">
              <div className="avatar ai" style={{ background: "transparent", boxShadow: "none" }}>
                <img src="/logo.png" alt="AI" className="rollable-icon" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
              </div>
              <div className="message-content">
                <div className="ai-message" style={{ color: "var(--text-secondary)", paddingTop: 6 }}>
                  Generating SQL and fetching data...
                </div>
              </div>
            </div>
          )}
          <div ref={endOfMessagesRef} />
        </div>

        {/* Input */}
        <div className="input-container">
          <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 4, background: "#f8fafc", padding: "4px", borderRadius: 100, border: "1px solid #e2e8f0" }}>
              <button onClick={() => setEngine("fast")} style={{ padding: "4px 16px", fontSize: 13, borderRadius: 100, border: "none", background: engine === "fast" ? "#fff" : "transparent", boxShadow: engine === "fast" ? "0 1px 4px rgba(0,0,0,0.1)" : "none", color: engine === "fast" ? "#10b981" : "#94a3b8", cursor: "pointer", fontWeight: 600, transition: "all 0.2s" }}>⚡ Fast</button>
              <button onClick={() => setEngine("deep_think")} style={{ padding: "4px 16px", fontSize: 13, borderRadius: 100, border: "none", background: engine === "deep_think" ? "#fff" : "transparent", boxShadow: engine === "deep_think" ? "0 1px 4px rgba(0,0,0,0.1)" : "none", color: engine === "deep_think" ? "#8b5cf6" : "#94a3b8", cursor: "pointer", fontWeight: 600, transition: "all 0.2s" }}>🧠 Deep Think</button>
            </div>
          </div>
          <div className="input-box">
            <input 
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSubmit()}
              placeholder="Ask a question about your database..."
              disabled={loading}
            />
            <button className="send-button" onClick={handleSubmit} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
          <div style={{textAlign: 'center', fontSize: 11, color: '#9ca3af', marginTop: 12}}>
            SQLSentinel AI can make mistakes. Verify critical SQL before running in production.
          </div>
        </div>
      </div>
      
      {showContextManager && <ContextManager onClose={() => setShowContextManager(false)} />}
      {showDbConnection && <DatabaseConnection onClose={() => setShowDbConnection(false)} onConnected={() => setMessages([])} />}
      {showDashboards && <DashboardManager onClose={() => setShowDashboards(false)} />}
    </div>
  );
}
