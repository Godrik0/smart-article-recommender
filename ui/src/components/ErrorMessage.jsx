export function ErrorMessage({ children, onDismiss }) {
  return (
    <div role="alert" className="error-msg">
      <span>{children}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="error-dismiss" type="button">
          dismiss
        </button>
      )}
    </div>
  );
}
