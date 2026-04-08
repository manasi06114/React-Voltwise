import axios from "axios";

const BASE = "/api";

export const resetEnv = (task = "medium") =>
  axios.post(`${BASE}/env/reset`, { task }).then((r) => r.data);

export const stepEnv = (task, action) =>
  axios.post(`${BASE}/env/step`, { task, action }).then((r) => r.data);

export const geminiStep = (task) =>
  axios.post(`${BASE}/env/gemini-step`, { task }).then((r) => r.data);

export const getState = (task) =>
  axios.get(`${BASE}/env/state/${task}`).then((r) => r.data);

export const getTasks = () =>
  axios.get(`${BASE}/env/tasks`).then((r) => r.data);

export const getHealth = () => axios.get(`${BASE}/health`).then((r) => r.data);

export const getApiKeyStatus = () =>
  axios.get(`${BASE}/api-keys/status`).then((r) => r.data);

// --- New endpoints ---

export const getForecast = (task) =>
  axios.get(`${BASE}/forecast/${task}`).then((r) => r.data);

export const getBlackoutRisk = (task) =>
  axios.get(`${BASE}/blackout-risk/${task}`).then((r) => r.data);

export const getStability = (task) =>
  axios.get(`${BASE}/stability/${task}`).then((r) => r.data);

export const getGridTopology = (task) =>
  axios.get(`${BASE}/grid-topology/${task}`).then((r) => r.data);

export const injectScenario = (task, scenario, intensity = 1.0) =>
  axios.post(`${BASE}/scenario/inject`, { task, scenario, intensity }).then((r) => r.data);

export const clearScenario = (task) =>
  axios.post(`${BASE}/scenario/clear`, { task }).then((r) => r.data);

export const getRecoveryStatus = (task) =>
  axios.get(`${BASE}/recovery-status/${task}`).then((r) => r.data);
