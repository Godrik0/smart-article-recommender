export function SearchPanel({ query, topK, onQueryChange, onTopKChange, onSubmit, submitting }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(query, topK);
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span>$</span> query
      </div>
      <form onSubmit={handleSubmit} className="panel-body">
        <textarea
          className="query-input"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          minLength={2}
          maxLength={1200}
          required
          placeholder="describe what you want to learn..."
          disabled={submitting}
          aria-label="Search query"
        />
        <div className="form-row">
          <div className="topk-group">
            <span className="topk-label">--top-k</span>
            <div className="topk-btns" role="radiogroup" aria-label="Top K results">
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <button
                  key={n}
                  type="button"
                  className={`topk-btn${topK === n ? ' active' : ''}`}
                  onClick={() => onTopKChange(n)}
                  disabled={submitting}
                  role="radio"
                  aria-checked={topK === n}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'running...' : 'run'}
          </button>
        </div>
      </form>
    </div>
  );
}
