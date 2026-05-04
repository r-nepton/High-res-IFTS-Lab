export type Page = "about" | "etc" | "how" | "credits";

interface TopNavProps {
  page: Page;
  onPageChange: (page: Page) => void;
}

const items: Array<{ id: Page; label: string }> = [
  { id: "about", label: "About MKID-IFTS" },
  { id: "etc", label: "ETC" },
  { id: "how", label: "How It Works" },
  { id: "credits", label: "Credits" }
];

export function TopNav({ page, onPageChange }: TopNavProps) {
  return (
    <header className="top-nav">
      <div>
        <p className="eyebrow">High-Resolution IFTS Lab · MKID-IFTS Web ETC v1.0</p>
        <h1>MKID-IFTS Web ETC</h1>
      </div>
      <nav>
        {items.map((item) => (
          <button
            key={item.id}
            className={page === item.id ? "active" : ""}
            onClick={() => onPageChange(item.id)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
