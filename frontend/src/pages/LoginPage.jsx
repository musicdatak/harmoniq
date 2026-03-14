import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-teal">HarmoniQ</h1>
          <p className="text-gray-400 mt-2">Harmonic Music Scheduler</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-dark-card rounded-xl p-8 shadow-lg border border-gray-800"
        >
          <h2 className="text-xl font-semibold mb-6">Sign in</h2>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 mb-4 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-dark-surface border border-gray-700 rounded-lg px-4 py-2.5 text-gray-100 focus:border-teal focus:ring-1 focus:ring-teal outline-none transition"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-dark-surface border border-gray-700 rounded-lg px-4 py-2.5 text-gray-100 focus:border-teal focus:ring-1 focus:ring-teal outline-none transition"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-6 bg-teal text-dark-bg font-semibold py-2.5 rounded-lg hover:bg-teal-400 transition disabled:opacity-50"
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>

          <p className="text-center text-sm text-gray-400 mt-4">
            No account?{" "}
            <Link to="/register" className="text-teal hover:underline">
              Register
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
