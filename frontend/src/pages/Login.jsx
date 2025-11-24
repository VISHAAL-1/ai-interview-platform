import React, { useState, useEffect } from "react";
import { register, login } from "../api";
import { saveToken } from "../auth";
import { jwtDecode } from 'jwt-decode';

export default function Login({ initialMode, onLogin, onSwitch }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isSigningUp, setIsSigningUp] = useState(initialMode === "signup");

    useEffect(() => {
        setIsSigningUp(initialMode === "signup");
    }, [initialMode]);

    async function doAuth(e) {
        e.preventDefault();

        if (isSigningUp) {
            try {
                await register({ email, password });
                alert("Registration successful! Please sign in.");
                setIsSigningUp(false);
                onSwitch("login");
            } catch (err) {
                const errorMessage =
                    err.response?.data?.detail ||
                    "Registration failed. Check logs for details.";
                alert(errorMessage);
            }
        } else {
            try {
                const res = await login(email, password);
                const token = res.data.access_token;

                saveToken(token);

                const decoded = jwtDecode(token);
                const userId = parseInt(decoded.sub);

                onLogin(userId);
            } catch (err) {
                alert("Incorrect email or password.");
            }
        }
    }

    return (
        <div className="auth-card">
            <div className="auth-tabs">
                <button
                    className={`tab-btn ${!isSigningUp ? "active" : ""}`}
                    onClick={() => {
                        setIsSigningUp(false);
                        onSwitch("login");
                    }}
                >
                    Sign In
                </button>

                <button
                    className={`tab-btn ${isSigningUp ? "active" : ""}`}
                    onClick={() => {
                        setIsSigningUp(true);
                        onSwitch("signup");
                    }}
                >
                    Sign Up
                </button>
            </div>

            <h2 className="auth-title">
                {isSigningUp ? "Create Account" : "Welcome Back"}
            </h2>
            <p className="auth-subtitle">
                {isSigningUp
                    ? "Sign up to begin your AI interview journey"
                    : "Sign in to continue your interview"}
            </p>

            <form onSubmit={doAuth} className="auth-form">
                <label className="input-label">Email</label>
                <input
                    type="email"
                    className="input-box"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />

                <label className="input-label">Password</label>
                <input
                    type="password"
                    className="input-box"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />

                <button className="auth-btn">
                    {isSigningUp ? "Create Account" : "Sign In"}
                </button>
            </form>
        </div>
    );
}
