const STEPS = ["Import", "Enrich", "Customize", "Results"];

export default function Stepper({ currentStep, onStepClick }) {
  return (
    <div className="flex items-center gap-1 mb-8">
      {STEPS.map((label, i) => {
        const isActive = i === currentStep;
        const isCompleted = i < currentStep;
        return (
          <div key={label} className="flex items-center">
            {i > 0 && (
              <div
                className={`w-8 h-px mx-1 ${
                  isCompleted ? "bg-teal" : "bg-gray-700"
                }`}
              />
            )}
            <button
              onClick={() => onStepClick?.(i)}
              disabled={i > currentStep}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition ${
                isActive
                  ? "bg-teal/15 text-teal border border-teal/30"
                  : isCompleted
                    ? "text-teal"
                    : "text-gray-500"
              } ${i <= currentStep ? "cursor-pointer hover:bg-teal/10" : "cursor-not-allowed"}`}
            >
              <span
                className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-mono ${
                  isActive
                    ? "bg-teal text-dark-bg"
                    : isCompleted
                      ? "bg-teal/20 text-teal"
                      : "bg-gray-800 text-gray-500"
                }`}
              >
                {isCompleted ? "\u2713" : i + 1}
              </span>
              <span className="hidden sm:inline">{label}</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}
