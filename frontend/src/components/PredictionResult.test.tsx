import { render, screen } from "@testing-library/react";
import { prediction } from "../test/fixtures";
import { PredictionResult } from "./PredictionResult";

describe("PredictionResult", () => {
  it("shows the estimate, interval and confidence for a displayable prediction", () => {
    render(<PredictionResult prediction={prediction()} />);
    expect(screen.getByText("Estimate available")).toBeInTheDocument();
    expect(screen.getByText("~12 s")).toBeInTheDocument();
    expect(screen.getByText(/Likely range: 8 s – 16 s/)).toBeInTheDocument();
    expect(screen.getAllByText("91%").length).toBeGreaterThan(0);
  });

  it("labels simulated input and synthetic training data", () => {
    render(<PredictionResult prediction={prediction()} />);
    expect(screen.getByText("Simulated data")).toBeInTheDocument();
    expect(screen.getByText("Model trained on synthetic data")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("not a guarantee");
  });

  it("does not present a low-confidence prediction as an estimate", () => {
    render(
      <PredictionResult
        prediction={prediction({
          status: "LOW_CONFIDENCE",
          displayable: false,
          confidence: 0.52,
          message: "Calibrated confidence 0.52 is below the display threshold 0.80.",
        })}
      />,
    );
    expect(screen.getByText("No reliable estimate")).toBeInTheDocument();
    expect(screen.getByText(/below the display threshold/)).toBeInTheDocument();
    expect(screen.queryByText("~12 s")).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Uncertain estimate: Green" })).toBeInTheDocument();
  });

  it("explains insufficient data", () => {
    render(
      <PredictionResult
        prediction={prediction({
          status: "INSUFFICIENT_DATA",
          displayable: false,
          predictedPhase: null,
          confidence: null,
          phaseProbabilities: null,
          remainingSeconds: null,
          dataOrigin: "NONE",
          anchorObservation: null,
          message: "No observation of this signal exists at or before the target time.",
        })}
      />,
    );
    expect(screen.getByText("Insufficient data")).toBeInTheDocument();
    expect(screen.getByText("No observation")).toBeInTheDocument();
    expect(screen.queryByText("Model output")).not.toBeInTheDocument();
  });

  it("marks real observations as real", () => {
    render(<PredictionResult prediction={prediction({ dataOrigin: "REAL", trainingDataOrigin: "REAL" })} />);
    expect(screen.getByText("Real observation")).toBeInTheDocument();
    expect(screen.queryByText(/Model trained on/)).not.toBeInTheDocument();
  });
});
