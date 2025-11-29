import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge, StatusBadge, CategoryBadge } from "./Badge";

describe("Badge", () => {
  it("renders badge with text", () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText(/test badge/i)).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    const { rerender } = render(<Badge variant="primary">Primary</Badge>);
    expect(screen.getByText(/primary/i)).toHaveClass("bg-blue-100");

    rerender(<Badge variant="success">Success</Badge>);
    expect(screen.getByText(/success/i)).toHaveClass("bg-emerald-100");

    rerender(<Badge variant="danger">Danger</Badge>);
    expect(screen.getByText(/danger/i)).toHaveClass("bg-red-100");
  });

  it("applies custom className", () => {
    render(<Badge className="custom-class">Custom</Badge>);
    expect(screen.getByText(/custom/i)).toHaveClass("custom-class");
  });
});

describe("StatusBadge", () => {
  it("renders new status", () => {
    render(<StatusBadge status="new" />);
    expect(screen.getByText(/new/i)).toBeInTheDocument();
  });

  it("renders verified status", () => {
    render(<StatusBadge status="verified" />);
    expect(screen.getByText(/verified/i)).toBeInTheDocument();
  });

  it("renders resolved status", () => {
    render(<StatusBadge status="resolved" />);
    expect(screen.getByText(/resolved/i)).toBeInTheDocument();
  });

  it("renders rejected status", () => {
    render(<StatusBadge status="rejected" />);
    expect(screen.getByText(/rejected/i)).toBeInTheDocument();
  });

  it("renders in_progress status", () => {
    render(<StatusBadge status="in_progress" />);
    expect(screen.getByText(/in progress/i)).toBeInTheDocument();
  });

  it("applies correct color for each status", () => {
    const { rerender } = render(<StatusBadge status="new" />);
    expect(screen.getByText(/new/i)).toHaveClass("bg-red-100");

    rerender(<StatusBadge status="verified" />);
    expect(screen.getByText(/verified/i)).toHaveClass("bg-amber-100");

    rerender(<StatusBadge status="resolved" />);
    expect(screen.getByText(/resolved/i)).toHaveClass("bg-emerald-100");
  });
});

describe("CategoryBadge", () => {
  it("renders fire category", () => {
    render(<CategoryBadge category="fire" />);
    expect(screen.getByText(/🔥/)).toBeInTheDocument();
    expect(screen.getByText(/fire/i)).toBeInTheDocument();
  });

  it("renders accident category", () => {
    render(<CategoryBadge category="accident" />);
    expect(screen.getByText(/🚗/)).toBeInTheDocument();
    expect(screen.getByText(/accident/i)).toBeInTheDocument();
  });

  it("renders infrastructure category", () => {
    render(<CategoryBadge category="infrastructure" />);
    expect(screen.getByText(/🚧/)).toBeInTheDocument();
    expect(screen.getByText(/infrastructure/i)).toBeInTheDocument();
  });

  it("returns null for unknown category", () => {
    const { container } = render(<CategoryBadge category="unknown" />);
    expect(container.firstChild).toBeNull();
  });
});
