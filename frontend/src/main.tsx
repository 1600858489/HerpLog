import React from "react";
import ReactDOM from "react-dom/client";
import "antd/dist/reset.css";
import "antd-mobile/es/global";
import { App } from "./app/App";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
