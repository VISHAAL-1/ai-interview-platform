import React, { useEffect, useState } from "react";
import AnalyticsCard from "../components/AnalyticsCard";
import axios from "axios";
import { getToken } from "../auth";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function Profile() {
    const [stats, setStats] = useState({
        total_interviews: 0,
        avg_score: 0.0,
        last_feedback: "No interviews completed yet."
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            const token = getToken();
            if (!token) {
                setLoading(false);
                return;
            }
            try {
                // Fetch stats from the backend endpoint
                const response = await axios.get(`${API_BASE}/profile/stats`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                setStats(response.data);
            } catch (error) {
                console.error("Error fetching profile stats:", error);
                setStats(s => ({ ...s, last_feedback: "Error loading statistics." }));
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) {
        return <div className="card center">Loading Profile...</div>;
    }

    return (
        <div className="card">
            <h3>Your Profile Dashboard</h3>
            <AnalyticsCard title="Total Interviews" value={stats.total_interviews} />
            <AnalyticsCard title="Avg Combined Score" value={stats.avg_score.toFixed(1)} />
            
            <div className="feedback">
                <h4>Last Interview Feedback</h4>
                <p>{stats.last_feedback}</p>
            </div>
        </div>
    );
}