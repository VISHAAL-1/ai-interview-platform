import React, { useEffect, useState } from "react";
import axios from "axios";
import { getToken } from "../auth";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function Profile() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            const token = getToken();
            if (!token) return;

            try {
                const res = await axios.get(`${API_BASE}/profile/stats`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                setStats(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading || !stats) {
        return <div className="profile-loading">Loading your profile...</div>;
    }

    return (
        <div className="profile-container">
            <h2 className="profile-title">Your Interview Insights</h2>

            {/* ---- SUMMARY CARDS ---- */}
            <div className="stats-section">
                <div className="stat-glass">
                    <h4>Total Interviews</h4>
                    <p>{stats.total_interviews}</p>
                </div>
                <div className="stat-glass">
                    <h4>Avg Correctness</h4>
                    <p>{stats.avg_correctness.toFixed(2)}</p>
                </div>
                <div className="stat-glass">
                    <h4>Avg Fluency</h4>
                    <p>{stats.avg_fluency.toFixed(2)}</p>
                </div>
                <div className="stat-glass">
                    <h4>Avg Combined</h4>
                    <p>{stats.avg_combined.toFixed(2)}</p>
                </div>
            </div>

            {/* ---- LAST FEEDBACK ---- */}
            <div className="glass-panel">
                <h3>Latest Feedback</h3>
                <p className="feedback-text">{stats.last_feedback}</p>
            </div>

            {/* ---- FULL HISTORY ---- */}
            <h3 className="history-title">Interview History</h3>

            {stats.history.length === 0 && (
                <p className="no-history">No interviews recorded yet.</p>
            )}

            <div className="history-list">
                {stats.history.map((ev) => (
                    <div key={ev.id} className="history-item">
                        <h4>{ev.question_text}</h4>

                        <div className="history-metrics">
                            <span><b>Correctness:</b> {ev.correctness_score}</span>
                            <span><b>Fluency:</b> {ev.fluency_score}</span>
                            <span><b>Combined:</b> {ev.combined_score}</span>
                        </div>

                        <p className="history-feedback">{ev.feedback}</p>

                        <small className="timestamp">
                            {new Date(ev.created_at).toLocaleString()}
                        </small>
                    </div>
                ))}
            </div>
        </div>
    );
}
