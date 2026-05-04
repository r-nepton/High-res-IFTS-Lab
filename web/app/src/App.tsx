import { useState } from "react";
import { TopNav, type Page } from "./components/TopNav";
import { Credits } from "./pages/Credits";
import { ETC } from "./pages/ETC";
import { Explore } from "./pages/Explore";
import { Home } from "./pages/Home";
import "./styles.css";

export default function App() {
  const [page, setPage] = useState<Page>("about");

  return (
    <div className="app-shell">
      <TopNav page={page} onPageChange={setPage} />
      {page === "about" ? <Home /> : null}
      {page === "etc" ? <ETC /> : null}
      {page === "how" ? <Explore /> : null}
      {page === "credits" ? <Credits /> : null}
      <footer>
        <span>MKID-IFTS Web ETC v1.0</span>
        <span>Planning/demo tool based on current model assumptions.</span>
      </footer>
    </div>
  );
}
