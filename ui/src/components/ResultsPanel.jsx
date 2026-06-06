import { Spinner } from './Spinner';
import { ErrorMessage } from './ErrorMessage';
import { ResultItem } from './ResultItem';

export function ResultsPanel({ result, polling, submitting, error, onDismissError }) {
  let content;

  if (error) {
    content = <ErrorMessage onDismiss={onDismissError}>ERR: {error}</ErrorMessage>;
  } else if (submitting || polling) {
    content = <Spinner />;
  } else if (result && result.status === 'failed') {
    content = <ErrorMessage onDismiss={onDismissError}>ERR: {result.error}</ErrorMessage>;
  } else if (result && result.status === 'completed' && result.result) {
    content = (
      <ul className="result-list" role="list">
        {result.result.items.map((item, i) => (
          <ResultItem key={item.id} item={item} index={i + 1} />
        ))}
      </ul>
    );
  } else {
    content = <div className="hint">no results yet. run a query to search.</div>;
  }

  return (
    <div className="panel" aria-live="polite">
      <div className="panel-header">
        <span>&gt;</span> results
      </div>
      {content}
    </div>
  );
}
