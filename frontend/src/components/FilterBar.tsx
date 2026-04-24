import { Button } from "./Button";

type FilterBarProps = {
  values: {
    search: string;
    type: string;
    country: string;
    anonymity: string;
  };
  onChange: (values: FilterBarProps["values"]) => void;
  onScrape: () => void;
  onExport: (format: "txt" | "csv") => void;
};

export function FilterBar({
  values,
  onChange,
  onScrape,
  onExport,
}: FilterBarProps) {
  const field =
    "rounded-md border border-line bg-panel px-3 py-2 text-sm text-ink transition focus:border-neon";

  return (
    <div className="rounded-md border border-line bg-panel p-3">
      <div className="grid gap-3 md:grid-cols-5">
        <input
          aria-label="Search proxy"
          className={field}
          placeholder="Search IP"
          value={values.search}
          onChange={(event) =>
            onChange({ ...values, search: event.target.value })
          }
        />
        <select
          aria-label="Filter type"
          className={field}
          value={values.type}
          onChange={(event) =>
            onChange({ ...values, type: event.target.value })
          }
        >
          <option value="">All types</option>
          <option value="http">HTTP</option>
          <option value="https">HTTPS</option>
          <option value="socks4">SOCKS4</option>
          <option value="socks5">SOCKS5</option>
        </select>
        <input
          aria-label="Filter country"
          className={field}
          placeholder="Country code"
          value={values.country}
          onChange={(event) =>
            onChange({ ...values, country: event.target.value.toUpperCase() })
          }
        />
        <input
          aria-label="Filter anonymity"
          className={field}
          placeholder="Anonymity"
          value={values.anonymity}
          onChange={(event) =>
            onChange({ ...values, anonymity: event.target.value })
          }
        />
        <div className="flex gap-2">
          <Button className="flex-1" onClick={onScrape}>
            Scrape
          </Button>
          <Button variant="secondary" onClick={() => onExport("txt")}>
            TXT
          </Button>
          <Button variant="ghost" onClick={() => onExport("csv")}>
            CSV
          </Button>
        </div>
      </div>
    </div>
  );
}
