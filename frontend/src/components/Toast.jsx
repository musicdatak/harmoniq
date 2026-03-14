import { createContext, useContext, useState, useCallback } from "react";

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = "success") => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const toast = useCallback({
    success: (msg) => addToast(msg, "success"),
    error: (msg) => addToast(msg, "error"),
  }, [addToast]);

  // Make toast callable as function too
  const toastFn = useCallback(
    (msg, type) => addToast(msg, type),
    [addToast]
  );
  toastFn.success = (msg) => addToast(msg, "success");
  toastFn.error = (msg) => addToast(msg, "error");

  return (
    <ToastContext.Provider value={toastFn}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto px-5 py-3 rounded-xl font-semibold shadow-lg text-sm animate-toast-in ${
              t.type === "error"
                ? "bg-red-500 text-white shadow-red-500/20"
                : "bg-teal text-dark-bg shadow-teal/20"
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
