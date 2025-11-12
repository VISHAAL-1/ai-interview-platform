import React, { useState, useEffect } from "react";
import { register, login } from "../api";
import { saveToken } from "../auth";
import { jwtDecode } from 'jwt-decode'; // <-- IMPORT THE DECODER

// Added onSwitch prop to allow App.jsx to control the mode
export default function Login({ initialMode, onLogin, onSwitch }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    // Use the prop to set initial mode, but still manage the toggle internally for visual state
    const [isSigningUp, setIsSigningUp] = useState(initialMode === 'signup');

    useEffect(() => {
        // Update local state if initialMode prop changes
        setIsSigningUp(initialMode === 'signup');
    }, [initialMode]);

    async function doAuth(e) {
        e.preventDefault();

        if (isSigningUp) {
            // --- Registration Attempt ---
            try {
                await register({ email, password });
                alert("Registration successful! Please sign in.");
                setIsSigningUp(false); 
                onSwitch('login'); 
            } catch (err) {
                const errorMessage = err.response?.data?.detail || "Registration failed. Check logs for server error.";
                alert(errorMessage);
            }
        } else {
            // --- Login Attempt ---
            try {
                const res = await login(email, password);
                const token = res.data.access_token;
                saveToken(token);
                
                // --- FIX: Decode the token to get the real user ID ---
                const decodedToken = jwtDecode(token);
                // The 'sub' field holds the user ID string from FastAPI
                const userId = parseInt(decodedToken.sub, 10); 
                
                // This sends the actual user ID (e.g., 5) to App.jsx
                onLogin(userId); 
                
            } catch (err) {
                alert("Sign in failed. Check your email or password.");
            }
        }
    }

    return (
        <div className="card center">
            <div className="auth-tabs">
                <button 
                    className={`tab-btn ${!isSigningUp ? 'active' : ''}`}
                    onClick={() => { setIsSigningUp(false); onSwitch('login'); }}
                >
                    Sign In
                </button>
                <button 
                    className={`tab-btn ${isSigningUp ? 'active' : ''}`}
                    onClick={() => { setIsSigningUp(true); onSwitch('signup'); }}
                >
                    Sign Up
                </button>
            </div>
            
            <h2>{isSigningUp ? "Create Account" : "Sign In"}</h2>

            <form onSubmit={doAuth} className="form">
                <label>Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
                
                <label>Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
                
                <button className="btn">
                    {isSigningUp ? "Register Account" : "Sign In"}
                </button>
            </form>
        </div>
    );
}