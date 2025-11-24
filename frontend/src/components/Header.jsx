import React from "react";

export default function Header({ onNavigate }) {
  return (
    <header className="header-bar">
      <div className="brand">AI Interviewer</div>

      <nav className="nav-buttons">
        <button onClick={() => onNavigate("interview")} className="nav-btn">
          Interview
        </button>

        <button onClick={() => onNavigate("profile")} className="nav-btn">
          Profile
        </button>

        <button onClick={() => onNavigate("login")} className="logout-btn">
          Logout
        </button>
      </nav>
    </header>
  );
}
