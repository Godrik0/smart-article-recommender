export function ResultItem({ item, index }) {
  const pct = Math.round(item.score * 100);

  return (
    <li className="result-item">
      <div className="result-head">
        <span className="result-idx">{index}.</span>
        <a href={item.url} target="_blank" rel="noopener noreferrer" className="result-title">
          {item.title}
        </a>
        <div className="result-meta">
          <span className="result-category">{item.category}</span>
          <span className="result-score">{pct}%</span>
        </div>
      </div>
      <p className="result-desc">{item.description}</p>
      <div className="result-tags">
        {item.tags.map((tag) => (
          <span key={tag} className="tag">{tag}</span>
        ))}
      </div>
    </li>
  );
}
