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
