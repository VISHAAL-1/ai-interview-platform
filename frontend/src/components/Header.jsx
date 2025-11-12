import React from "react";

export default function Header({ onNavigate }) {
  return (
    <header className="header">
      <div className="brand">AI Interviewer</div>
      <nav className="nav">
        <button onClick={() => onNavigate("interview")} className="btn-link">
          Interview
        </button>
        <button onClick={() => onNavigate("profile")} className="btn-link">
          Profile
        </button>
        <button onClick={() => onNavigate("login")} className="btn-ghost">
          Logout
        </button>
      </nav>
    </header>
  );
}
