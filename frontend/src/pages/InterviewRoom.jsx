import React, { useEffect, useState, useRef } from "react";
import { getToken } from "../auth";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function InterviewRoom({ userId }) {
    const [ws, setWs] = useState(null);
    const [logs, setLogs] = useState([]);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [questionIndex, setQuestionIndex] = useState(0);
    const [interviewId, setInterviewId] = useState(null);
    
    // Media Access State & Refs
    const localVideoRef = useRef(null);
    const localStreamRef = useRef(null);
    const [isMediaActive, setIsMediaActive] = useState(false);
    
    const roomId = `interview-${userId}`;

    // --- EFFECT: WEBSOCKET CONNECTION ---
    useEffect(() => {
        if (!userId) {
            setLogs(l => [...l, "Error: User ID is missing, cannot connect WS."]);
            return;
        }
        
        const token = getToken();
        const w = new WebSocket(`ws://localhost:8000/ws/${roomId}?token=${token}`);
        
        w.onopen = () => setLogs(l => [...l, "WebSocket connected"]);
        w.onmessage = (ev) => {
            const data = JSON.parse(ev.data);
            setLogs(l => [...l, JSON.stringify(data)]);
            
            if (data.type === 'evaluation') {
                alert(`Feedback received! Score: ${data.evaluation.combined_score}`);
                setTimeout(nextQuestion, 1500);
            }
        };
        w.onclose = () => setLogs(l => [...l, "WebSocket closed"]);

        setWs(w);
        return () => w.close();
    }, [roomId, userId]);
    
    // --- FUNCTION: Start Camera and Microphone ---
    const startLocalMedia = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: { width: 400, height: 300 } 
            });
            
            localStreamRef.current = stream;
            
            if (localVideoRef.current) {
                localVideoRef.current.srcObject = stream;
            }
            
            setIsMediaActive(true);
            setLogs(l => [...l, "Microphone and Camera started."]);
        } catch (err) {
            setLogs(l => [...l, `Error accessing media: ${err.name} - Permission denied or device in use.`]);
            console.error("Media access error:", err);
            setIsMediaActive(false);
        }
    };
    
    // --- FUNCTION: Stop Media ---
    const stopLocalMedia = () => {
        if (localStreamRef.current) {
            localStreamRef.current.getTracks().forEach(track => track.stop());
            localStreamRef.current = null;
        }
        setIsMediaActive(false);
        setLogs(l => [...l, "Microphone and Camera stopped."]);
    };

    // --- Clean-up media on component unmount ---
    useEffect(() => {
        return () => {
            stopLocalMedia();
        };
    }, []);

    // --- FUNCTION: START INTERVIEW & FETCH QUESTIONS ---
    const startInterview = async () => {
        if (!userId) {
             setLogs(l => [...l, "Error: Cannot start interview. User ID is missing."]);
             return;
        }
        try {
            const token = getToken();
            
            const startRes = await axios.post(`${API_BASE}/start_interview`, { user_id: userId }, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setInterviewId(startRes.data.id);
            setLogs(l => [...l, `New Interview started with ID: ${startRes.data.id}`]);

            const questionsRes = await axios.get(`${API_BASE}/questions?level=1&limit=5`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            const fetchedQuestions = questionsRes.data;
            if (fetchedQuestions.length > 0) {
                setQuestions(fetchedQuestions);
                setQuestionIndex(0);
                setCurrentQuestion(fetchedQuestions[0]);
                setLogs(l => [...l, `Interview Started: ${fetchedQuestions.length} Questions Loaded`]);
                
                // Automatically start media upon loading the first question
                startLocalMedia(); 
            } else {
                setLogs(l => [...l, "Error: No questions found in the database."]);
            }
        } catch (error) {
            setLogs(l => [...l, "Error starting interview/fetching questions: " + (error.response?.statusText || error.message)]);
        }
    };

    // --- FUNCTION: NEXT QUESTION ---
    const nextQuestion = () => {
        if (questionIndex < questions.length - 1) {
            const nextIndex = questionIndex + 1;
            setQuestionIndex(nextIndex);
            setCurrentQuestion(questions[nextIndex]);
            setLogs(l => [...l, `Moving to next question: ${questions[nextIndex].text.substring(0, 30)}...`]);
            startLocalMedia(); // Restart media for the next answer
        } else {
            setCurrentQuestion({ text: "Interview Finished! Results sent for final review." });
            setLogs(l => [...l, "Interview Finished! Check Profile for results."]);
            setQuestions([]); 
            stopLocalMedia(); // Stop media when interview ends
        }
    };
    
    // --- FUNCTION: SEND DUMMY ANSWER (Audio Simulation) ---
    async function sendTranscript() {
        if (!ws || !currentQuestion || questionIndex >= questions.length || !isMediaActive) return;
        
        // 1. STOP MEDIA to simulate end of recording
        stopLocalMedia(); 
        setLogs(l => [...l, "Simulated recording complete. Sending transcript..."]);

        // 2. Send simulated transcript
        const answerText = `This is my simulated answer for the question: ${currentQuestion.text}`;

        ws.send(JSON.stringify({
            type: "transcript", 
            question: currentQuestion.text, 
            text: answerText
        }));
        setLogs(l => [...l, `Sent dummy answer to server for evaluation.`]);
    }

    // --- RENDER ---
    return (
        <div className="card">
            <h3>AI Interview Room</h3>

            {/* VIDEO STREAM CONTAINER */}
            <div className="video-container" style={{ textAlign: 'center', marginBottom: '15px' }}>
                <video 
                    ref={localVideoRef} 
                    autoPlay 
                    muted 
                    style={{ 
                        width: '100%', 
                        maxWidth: '400px', 
                        height: 'auto', 
                        aspectRatio: '4/3',
                        background: '#000', 
                        border: isMediaActive ? '2px solid #635bff' : '1px solid #333'
                    }}
                >
                </video>
            </div>
            
            {!currentQuestion && questions.length === 0 && (
                <div style={{ textAlign: 'center' }}>
                    <p>Ready to start your practice interview?</p>
                    <button className="btn" onClick={startInterview}>
                        Take Interview
                    </button>
                </div>
            )}

            {currentQuestion && questions.length > 0 && (
                <>
                    {/* --- FIX: Display Question Text with direct styling to ensure visibility --- */}
                    <h4 style={{ color: 'white', marginTop: '20px', marginBottom: '20px' }}>
                        Question {questionIndex + 1} of {questions.length}: {currentQuestion.text}
                    </h4>
                    
                    <div className="controls">
                        <button 
                            className="btn" 
                            onClick={sendTranscript} 
                            disabled={!ws || questionIndex >= questions.length || !isMediaActive}
                        >
                            Submit Answer (Simulated)
                        </button>
                        
                        {/* The Stop Media button is kept separate just for manual debug */}
                        <button 
                            className="btn" 
                            onClick={stopLocalMedia} 
                            disabled={!isMediaActive}
                            style={{ background: '#ff5555' }}
                        >
                            Stop Media
                        </button>
                    </div>
                </>
            )}

            <div className="logs">
                {logs.map((l, i) => <div key={i} className="log-line">{l}</div>)}
            </div>
        </div>
    );
}