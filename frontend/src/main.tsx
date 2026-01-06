import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { supabase } from "./lib/supabase";

supabase.auth.getSession().then(({ data }) => {
  if (data.session) {
    // Clean the URL after consuming token
    window.history.replaceState(
      {},
      document.title,
      "/HappyApp/#/"
    );
  }
});

ReactDOM.createRoot(
  document.getElementById("root")!
).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>
);
