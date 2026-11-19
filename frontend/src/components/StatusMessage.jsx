export default function StatusMessage({ message, onRetry }) {
  return (
    <div className={`status${onRetry ? " error" : ""}`} role={onRetry ? "alert" : "status"}>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="secondary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
