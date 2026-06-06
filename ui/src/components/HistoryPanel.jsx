import { Skeleton } from './Skeleton';

export function HistoryPanel({ requests, loading, onSelect }) {
  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span>#</span> history
        </div>
        <Skeleton />
      </div>
    );
  }

  if (!requests || requests.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span>#</span> history
        </div>
        <div className="history-empty">-- no history --</div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <span>#</span> history
      </div>
      <ul className="history-list history-scroll" role="list">
        {requests.map((req) => (
          <li key={req.id}>
            <button
              className="history-item"
              onClick={() => onSelect(req)}
              type="button"
              aria-label={`Request: ${req.query}, status: ${req.status}`}
            >
              <span className={`status-dot ${req.status}`} aria-hidden="true" />
              <span className="history-query">
                {req.query.length > 40 ? req.query.slice(0, 40) + '...' : req.query}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
