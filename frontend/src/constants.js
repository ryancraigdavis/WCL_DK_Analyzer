export const ANALYSIS_URL = {
  development: "http://localhost:8000/analyze_fight",
  production:
    "https://m82aq13rrc.execute-api.us-west-1.amazonaws.com/analyze_fight",
}[import.meta.env.MODE];
