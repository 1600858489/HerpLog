import { useEffect, useState } from "react";
import "./App.css";

type ApiStatus = "checking" | "online" | "offline";

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((response) => {
        setApiStatus(response.ok ? "online" : "offline");
      })
      .catch(() => {
        setApiStatus("offline");
      });
  }, []);

  const statusText = {
    checking: "正在连接后端...",
    online: "后端已连接",
    offline: "后端未连接",
  }[apiStatus];

  return (
    <main className="app-shell">
      <section className="intro">
        <p className="eyebrow">HerpLog</p>
        <h1>鳞记</h1>
        <p className="summary">
          一个面向爬宠长期饲养的记录与提醒工具。当前是前后端基础运行骨架。
        </p>
        <div className={`status status-${apiStatus}`}>{statusText}</div>
      </section>
    </main>
  );
}

export default App;
