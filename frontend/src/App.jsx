import Login from "./pages/Login.jsx";
import React, { useState } from "react";

import Header from "./components/Header.jsx";
import InterviewRoom from "./pages/InterviewRoom.jsx";
import Profile from "./pages/Profile.jsx";

// New Component to offer the initial choice
function AuthChooser({ onSelect }) {
    return (
        <div className="card center" style={{ textAlign: 'center', maxWidth: '400px', marginTop: '100px' }}>
            <h2>Welcome to AI Interviewer</h2>
            <p>Please select an option to continue.</p>
            <div className="controls" style={{ justifyContent: 'center', marginTop: '20px' }}>
                <button 
                    className="btn" 
                    onClick={() => onSelect("login")} 
                    style={{ background: 'var(--accent)' }}
                >
                    Sign In
                </button>
                <button 
                    className="btn" 
                    onClick={() => onSelect("signup")}
                    style={{ background: '#5b9bff' }}
                >
                    Sign Up
                </button>
            </div>
        </div>
    );
}

export default function App() {
    // 💡 CHANGE: Start at "auth" to present the choice
    const [page, setPage] = useState("auth"); 
    const [userId, setUserId] = useState(null);

    const to = (p) => setPage(p);

    // Function that runs upon successful login/registration
    const handleAuthSuccess = (id) => {
        setUserId(id);
        to("interview"); // Navigate directly to interview room
    };

    return (
        <div className="app">
            {/* Show Header only if not on the Auth Choice screen */}
            {page !== "auth" && page !== "login" && page !== "signup" && <Header onNavigate={to} />}
            
            <main className="container">
                {/* 1. INITIAL CHOICE SCREEN */}
                {page === "auth" && <AuthChooser onSelect={to} />}

                {/* 2. SIGN IN / SIGN UP FORM */}
                {(page === "login" || page === "signup") && (
                    <Login
                        initialMode={page} // Pass initial mode based on choice
                        onLogin={handleAuthSuccess}
                        onSwitch={(mode) => to(mode)} // Allows toggling between signin/signup
                    />
                )}

                {/* 3. APP SCREENS (Interview is available immediately after successful auth) */}
                {page === "interview" && <InterviewRoom userId={userId} />}
                {page === "profile" && <Profile userId={userId} />}
            </main>
        </div>
    );
}