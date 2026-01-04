import { NavLink } from "react-router-dom";

const linkClass =
  "px-3 py-2 rounded-md text-sm font-medium";

export default function NavBar() {
  return (
    <nav className="w-full bg-white shadow-sm">
      <div className="max-w-5xl mx-auto px-4 h-12 flex items-center space-x-4">
        <NavLink
          to="/"
          className={({ isActive }) =>
            `${linkClass} ${
              isActive ? "bg-gray-200" : "text-gray-600"
            }`
          }
        >
          Home
        </NavLink>

        <NavLink
          to="/mood"
          className={({ isActive }) =>
            `${linkClass} ${
              isActive ? "bg-gray-200" : "text-gray-600"
            }`
          }
        >
          Mood
        </NavLink>

        <NavLink
          to="/about"
          className={({ isActive }) =>
            `${linkClass} ${
              isActive ? "bg-gray-200" : "text-gray-600"
            }`
          }
        >
          About
        </NavLink>
      </div>
    </nav>
  );
}
