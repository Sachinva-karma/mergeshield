import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function CleanResult({ analysis }) {
  const fileCount = analysis?.diff_summary?.total_files || 0;
  const lineCount = analysis?.diff_summary?.total_lines || 0;

  return (
    <div className="clean-pass-card">
      <div className="clean-icon-circle">
        <ShieldCheck size={28} />
      </div>
      <h3 className="clean-pass-title">Clean Pass — No Potential Risks Detected</h3>
      <p className="clean-pass-desc">
        Analyzed {fileCount} file{fileCount === 1 ? '' : 's'} across {lineCount} lines of diff. No breaking public API changes, unhandled async promises, or syntax/logic regressions were discovered.
      </p>
      <div className="clean-pass-disclaimer">
        <strong>Transparency Note:</strong> A clean audit indicates no detectable risks within the retrieved changes. It does not certify that the repository or un-reviewed modules are completely free of bugs.
      </div>
    </div>
  );
}
