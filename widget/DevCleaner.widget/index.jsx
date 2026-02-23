/**
 * DevCleaner — Übersicht Desktop Widget
 * Muestra el estado de la última limpieza de dependencias.
 * Lee ~/Desktop/DevCleaner/history.json
 */

import { run } from "uebersicht";

export const refreshFrequency = 300000; // 5 minutos

export const className = `
  bottom: 20px;
  right: 20px;
  width: 320px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  color: #e8e8e8;
  z-index: 1;
`;

const HISTORY_PATH = `${process.env.HOME}/Desktop/DevCleaner/history.json`;

export const command = `cat '${HISTORY_PATH}' 2>/dev/null || echo '[]'`;

export const render = ({ output, error }) => {
  let lastRun = null;
  let totalFreed = 0;

  try {
    const history = JSON.parse(output || "[]");
    if (history.length > 0) {
      lastRun = history[0];
      totalFreed = history.reduce((sum, r) => sum + (r.total_freed_mb || 0), 0);
    }
  } catch {
    // ignore parse errors
  }

  const styles = {
    container: {
      background: "rgba(30, 30, 30, 0.85)",
      backdropFilter: "blur(20px)",
      WebkitBackdropFilter: "blur(20px)",
      borderRadius: "16px",
      padding: "16px 18px",
      border: "1px solid rgba(255,255,255,0.08)",
      boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
    },
    header: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: "12px",
    },
    title: {
      fontSize: "15px",
      fontWeight: 600,
      letterSpacing: "-0.2px",
    },
    badge: {
      fontSize: "10px",
      background: lastRun?.dry_run ? "rgba(100,100,200,0.3)" : "rgba(50,160,80,0.3)",
      color: lastRun?.dry_run ? "#aaaaff" : "#66dd88",
      padding: "2px 8px",
      borderRadius: "10px",
      fontWeight: 500,
    },
    row: {
      display: "flex",
      justifyContent: "space-between",
      fontSize: "12px",
      padding: "3px 0",
      color: "#b0b0b0",
    },
    value: {
      color: "#e0e0e0",
      fontWeight: 500,
      fontVariantNumeric: "tabular-nums",
    },
    divider: {
      borderTop: "1px solid rgba(255,255,255,0.06)",
      margin: "8px 0",
    },
    empty: {
      fontSize: "12px",
      color: "#888",
      textAlign: "center",
      padding: "8px 0",
    },
    item: {
      fontSize: "11px",
      color: "#999",
      padding: "2px 0",
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis",
    },
  };

  if (!lastRun) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.title}>🧹 DevCleaner</span>
        </div>
        <div style={styles.empty}>Sin datos aún. Ejecutá la app.</div>
      </div>
    );
  }

  const items = lastRun.results || [];
  const homePath = process.env.HOME || "";

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>🧹 DevCleaner</span>
        <span style={styles.badge}>{lastRun.dry_run ? "DRY RUN" : "LIMPIEZA"}</span>
      </div>

      <div style={styles.row}>
        <span>Última ejecución</span>
        <span style={styles.value}>{lastRun.timestamp}</span>
      </div>
      <div style={styles.row}>
        <span>Items procesados</span>
        <span style={styles.value}>{items.length}</span>
      </div>
      <div style={styles.row}>
        <span>Espacio liberado</span>
        <span style={{ ...styles.value, color: "#66dd88" }}>
          {lastRun.total_freed_mb.toFixed(1)} MB
        </span>
      </div>
      <div style={styles.row}>
        <span>Total histórico</span>
        <span style={{ ...styles.value, color: "#88bbff" }}>
          {totalFreed.toFixed(1)} MB
        </span>
      </div>

      {items.length > 0 && (
        <>
          <div style={styles.divider} />
          {items.slice(0, 5).map((item, i) => (
            <div key={i} style={styles.item}>
              {item.deleted ? "✅" : "👁"}{" "}
              {item.path.replace(homePath, "~")} ({item.size_mb}MB)
            </div>
          ))}
          {items.length > 5 && (
            <div style={{ ...styles.item, color: "#666" }}>
              ... y {items.length - 5} más
            </div>
          )}
        </>
      )}
    </div>
  );
};
