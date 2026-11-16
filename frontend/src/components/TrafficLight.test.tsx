import { render, screen } from "@testing-library/react";
import { TrafficLight } from "./TrafficLight";

describe("TrafficLight", () => {
  it("lights only the predicted lamp", () => {
    render(<TrafficLight phase="GREEN" />);
    expect(screen.getByRole("img", { name: "Estimated phase: Green" })).toBeInTheDocument();
    expect(screen.getByTestId("lamp-GREEN")).toHaveAttribute("data-lit", "true");
    expect(screen.getByTestId("lamp-RED")).toHaveAttribute("data-lit", "false");
  });

  it("announces uncertain estimates", () => {
    render(<TrafficLight phase="RED" uncertain />);
    expect(screen.getByRole("img", { name: "Uncertain estimate: Red" })).toBeInTheDocument();
  });

  it("shows no lit lamp without a phase", () => {
    render(<TrafficLight phase={null} />);
    expect(screen.getByRole("img", { name: "No phase estimate" })).toBeInTheDocument();
    for (const lamp of ["RED", "YELLOW", "GREEN"]) {
      expect(screen.getByTestId(`lamp-${lamp}`)).toHaveAttribute("data-lit", "false");
    }
  });
});
