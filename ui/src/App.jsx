import { Component, useCallback, useEffect, useState } from 'react';
import { recommend, fetchRecommendation, listRecommendations } from './api';
import { SearchPanel } from './components/SearchPanel';
import { ResultsPanel } from './components/ResultsPanel';
import { HistoryPanel } from './components/HistoryPanel';

const MAX_POLL_ERRORS = 3;
const POLL_INTERVAL = 2000;

class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="page">
          <div role="alert" className="error-boundary">
            <h1>fatal error</h1>
            <p>An unexpected error occurred. Try refreshing the page.</p>
            <button onClick={() => window.location.reload()}>refresh</button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}

function Separator() {
  return (
    <div className="separator" aria-hidden="true">
      ░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒░░░▒▒▒
    </div>
  );
}

function App() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [requests, setRequests] = useState([]);
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [activeRequestId, setActiveRequestId] = useState(null);
  const [activeResult, setActiveResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState(null);

  const loadRequests = useCallback(async () => {
    try {
      const data = await listRecommendations();
      setRequests(data.items);
    } catch {
      // non-critical
    } finally {
      setRequestsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  useEffect(() => {
    if (!activeRequestId) {
      setPolling(false);
      return undefined;
    }

    const activeReq = requests.find((r) => r.id === activeRequestId);
    if (activeReq && ['completed', 'failed'].includes(activeReq.status)) {
      setPolling(false);
      setActiveResult(activeReq);
      return undefined;
    }

    setPolling(true);
    let errorCount = 0;
    let timerId;

    const poll = async () => {
      try {
        const refreshed = await fetchRecommendation(activeRequestId);
        errorCount = 0;
        if (['completed', 'failed'].includes(refreshed.status)) {
          setPolling(false);
          setActiveResult(refreshed);
          setRequests((prev) => prev.map((r) => (r.id === refreshed.id ? refreshed : r)));
        } else {
          timerId = setTimeout(poll, POLL_INTERVAL);
        }
      } catch {
        errorCount += 1;
        if (errorCount >= MAX_POLL_ERRORS) {
          setPolling(false);
          setError('service temporarily unavailable');
        } else {
          timerId = setTimeout(poll, POLL_INTERVAL);
        }
      }
    };

    timerId = setTimeout(poll, POLL_INTERVAL);

    return () => {
      clearTimeout(timerId);
      setPolling(false);
    };
  }, [activeRequestId, requests]);

  const handleSubmit = useCallback(async (q, k) => {
    setSubmitting(true);
    setError(null);
    setActiveResult(null);

    try {
      const accepted = await recommend({ query: q, top_k: k });
      setActiveRequestId(accepted.request_id);
      await loadRequests();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }, [loadRequests]);

  const handleSelectRequest = useCallback((req) => {
    setActiveRequestId(req.id);
    setActiveResult(req);
  }, []);

  return (
    <main className="page">
      <header className="header">
        <h1>
          smart-article-recommender <span className="muted">v0.1.0</span>
        </h1>
        <p className="subtitle">semantic search over arxiv papers. powered by sentence-transformers.</p>
      </header>

      <Separator />

      <div className="layout">
        <div className="main-col">
          <SearchPanel
            query={query}
            topK={topK}
            onQueryChange={setQuery}
            onTopKChange={setTopK}
            onSubmit={handleSubmit}
            submitting={submitting}
          />
          <div style={{ marginTop: 16 }}>
            <ResultsPanel
              result={activeResult}
              polling={polling}
              submitting={submitting}
              error={error}
              onDismissError={() => setError(null)}
            />
          </div>
        </div>
        <div className="side-col">
          <HistoryPanel
            requests={requests}
            loading={requestsLoading}
            onSelect={handleSelectRequest}
          />
        </div>
      </div>

      <footer className="footer">
        <a href="https://github.com/Godrik0" target="_blank" rel="noopener noreferrer">GITHUB</a>
      </footer>
    </main>
  );
}

export default function AppWithBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}
