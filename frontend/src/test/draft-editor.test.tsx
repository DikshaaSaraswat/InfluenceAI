import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DraftEditor } from "@/components/app/DraftEditor";

function setup() {
  const handlers = {
    onSave: vi.fn(async () => ({})),
    onApprove: vi.fn(async () => ({})),
    onSend: vi.fn(async () => ({})),
  };
  render(<DraftEditor initial={{ subject: "Hello", body: "Campaign details" }} {...handlers} />);
  return handlers;
}

describe("DraftEditor email safety", () => {
  it("does not send while saving or approving a draft", async () => {
    const handlers = setup();

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));

    await waitFor(() => expect(handlers.onApprove).toHaveBeenCalledTimes(1));
    expect(handlers.onSave).toHaveBeenCalledWith({ subject: "Hello", body: "Campaign details" });
    expect(handlers.onSend).not.toHaveBeenCalled();
  });

  it("sends only after the user clicks Send and confirms", async () => {
    const handlers = setup();
    const confirmation = vi.spyOn(window, "confirm").mockReturnValue(true);

    expect(handlers.onSend).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(confirmation).toHaveBeenCalledWith("Send this email now?");
    await waitFor(() => expect(handlers.onSend).toHaveBeenCalledTimes(1));
    confirmation.mockRestore();
  });
});
