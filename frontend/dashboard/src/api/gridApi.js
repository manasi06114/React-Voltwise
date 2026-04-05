import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Session management
export const createSession = async () => {
  try {
    const response = await api.post("/env/create-session");
    return response.data;
  } catch (error) {
    console.error("Error creating session:", error);
    throw error;
  }
};

export const resetEnv = async (sessionId) => {
  try {
    const response = await api.post(`/env/${sessionId}/reset`);
    return response.data;
  } catch (error) {
    console.error("Error resetting environment:", error);
    throw error;
  }
};

// Environment state
export const getState = async (sessionId) => {
  try {
    const response = await api.get(`/env/${sessionId}/state`);
    return response.data;
  } catch (error) {
    console.error("Error fetching state:", error);
    throw error;
  }
};

// Actions
export const step = async (sessionId, action) => {
  try {
    const response = await api.post(`/env/${sessionId}/step`, { action });
    return response.data;
  } catch (error) {
    console.error("Error stepping environment:", error);
    throw error;
  }
};

// Gemini AI step
export const geminiStep = async (sessionId) => {
  try {
    const response = await api.post(`/env/${sessionId}/gemini-step`);
    return response.data;
  } catch (error) {
    console.error("Error calling Gemini step:", error);
    throw error;
  }
};

// Scenario simulation
export const simulateScenario = async (sessionId, scenarioName) => {
  try {
    const response = await api.post(`/env/${sessionId}/simulate-scenario`, {
      scenario: scenarioName,
    });
    return response.data;
  } catch (error) {
    console.error("Error simulating scenario:", error);
    throw error;
  }
};

export default api;
