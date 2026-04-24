import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement>
> & {
  variant?: "primary" | "secondary" | "ghost";
};

export function Button({
  children,
  className = "",
  variant = "primary",
  ...props
}: ButtonProps) {
  const variants = {
    primary: "bg-neon text-void hover:bg-magenta hover:text-white shadow-glow",
    secondary:
      "border border-neon bg-transparent text-neon hover:bg-neon hover:text-void",
    ghost:
      "border border-line bg-panel/70 text-ink hover:border-magenta hover:text-magenta",
  };

  return (
    <button
      className={`rounded-md px-4 py-2 text-sm font-semibold transition duration-200 disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
