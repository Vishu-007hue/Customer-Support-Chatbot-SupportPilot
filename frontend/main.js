const API_BASE_URL = window.__API_BASE_URL__ || "http://localhost:8000";
const ADMIN_USERNAME = "admin";
const ADMIN_PASSWORD = "admin123";
const USERS_KEY = "supportpilot_users";
const FEEDBACK_KEY = "supportpilot_feedback";
const QUERY_KEY = "supportpilot_queries";

const { useMemo, useState } = React;

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (_) {
    return fallback;
  }
}

function writeJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function App() {
  const [view, setView] = useState("landing");
  const [authMode, setAuthMode] = useState("login");
  const [user, setUser] = useState(null);
  const [adminToken, setAdminToken] = useState("");
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [feedback, setFeedback] = useState(readJson(FEEDBACK_KEY, []));
  const [queryLog, setQueryLog] = useState(readJson(QUERY_KEY, []));
  const [toasts, setToasts] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  function notify(message, type = "info") {
    const id = `t-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id));
    }, 2600);
  }

  const currentUserQueries = useMemo(
    () => queryLog.filter((item) => user && item.userEmail === user.email),
    [queryLog, user]
  );

  const solvedCount = currentUserQueries.filter((item) => item.status === "solved").length;
  const activeCount = currentUserQueries.filter((item) => item.status === "active").length;

  const adminQueryStats = useMemo(() => {
    const solved = queryLog.filter((q) => q.status === "solved").length;
    return {
      solved,
      active: queryLog.length - solved,
      total: queryLog.length,
    };
  }, [queryLog]);

  function saveQuery(item) {
    const next = [item, ...queryLog];
    setQueryLog(next);
    writeJson(QUERY_KEY, next);
  }

  function registerUser(formData) {
    const users = readJson(USERS_KEY, []);
    if (users.some((item) => item.email === formData.email)) {
      notify("User already exists. Please login.", "error");
      return;
    }
    const nextUser = { ...formData, role: "user" };
    writeJson(USERS_KEY, [...users, nextUser]);
    notify("Signup successful. Please login as user.", "success");
    setAuthMode("login");
  }

  async function loginUser(email, password, role) {
    if (role === "admin") {
      if (email !== ADMIN_USERNAME || password !== ADMIN_PASSWORD) {
        notify("Admin credentials do not match.", "error");
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/api/admin/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: email, password }),
        });
        const data = await res.json();
        if (!data.access_token) {
          notify("Admin API login failed. Start backend first.", "error");
          return;
        }
        setAdminToken(data.access_token);
        setUser({ name: "Primary Admin", email, role: "admin" });
        setView("admin");
        notify("Admin login successful.", "success");
        fetchAnalytics(data.access_token);
      } catch (_) {
        notify("Backend is unreachable for admin login.", "error");
      }
      return;
    }

    const users = readJson(USERS_KEY, []);
    const found = users.find((item) => item.email === email && item.password === password);
    if (!found) {
      notify("Invalid user credentials.", "error");
      return;
    }
    setUser(found);
    setView("chat");
    notify(`Welcome ${found.name}.`, "success");
  }

  function resetPassword(email, newPassword) {
    const users = readJson(USERS_KEY, []);
    const idx = users.findIndex((item) => item.email === email);
    if (idx === -1) {
      notify("No user found with this email.", "error");
      return;
    }
    users[idx].password = newPassword;
    writeJson(USERS_KEY, users);
    notify("Password reset complete. Login with the new password.", "success");
    setAuthMode("login");
  }

  function logout() {
    setUser(null);
    setAdminToken("");
    setView("landing");
    notify("Logged out.", "info");
  }

  async function fetchAnalytics(tokenOverride) {
    const token = tokenOverride || adminToken;
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/analytics/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setAnalytics(data);
    } catch (_) {
      notify("Analytics not available. Check backend.", "error");
    }
  }

  async function sendMessage() {
    if (!message.trim() || !user) return;
    const sessionId = `${user.email}-session`;
    const userText = message.trim();
    setChat((prev) => [...prev, { sender: "user", text: userText }]);
    setMessage("");

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: userText, user_id: user.email }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data?.detail || "Chat request failed.";
        setChat((prev) => [...prev, { sender: "bot", text: `Sorry, I could not process that: ${detail}` }]);
        notify("Message failed.", "error");
        return;
      }

      const reply = typeof data?.reply === "string" && data.reply.trim()
        ? data.reply
        : "I could not understand that. Please rephrase your query.";
      const intent = typeof data?.intent === "string" && data.intent.trim() ? data.intent : "unknown";
      const confidenceNumber = Number(data?.confidence);
      const confidenceText = Number.isFinite(confidenceNumber) ? confidenceNumber.toFixed(2) : "0.00";
      const botText = `${reply} (intent ${intent}, confidence ${confidenceText})`;
      setChat((prev) => [...prev, { sender: "bot", text: botText }]);

      saveQuery({
        id: `q-${Date.now()}`,
        userEmail: user.email,
        text: userText,
        intent,
        status: "active",
        createdAt: new Date().toISOString(),
      });
      notify("Query sent successfully.", "success");
    } catch (_) {
      setChat((prev) => [...prev, { sender: "bot", text: "Backend is unreachable. Start API server." }]);
      notify("Message failed.", "error");
    }
  }

  function submitFeedback(type, notes) {
    if (!user) return;
    const item = {
      id: `f-${Date.now()}`,
      userEmail: user.email,
      type,
      notes,
      createdAt: new Date().toISOString(),
    };
    const next = [item, ...feedback];
    setFeedback(next);
    writeJson(FEEDBACK_KEY, next);

    if (type === "helpful") {
      const nextQueries = queryLog.map((q) => {
        if (q.userEmail === user.email && q.status === "active") {
          return { ...q, status: "solved" };
        }
        return q;
      });
      setQueryLog(nextQueries);
      writeJson(QUERY_KEY, nextQueries);
    }

    notify("Feedback submitted. Thank you.", "success");
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">SupportPilot</div>
        <div className="actions">
          <button className="ghost" onClick={() => setView("landing")}>Home</button>
          {!user && <button className="primary" onClick={() => { setView("auth"); setAuthMode("login"); }}>Login</button>}
          {!user && <button onClick={() => { setView("auth"); setAuthMode("signup"); }}>Signup</button>}
          {user && <button onClick={logout}>Logout</button>}
        </div>
      </header>

      {view === "landing" && (
        <section className="hero">
          <div className="panel">
            <h1>Customer Support Chatbot Platform</h1>
            <p className="small">
              Fast AI responses, role-based access, feedback tracking, and actionable dashboards.
            </p>
            <div className="help-text">
              For users: sign up, ask support questions, and track your solved vs active queries.
              For admin: login using the only admin account, monitor solution quality, and review volume.
            </div>
          </div>
          <div className="panel">
            <h3>Admin Login (Hardcoded)</h3>
            <p className="small">Only one admin is allowed in the system.</p>
            <p><strong>ID:</strong> admin</p>
            <p><strong>Password:</strong> admin123</p>
            <p className="small">New registrations are always created as normal users.</p>
          </div>
        </section>
      )}

      {view === "auth" && (
        <AuthView
          authMode={authMode}
          setAuthMode={setAuthMode}
          onLogin={loginUser}
          onSignup={registerUser}
          onForgot={resetPassword}
        />
      )}

      {view === "chat" && user && user.role === "user" && (
        <UserView
          user={user}
          message={message}
          setMessage={setMessage}
          chat={chat}
          onSend={sendMessage}
          onFeedback={submitFeedback}
          solvedCount={solvedCount}
          activeCount={activeCount}
        />
      )}

      {view === "admin" && user && user.role === "admin" && (
        <AdminView
          analytics={analytics}
          localStats={adminQueryStats}
          onRefresh={() => fetchAnalytics()}
          feedback={feedback}
        />
      )}

      <div className="toast-wrap">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}

function AuthView({ authMode, setAuthMode, onLogin, onSignup, onForgot }) {
  const [role, setRole] = useState("user");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  return (
    <section className="panel auth-card">
      <h2>{authMode === "login" ? "Login" : authMode === "signup" ? "Signup" : "Forgot Password"}</h2>
      {authMode === "login" && (
        <div className="form">
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
          <input
            placeholder={role === "admin" ? "Admin username" : "Email"}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="primary" onClick={() => onLogin(email.trim(), password, role)}>Login</button>
        </div>
      )}

      {authMode === "signup" && (
        <div className="form">
          <input placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} />
          <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            className="primary"
            onClick={() => onSignup({ name: name.trim(), email: email.trim(), password })}
          >
            Create User Account
          </button>
          <p className="small">Role is fixed to user during registration.</p>
        </div>
      )}

      {authMode === "forgot" && (
        <div className="form">
          <input placeholder="Registered email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input
            placeholder="New password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <button className="primary" onClick={() => onForgot(email.trim(), newPassword)}>Reset Password</button>
        </div>
      )}

      <div className="row">
        <button onClick={() => setAuthMode("login")}>Login</button>
        <button onClick={() => setAuthMode("signup")}>Signup</button>
        <button onClick={() => setAuthMode("forgot")}>Forgot Password</button>
      </div>
    </section>
  );
}

function UserView({ user, message, setMessage, chat, onSend, onFeedback, solvedCount, activeCount }) {
  const [feedbackNote, setFeedbackNote] = useState("");

  return (
    <section className="chat-layout">
      <div className="panel">
        <h2>Chat Assistant</h2>
        <p className="small">Hi {user.name}, ask any support question and review bot confidence in replies.</p>
        <div className="messages">
          {chat.map((item, idx) => (
            <div key={idx} className={`msg ${item.sender}`}>
              <strong>{item.sender === "user" ? "You" : "Bot"}:</strong> {item.text}
            </div>
          ))}
        </div>
        <div className="row">
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask your support question..."
            onKeyDown={(e) => { if (e.key === "Enter") onSend(); }}
          />
          <button className="primary" onClick={onSend}>Send</button>
        </div>
      </div>

      <div className="panel">
        <h3>Your Dashboard</h3>
        <div className="cards">
          <div className="card">
            <div className="small">Solved Queries</div>
            <div className="value status-ok">{solvedCount}</div>
          </div>
          <div className="card">
            <div className="small">Active Queries</div>
            <div className="value status-warn">{activeCount}</div>
          </div>
          <div className="card">
            <div className="small">Total Queries</div>
            <div className="value">{solvedCount + activeCount}</div>
          </div>
        </div>

        <h3>Feedback</h3>
        <textarea
          rows="4"
          value={feedbackNote}
          onChange={(e) => setFeedbackNote(e.target.value)}
          placeholder="Tell us how we can improve your support experience..."
        />
        <div className="row">
          <button onClick={() => onFeedback("helpful", feedbackNote)}>Helpful</button>
          <button onClick={() => onFeedback("not_helpful", feedbackNote)}>Needs Improvement</button>
        </div>
      </div>
    </section>
  );
}

function AdminView({ analytics, localStats, onRefresh, feedback }) {
  return (
    <section className="panel">
      <h2>Admin Dashboard</h2>
      <p className="small">Monitors global activity and quality signals across all users.</p>
      <button className="primary" onClick={onRefresh}>Refresh Backend Analytics</button>

      <div className="cards" style={{ marginTop: "12px" }}>
        <div className="card">
          <div className="small">Solved Queries (Frontend)</div>
          <div className="value status-ok">{localStats.solved}</div>
        </div>
        <div className="card">
          <div className="small">Active Queries (Frontend)</div>
          <div className="value status-warn">{localStats.active}</div>
        </div>
        <div className="card">
          <div className="small">Total Queries (Frontend)</div>
          <div className="value">{localStats.total}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Backend Analytics</h3>
          <p className="small">Uses `/api/analytics/summary`.</p>
          <p>Total Queries: {analytics?.total_queries ?? "N/A"}</p>
          <p>Bot Messages: {analytics?.bot_messages ?? "N/A"}</p>
          <p>Handovers: {analytics?.handover_count ?? "N/A"}</p>
        </div>
        <div className="card">
          <h3>Recent Feedback</h3>
          {feedback.length === 0 && <p className="small">No feedback yet.</p>}
          {feedback.slice(0, 5).map((item) => (
            <p key={item.id} className="small">
              [{item.type}] {item.userEmail}: {item.notes || "No note"}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
