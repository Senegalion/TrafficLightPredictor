import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { intersections } from "../test/fixtures";
import { IntersectionList } from "./IntersectionList";

describe("IntersectionList", () => {
  it("calls onSelect with the clicked intersection", async () => {
    const onSelect = vi.fn();
    render(<IntersectionList intersections={intersections} selectedId={1} onSelect={onSelect} />);

    await userEvent.click(screen.getByRole("button", { name: /Sienkiewicza/ }));

    expect(onSelect).toHaveBeenCalledWith(2);
    expect(screen.getByRole("button", { name: /Kościuszki/ })).toHaveAttribute("aria-pressed", "true");
  });
});
