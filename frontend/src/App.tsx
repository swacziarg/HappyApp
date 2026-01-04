import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import Home from "./pages/Home";
import About from "./pages/About";
import Today from "./pages/Today";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />

      <div className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/mood" element={<Today />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </div>
    </div>
  );
}
