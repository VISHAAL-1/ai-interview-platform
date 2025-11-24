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
    const [followupQuestion, setFollowupQuestion] = useState(null);
    const [evaluationReceived, setEvaluationReceived] = useState(false);

    const localVideoRef = useRef(null);
    const localStreamRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const [isRecording, setIsRecording] = useState(false);
    const roomId = `interview-${userId}`;

    const appendLog = (msg) => {
        const line = `[${new Date().toISOString()}] ${msg}`;
        console.log(line);
        setLogs((prev) => [...prev, line]);
    };

    // ---------------- WEBSOCKET SETUP ----------------
    useEffect(() => {
        const token = getToken();
        const w = new WebSocket(`ws://localhost:8000/ws/${roomId}?token=${token}`);

        w.onopen = () => appendLog("WebSocket connected.");
        w.onclose = () => appendLog("WebSocket disconnected.");
        w.onerror = () => appendLog("WebSocket error.");

        w.onmessage = (ev) => {
            const data = JSON.parse(ev.data);
            appendLog(`WS Message: ${JSON.stringify(data)}`);

            if (data.type === "transcript_result") {
                appendLog(`Transcript: ${data.text}`);
            } else if (data.type === "evaluation") {
                setEvaluationReceived(true);
                setFollowupQuestion(null);
                appendLog("Evaluation received.");
            } else if (data.type === "followup") {
                setFollowupQuestion(data.question);
                appendLog("Follow-up question received.");
            }
        };

        setWs(w);
        return () => w.close();
    }, [userId]);


    // ---------------- MEDIA ----------------
    const startLocalMedia = async () => {
        if (isRecording) return;
        appendLog("Requesting media devices...");

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: { width: 400, height: 300 },
            });

            localStreamRef.current = stream;
            if (localVideoRef.current) localVideoRef.current.srcObject = stream;

            const audioStream = new MediaStream(stream.getAudioTracks());
            let mime = "audio/webm; codecs=opus";
            if (!MediaRecorder.isTypeSupported(mime)) mime = "audio/webm";

            const recorder = new MediaRecorder(audioStream, { mimeType: mime });

            audioChunksRef.current = [];
            recorder.ondataavailable = (e) => e.data.size > 0 && audioChunksRef.current.push(e.data);
            recorder.onstop = () => appendLog("Recording stopped.");

            recorder.start();
            mediaRecorderRef.current = recorder;
            setIsRecording(true);
            appendLog("Recording started.");
        } catch (err) {
            appendLog("Media access error: " + err.message);
        }
    };

    const stopLocalMediaAndSend = () => {
        if (!mediaRecorderRef.current) return;

        const mr = mediaRecorderRef.current;
        mr.onstop = () => {
            const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
            appendLog(`Final blob size: ${blob.size} bytes`);

            const reader = new FileReader();
            reader.onloadend = () => {
                const base64 = reader.result.split(",")[1];

                ws.send(
                    JSON.stringify({
                        type: "audio_data",
                        question: currentQuestion.text,
                        interview_id: interviewId,
                        data: base64,
                        format: mr.mimeType,
                    })
                );

                appendLog("Audio sent to server.");
            };
            reader.readAsDataURL(blob);

            setIsRecording(false);
        };

        mr.stop();
        if (localStreamRef.current)
            localStreamRef.current.getTracks().forEach((t) => t.stop());
    };


    // ---------------- INTERVIEW FLOW ----------------
    const startInterview = async () => {
        const token = getToken();

        const startRes = await axios.post(
            `${API_BASE}/start_interview`,
            { user_id: userId },
            { headers: { Authorization: `Bearer ${token}` } }
        );

        setInterviewId(startRes.data.id);

        const qRes = await axios.get(`${API_BASE}/questions?level=1&limit=5`, {
            headers: { Authorization: `Bearer ${token}` },
        });

        setQuestions(qRes.data);
        setCurrentQuestion(qRes.data[0]);
        setQuestionIndex(0);

        appendLog("Interview started.");
        startLocalMedia();
    };

    const nextQuestion = () => {
        setEvaluationReceived(false);
        setFollowupQuestion(null);

        if (questionIndex < questions.length - 1) {
            const next = questionIndex + 1;
            setQuestionIndex(next);
            setCurrentQuestion(questions[next]);
            appendLog("Next question loaded.");
            startLocalMedia();
        } else {
            appendLog("Interview finished.");
            setCurrentQuestion({ text: "Interview finished!" });
        }
    };


    // ---------------- RENDER ----------------
    return (
        <div className="interview-card">

            <h2 className="room-title">AI Interview Room</h2>

            <video ref={localVideoRef} autoPlay muted className="interview-video" />

            {!currentQuestion && (
                <button className="primary-btn" onClick={startInterview}>
                    Start Interview
                </button>
            )}

            {currentQuestion && (
                <div className="question-box">
                    <div className="question-label">
                        Question {questionIndex + 1}
                    </div>

                    <div className="question-text-display">
                        {currentQuestion.text}
                    </div>

                    {!evaluationReceived ? (
                        <button
                            className="primary-btn"
                            onClick={stopLocalMediaAndSend}
                            disabled={!isRecording}
                        >
                            Stop & Submit
                        </button>
                    ) : (
                        <div className="next-box">
                            {followupQuestion && (
                                <div className="followup">
                                    <b>Follow-up:</b> {followupQuestion}
                                </div>
                            )}

                            <button className="secondary-btn" onClick={nextQuestion}>
                                Next Question
                            </button>
                        </div>
                    )}
                </div>
            )}

            <div className="log-box">
                {logs.map((l, i) => (
                    <div key={i} className="log-line">
                        {l}
                    </div>
                ))}
            </div>
        </div>
    );
}
