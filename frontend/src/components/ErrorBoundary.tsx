import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6">
          <div className="max-w-2xl w-full bg-slate-800 rounded-lg border border-slate-700 p-8">
            <div className="flex items-center gap-3 mb-6">
              <AlertTriangle className="text-red-500" size={32} />
              <h1 className="text-2xl font-bold text-white">Something went wrong</h1>
            </div>

            <div className="mb-6">
              <p className="text-slate-300 mb-4">
                An unexpected error occurred in the application. This has been logged and
                will be investigated.
              </p>

              {this.state.error && (
                <div className="bg-slate-900 rounded p-4 mb-4">
                  <div className="text-sm font-mono text-red-400 mb-2">
                    {this.state.error.toString()}
                  </div>
                  {this.state.errorInfo && (
                    <details className="text-xs text-slate-400">
                      <summary className="cursor-pointer hover:text-slate-300">
                        Show stack trace
                      </summary>
                      <pre className="mt-2 overflow-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition-colors"
              >
                <RefreshCw size={18} />
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded font-medium transition-colors"
              >
                Reload Page
              </button>
            </div>

            <div className="mt-6 text-sm text-slate-400">
              If this problem persists, please check the browser console for more details or
              contact support.
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
