import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MESSAGES } from "@/i18n";

import { ScanForm } from "./ScanForm";

const t = MESSAGES.en;

function setup() {
  const onSubmit = vi.fn();
  render(<ScanForm onSubmit={onSubmit} />);
  return {
    onSubmit,
    user: userEvent.setup(),
    url: screen.getByLabelText(t.form.urlLabel),
    checkbox: screen.getByRole("checkbox", { name: t.form.authorize }),
    submit: screen.getByRole("button", { name: t.form.submit }),
  };
}

describe("ScanForm", () => {
  it("asks for an address and focuses the field", async () => {
    const { user, url, submit, onSubmit } = setup();
    await user.click(submit);
    expect(screen.getByText(t.validation.emptyUrl)).toBeInTheDocument();
    expect(url).toHaveAttribute("aria-invalid", "true");
    expect(url).toHaveFocus();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("refuses to scan without authorisation", async () => {
    const { user, url, checkbox, submit, onSubmit } = setup();
    await user.type(url, "shop.example");
    await user.click(submit);
    expect(screen.getByText(t.validation.notAuthorized)).toBeInTheDocument();
    expect(checkbox).toHaveFocus();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the trimmed address once authorised", async () => {
    const { user, url, checkbox, submit, onSubmit } = setup();
    await user.type(url, "  shop.example  ");
    await user.click(checkbox);
    await user.click(submit);
    expect(onSubmit).toHaveBeenCalledWith("shop.example");
  });
});
