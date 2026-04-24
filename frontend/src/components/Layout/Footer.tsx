type FooterProps = {
  collapsed: boolean;
};

export function Footer({ collapsed }: FooterProps) {
  return (
    <footer
      className={`fixed bottom-0 right-0 z-20 h-10 border-t border-line bg-void/95 px-6 py-3 text-xs text-zinc-500 transition-all duration-200 ${
        collapsed ? "left-20" : "left-64"
      }`}
    >
      ezProxy is local-first and unauthenticated. Privacy means you own the
      machine.
    </footer>
  );
}
